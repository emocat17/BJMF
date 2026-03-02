from flask import Flask, jsonify, request, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import secrets
import time
import hashlib
from datetime import datetime, timedelta

from .db import init_db
from .scheduler import register_existing_tasks, register_task_jobs, unregister_task_jobs
from .models import Task, TaskLog, Setting
from .qr_login import QRLoginService
import json
import os
import re


qr_service = QRLoginService()


def _parse_coord_string(coord: str):
    """
    将前端传入的一整段经纬度字符串解析为 (lat, lng)。
    支持空格、逗号、竖线、中文逗号等多种分隔符。
    """
    if not coord:
        return None, None
    # 统一替换常见分隔符为空格
    normalized = re.sub(r"[,\|，、]+", " ", coord)
    parts = [p for p in normalized.strip().split() if p]
    if len(parts) < 2:
        return None, None
    return parts[0], parts[1]


def create_app():
    app = Flask(__name__)

    # 初始化数据库
    engine, SessionLocal = init_db()
    app.config["DB_ENGINE"] = engine
    app.config["DB_SESSION_FACTORY"] = SessionLocal

    # 初始化 APScheduler（后台调度器）
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    scheduler.start()
    app.config["SCHEDULER"] = scheduler

    # 简单的内存态管理员 token 管理（仅单进程场景）
    app.config["ADMIN_TOKENS"] = {}  # {token: expire_at_utc}

    # 启动时加载已启用任务到调度器
    register_existing_tasks(app)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    # 前端单页（用户配置页面）
    @app.get("/")
    def index_page():
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
        return send_from_directory(static_dir, "index.html")

    # 后台管理页面（仅提供静态 HTML，实际权限控制在 /api/admin/* 接口中完成）
    @app.get("/manage")
    def manage_page():
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
        return send_from_directory(static_dir, "manage.html")

    # ========== 阶段三：扫码登录接口 ==========

    @app.get("/api/qr")
    def api_create_qr():
        """
        创建扫码登录会话，返回二维码 base64 和 token。
        """
        token = secrets.token_urlsafe(16)
        result = qr_service.create_qr_session(token)
        if not result or result.get("error"):
            return jsonify({"error": result.get("error", "创建二维码失败")}), 500
        return jsonify(result)

    @app.get("/api/qr/status")
    def api_qr_status():
        """
        轮询扫码状态。
        返回：
        - pending: 尚未扫码/确认
        - success: 登录成功，返回用户与班级信息
        - expired: 二维码过期
        - error: 出错
        """
        token = request.args.get("token")
        if not token:
            return jsonify({"error": "missing token"}), 400

        state = qr_service.get_session_state(token)
        if not state:
            return jsonify({"status": "expired"})

        if state.error:
            return jsonify({"status": "error", "error": state.error})
        if state.expired:
            return jsonify({"status": "expired"})
        if state.cookie and state.user_name:
            return jsonify(
                {
                    "status": "success",
                    "user": {
                        "name": state.user_name,
                        "class_id": state.class_id,
                        "class_name": state.class_name,
                        "class_code": state.class_code,
                    },
                }
            )

        return jsonify({"status": "pending"})

    # ========== 阶段三：任务管理接口（用户侧） ==========

    @app.post("/api/tasks")
    def api_create_task():
        """
        基于已经完成扫码登录的会话创建签到任务。
        Body JSON:
        - token: 扫码登录 token
        - coord: 一整段经纬度字符串（可包含空格、逗号、竖线等任意分隔符）
        - wx_key, qq_key
        - times: ["07:30:00","12:30:15"]  （支持到秒，若仅到分钟将自动补齐为 :00）
        - date_start: "2026-03-01"（可选，任务开始生效日期）
        - date_end: "2026-03-31"（可选，任务结束日期，留空则表示长期）
        """
        data = request.get_json(silent=True) or {}
        token = data.get("token")
        if not token:
            return jsonify({"error": "missing token"}), 400

        state = qr_service.get_session_state(token)
        if not state or not state.cookie or not state.user_name:
            return jsonify({"error": "invalid or expired token"}), 400

        # 兼容老版本：优先从 coord 解析，经纬度单独字段作为降级方案
        coord = (data.get("coord") or "").strip()
        lat = None
        lng = None
        if coord:
            lat, lng = _parse_coord_string(coord)
        # 如果 coord 解析失败，则尝试直接使用 lat / lng 字段
        if not lat or not lng:
            lat = data.get("lat")
            lng = data.get("lng")

        # 精度/海拔前端不再传，后端统一固定为 30
        acc = "30"
        times = data.get("times") or []
        wx_key = data.get("wx_key") or ""
        qq_key = data.get("qq_key") or ""

        # 可选日期范围：前端传 YYYY-MM-DD 字符串，后端解析为本地日期（Asia/Shanghai）
        raw_date_start = (data.get("date_start") or "").strip() or None
        raw_date_end = (data.get("date_end") or "").strip() or None
        date_start = None
        date_end = None
        try:
            if raw_date_start:
                # 视为本地日期 00:00:00
                date_start = datetime.strptime(raw_date_start, "%Y-%m-%d")
            if raw_date_end:
                # 视为本地日期 23:59:59，便于包含整天
                date_end = datetime.strptime(raw_date_end, "%Y-%m-%d") + timedelta(
                    hours=23, minutes=59, seconds=59
                )
        except ValueError:
            return jsonify({"error": "日期格式错误，应为 YYYY-MM-DD"}), 400

        if not lat or not lng or not isinstance(times, list) or not times:
            return jsonify({"error": "经纬度(coord/lat,lng) 与 times 为必填"}), 400

        SessionLocal = app.config["DB_SESSION_FACTORY"]
        with SessionLocal() as db:
            task = Task(
                name=state.user_name,
                class_id=state.class_id or "",
                cookie=state.cookie,
                lat=str(lat),
                lng=str(lng),
                acc=str(acc),
                wx_key=wx_key,
                qq_key=qq_key,
                times=json.dumps(times, ensure_ascii=False),
                enabled=True,
                date_start=date_start,
                date_end=date_end,
            )
            db.add(task)
            db.commit()
            db.refresh(task)

            # 为新任务注册调度 job
            register_task_jobs(app, task)

            return (
                jsonify(
                    {
                        "id": task.id,
                        "name": task.name,
                        "class_id": task.class_id,
                        "lat": task.lat,
                        "lng": task.lng,
                        "acc": task.acc,
                        "wx_key": task.wx_key,
                        "qq_key": task.qq_key,
                        "times": times,
                        "enabled": task.enabled,
                        "date_start": task.date_start.isoformat() if task.date_start else None,
                        "date_end": task.date_end.isoformat() if task.date_end else None,
                    }
                ),
                201,
            )

    @app.get("/api/tasks/<int:task_id>")
    def api_get_task(task_id: int):
        """
        返回任务详情（不包含 cookie）。
        """
        SessionLocal = app.config["DB_SESSION_FACTORY"]
        with SessionLocal() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return jsonify({"error": "not found"}), 404

            return jsonify(
                {
                    "id": task.id,
                    "name": task.name,
                    "class_id": task.class_id,
                    "lat": task.lat,
                    "lng": task.lng,
                    "acc": task.acc,
                    "wx_key": task.wx_key,
                    "qq_key": task.qq_key,
                    "times": json.loads(task.times or "[]"),
                    "enabled": task.enabled,
                    "date_start": task.date_start.isoformat() if task.date_start else None,
                    "date_end": task.date_end.isoformat() if task.date_end else None,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                }
            )

    @app.get("/api/tasks/<int:task_id>/logs")
    def api_get_task_logs(task_id: int):
        """
        查询指定任务的最近执行日志（按任务 ID）。

        Query 参数：
        - limit: 返回条数，默认 20，最大 100
        """
        try:
            limit = int(request.args.get("limit", "20"))
        except ValueError:
            limit = 20
        if limit <= 0:
            limit = 20
        if limit > 100:
            limit = 100

        SessionLocal = app.config["DB_SESSION_FACTORY"]
        with SessionLocal() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return jsonify({"error": "not found"}), 404

            logs = (
                db.query(TaskLog)
                .filter(TaskLog.task_id == task_id)
                .order_by(TaskLog.run_at.desc())
                .limit(limit)
                .all()
            )

    # ========== 阶段三扩展：基于扫码会话的用户配置与日志 ==========

            return jsonify(
                [
                    {
                        "id": log.id,
                        "run_at": log.run_at.isoformat() if log.run_at else None,
                        "status": log.status,
                        "message": log.message,
                    }
                    for log in logs
                ]
            )

    @app.get("/api/user/config")
    def api_get_user_config():
        """
        基于当前扫码会话（token 映射到 cookie）返回该账号最近一次任务配置，
        并判断本次扫码获取的 cookie 与数据库中记录的是否一致。

        Query 参数：
        - token: 扫码登录 token（必填）
        """
        token = request.args.get("token")
        if not token:
            return jsonify({"error": "missing token"}), 400

        state = qr_service.get_session_state(token)
        if not state or not state.cookie:
            return jsonify({"error": "invalid or expired token"}), 400

        SessionLocal = app.config["DB_SESSION_FACTORY"]
        with SessionLocal() as db:
            # 找出该账号（按 cookie）最近一次的任务配置；
            # 这里按 created_at 倒序取第一个。
            task = (
                db.query(Task)
                .filter(Task.cookie == state.cookie)
                .order_by(Task.created_at.desc())
                .first()
            )

            if not task:
                return jsonify(
                    {
                        "has_task": False,
                        "cookie_changed": False,
                        "config": None,
                    }
                )

            # 这里的 cookie_changed 主要用于「提示已更新」场景；
            # 当前实现里 Task.cookie 就是最近一次使用的 cookie，
            # 若你未来引入多次扫码并保留历史 cookie，可在此对比。
            cookie_changed = task.cookie != state.cookie

            return jsonify(
                {
                    "has_task": True,
                    "cookie_changed": cookie_changed,
                    "config": {
                        "id": task.id,
                        "name": task.name,
                        "class_id": task.class_id,
                        "lat": task.lat,
                        "lng": task.lng,
                        "acc": task.acc,
                        "wx_key": task.wx_key,
                        "qq_key": task.qq_key,
                        "times": json.loads(task.times or "[]"),
                        "enabled": task.enabled,
                        "date_start": task.date_start.isoformat() if task.date_start else None,
                        "date_end": task.date_end.isoformat() if task.date_end else None,
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                    },
                }
            )

    @app.get("/api/user/logs")
    def api_get_user_logs():
        """
        基于当前扫码会话（token 映射到 cookie）查询该账号下所有任务的执行日志。

        Query 参数：
        - token: 扫码登录 token（必填）
        - limit: 返回条数，默认 20，最大 100
        """
        token = request.args.get("token")
        if not token:
            return jsonify({"error": "missing token"}), 400

        state = qr_service.get_session_state(token)
        if not state or not state.cookie:
            return jsonify({"error": "invalid or expired token"}), 400

        try:
            limit = int(request.args.get("limit", "20"))
        except ValueError:
            limit = 20
        if limit <= 0:
            limit = 20
        if limit > 100:
            limit = 100

        SessionLocal = app.config["DB_SESSION_FACTORY"]
        with SessionLocal() as db:
            # 找出该 cookie 对应的所有任务
            tasks = db.query(Task).filter(Task.cookie == state.cookie).all()
            if not tasks:
                return jsonify([])

            task_ids = [t.id for t in tasks]
            logs = (
                db.query(TaskLog, Task)
                .join(Task, TaskLog.task_id == Task.id)
                .filter(TaskLog.task_id.in_(task_ids))
                .order_by(TaskLog.run_at.desc())
                .limit(limit)
                .all()
            )

            return jsonify(
                [
                    {
                        "id": log.id,
                        "run_at": log.run_at.isoformat() if log.run_at else None,
                        "status": log.status,
                        "message": log.message,
                        "task": {
                            "id": task.id,
                            "name": task.name,
                            "class_id": task.class_id,
                            "lat": task.lat,
                            "lng": task.lng,
                        },
                    }
                    for log, task in logs
                ]
            )

    # ========== 阶段五：管理员后台与运维接口（后端部分） ==========

    def _hash_admin_key(key: str) -> str:
        """
        对管理员 Key 做简单哈希存储，避免明文落库。
        """
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _get_admin_key_hash(db):
        setting = db.query(Setting).filter(Setting.key == "admin_key_hash").first()
        return setting.value if setting else None

    def _require_admin(app):
        """
        管理员认证校验。

        当前部署需求：后台无需密码即可查看与管理所有任务，
        因此此函数直接放行，不再强制要求 admin token。

        如需重新开启鉴权，可恢复为从请求头 `X-Admin-Token` /
        查询参数 `admin_token` 中读取 token 并校验有效期。
        """
        return "public", None

    @app.post("/api/admin/init")
    def api_admin_init():
        """
        初始化管理员 Key：
        - 仅当数据库中不存在 admin_key_hash 时允许调用；
        - Body: { "key": "你的管理员密码" }。
        """
        SessionLocal = app.config["DB_SESSION_FACTORY"]
        data = request.get_json(silent=True) or {}
        key = (data.get("key") or "").strip()
        if not key:
            return jsonify({"error": "missing key"}), 400

        with SessionLocal() as db:
            existing_hash = _get_admin_key_hash(db)
            if existing_hash:
                return jsonify({"error": "admin key already initialized"}), 409

            setting = Setting(
                key="admin_key_hash",
                value=_hash_admin_key(key),
            )
            db.add(setting)
            db.commit()

        return jsonify({"status": "ok"})

    @app.post("/api/admin/login")
    def api_admin_login():
        """
        管理员登录：提交管理员 Key，返回一个短期 admin token。

        Body:
        - key: 管理员密码

        响应:
        - token: 管理员访问 token
        - expires_in: 过期时间（秒），默认 24 小时
        """
        SessionLocal = app.config["DB_SESSION_FACTORY"]
        data = request.get_json(silent=True) or {}
        key = (data.get("key") or "").strip()
        if not key:
            return jsonify({"error": "missing key"}), 400

        with SessionLocal() as db:
            key_hash = _get_admin_key_hash(db)
            if not key_hash:
                return jsonify({"error": "admin key not initialized"}), 400

            if _hash_admin_key(key) != key_hash:
                return jsonify({"error": "invalid admin key"}), 401

        # 生成 admin token，默认有效期 24 小时
        token = secrets.token_urlsafe(24)
        expires_in = 24 * 3600
        expire_at = datetime.utcnow() + timedelta(seconds=expires_in)
        app.config["ADMIN_TOKENS"][token] = expire_at

        return jsonify({"token": token, "expires_in": expires_in})

    @app.get("/api/admin/tasks")
    def api_admin_list_tasks():
        """
        管理员查看任务列表。

        认证：需要有效的 admin token（X-Admin-Token）。

        Query 参数（可选）：
        - name: 按姓名模糊搜索
        - class_id: 按班级标识模糊搜索
        - enabled: 1 / 0 过滤启用状态
        """
        _, error_resp = _require_admin(app)
        if error_resp:
            return error_resp

        name = (request.args.get("name") or "").strip()
        class_id = (request.args.get("class_id") or "").strip()
        enabled = request.args.get("enabled")

        SessionLocal = app.config["DB_SESSION_FACTORY"]
        with SessionLocal() as db:
            query = db.query(Task)
            if name:
                query = query.filter(Task.name.contains(name))
            if class_id:
                query = query.filter(Task.class_id.contains(class_id))
            if enabled in ("0", "1"):
                flag = enabled == "1"
                query = query.filter(Task.enabled.is_(flag))

            tasks = query.order_by(Task.id.desc()).all()

            return jsonify(
                [
                    {
                        "id": t.id,
                        "name": t.name,
                        "class_id": t.class_id,
                        "lat": t.lat,
                        "lng": t.lng,
                        "acc": t.acc,
                        "wx_key": t.wx_key,
                        "qq_key": t.qq_key,
                        "times": json.loads(t.times or "[]"),
                        "enabled": t.enabled,
                        "date_start": t.date_start.isoformat() if t.date_start else None,
                        "date_end": t.date_end.isoformat() if t.date_end else None,
                        "created_at": t.created_at.isoformat() if t.created_at else None,
                        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                    }
                    for t in tasks
                ]
            )

    @app.patch("/api/admin/tasks/<int:task_id>")
    def api_admin_update_task(task_id: int):
        """
        管理员修改任务配置（位置、时间、通知 Key、启用状态等）。

        Body JSON：可选字段，按需更新
        - lat, lng, acc
        - wx_key, qq_key
        - times: ["07:30:00","12:30:15"]
        - enabled: bool
        - date_start: "2026-03-01"（可选，任务开始日期）
        - date_end: "2026-03-31"（可选，任务结束日期）
        """
        _, error_resp = _require_admin(app)
        if error_resp:
            return error_resp

        data = request.get_json(silent=True) or {}

        SessionLocal = app.config["DB_SESSION_FACTORY"]
        with SessionLocal() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return jsonify({"error": "not found"}), 404

            # 记录更新前后 enabled / times 是否有变化，用于刷新调度
            old_enabled = bool(task.enabled)
            old_times = json.loads(task.times or "[]")

            if "lat" in data:
                task.lat = str(data.get("lat") or task.lat)
            if "lng" in data:
                task.lng = str(data.get("lng") or task.lng)
            if "acc" in data:
                task.acc = str(data.get("acc") or task.acc)
            if "wx_key" in data:
                task.wx_key = data.get("wx_key") or ""
            if "qq_key" in data:
                task.qq_key = data.get("qq_key") or ""
            if "times" in data:
                times = data.get("times") or []
                if not isinstance(times, list):
                    return jsonify({"error": "times must be a list"}), 400
                task.times = json.dumps(times, ensure_ascii=False)
            if "enabled" in data:
                task.enabled = bool(data.get("enabled"))
            # 日期范围更新：允许传入 YYYY-MM-DD 字符串或 null/空字符串
            raw_date_start = data.get("date_start", "__missing__")
            raw_date_end = data.get("date_end", "__missing__")
            try:
                if raw_date_start != "__missing__":
                    if raw_date_start:
                        task.date_start = datetime.strptime(raw_date_start, "%Y-%m-%d")
                    else:
                        task.date_start = None
                if raw_date_end != "__missing__":
                    if raw_date_end:
                        task.date_end = datetime.strptime(raw_date_end, "%Y-%m-%d") + timedelta(
                            hours=23, minutes=59, seconds=59
                        )
                    else:
                        task.date_end = None
            except ValueError:
                return jsonify({"error": "日期格式错误，应为 YYYY-MM-DD"}), 400

            db.commit()
            db.refresh(task)

            # 根据 enabled/times 的变化动态更新 APScheduler job
            new_enabled = bool(task.enabled)
            new_times = json.loads(task.times or "[]")

            if not new_enabled:
                # 禁用任务：移除所有 job
                unregister_task_jobs(app, task.id)
            else:
                # 启用或时间列表发生变化：重建 job
                if (not old_enabled and new_enabled) or old_times != new_times:
                    register_task_jobs(app, task)

            return jsonify(
                {
                    "id": task.id,
                    "name": task.name,
                    "class_id": task.class_id,
                    "lat": task.lat,
                    "lng": task.lng,
                    "acc": task.acc,
                    "wx_key": task.wx_key,
                    "qq_key": task.qq_key,
                    "times": new_times,
                    "enabled": task.enabled,
                    "date_start": task.date_start.isoformat() if task.date_start else None,
                    "date_end": task.date_end.isoformat() if task.date_end else None,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                }
            )

    @app.get("/api/admin/logs")
    def api_admin_logs():
        """
        管理员查看执行日志。

        认证：需要 admin token。

        Query 参数：
        - task_id: 可选，若提供则仅查看该任务日志
        - limit: 返回条数，默认 50，最大 200
        """
        _, error_resp = _require_admin(app)
        if error_resp:
            return error_resp

        try:
            limit = int(request.args.get("limit", "50"))
        except ValueError:
            limit = 50
        if limit <= 0:
            limit = 50
        if limit > 200:
            limit = 200

        task_id = request.args.get("task_id")

        SessionLocal = app.config["DB_SESSION_FACTORY"]
        with SessionLocal() as db:
            query = db.query(TaskLog, Task).join(Task, TaskLog.task_id == Task.id)
            if task_id:
                try:
                    task_id_int = int(task_id)
                    query = query.filter(TaskLog.task_id == task_id_int)
                except ValueError:
                    return jsonify({"error": "task_id must be integer"}), 400

            logs = query.order_by(TaskLog.run_at.desc()).limit(limit).all()

            return jsonify(
                [
                    {
                        "id": log.id,
                        "run_at": log.run_at.isoformat() if log.run_at else None,
                        "status": log.status,
                        "message": log.message,
                        "task": {
                            "id": task.id,
                            "name": task.name,
                            "class_id": task.class_id,
                            "lat": task.lat,
                            "lng": task.lng,
                        },
                    }
                    for log, task in logs
                ]
            )

    @app.delete("/api/admin/tasks/<int:task_id>")
    def api_admin_delete_task(task_id: int):
        """
        管理员删除任务。

        - 认证：需要 admin token。
        - 同时会移除 APScheduler 中对应的调度任务；
        - 由于 Task.logs 关系设置了 cascade="all, delete-orphan"，
          删除任务会自动级联删除该任务的所有日志。
        """
        _, error_resp = _require_admin(app)
        if error_resp:
            return error_resp

        SessionLocal = app.config["DB_SESSION_FACTORY"]
        with SessionLocal() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return jsonify({"error": "not found"}), 404

            # 先移除调度任务，再删数据库记录
            unregister_task_jobs(app, task.id)
            db.delete(task)
            db.commit()

        return jsonify({"status": "ok"})

    return app
