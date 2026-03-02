from datetime import datetime, timedelta
import json

from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import delete

from .models import Task, TaskLog


def _parse_times(times_json: str):
    """
    将存储在 Task.times 中的 JSON 字符串解析为时间点列表，支持到秒。

    存储格式示例：["07:30:00", "12:30:15"] 或历史数据 ["07:30", "12:30"]。
    返回标准化后的字符串列表，统一为 "HH:MM:SS"。
    """
    try:
        data = json.loads(times_json)
        if isinstance(data, list):
            result = []
            for t in data:
                if not isinstance(t, str):
                    continue
                # 兼容旧格式 HH:MM，自动补齐为 HH:MM:00
                if len(t) == 5:
                    t = t + ":00"
                # 简单校验
                parts = t.split(":")
                if len(parts) != 3:
                    continue
                try:
                    h, m, s = map(int, parts)
                    if 0 <= h < 24 and 0 <= m < 60 and 0 <= s < 60:
                        result.append(f"{h:02d}:{m:02d}:{s:02d}")
                except ValueError:
                    continue
            return result
    except Exception:
        return []
    return []


def _job_id_for(task_id: int, time_str: str) -> str:
    return f"task_{task_id}_{time_str.replace(':', '')}"


def register_task_jobs(app, task: Task):
    """
    为单个 Task 注册所有时间点的 APScheduler 任务。
    """
    scheduler = app.config["SCHEDULER"]
    times = _parse_times(task.times)
    for t in times:
        hour, minute, second = t.split(":")
        job_id = _job_id_for(task.id, t)
        # 先移除可能已存在的 job
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass

        # 组装可选的生效时间范围
        start_date = task.date_start
        end_date = task.date_end

        trigger = CronTrigger(
            hour=int(hour),
            minute=int(minute),
            second=int(second),
            start_date=start_date,
            end_date=end_date,
            timezone="Asia/Shanghai",
        )
        scheduler.add_job(
            func=run_task_job,
            trigger=trigger,
            id=job_id,
            args=[task.id],
            replace_existing=True,
        )


def unregister_task_jobs(app, task_id: int):
    """
    移除某个 Task 的所有调度任务。
    这里简单处理：根据当前已知时间组合尝试移除，或在任务更新时重建即可。
    """
    scheduler = app.config["SCHEDULER"]
    # APScheduler 本身没有按前缀批量获取 job 的标准接口，实际实现中可维护映射。
    for job in scheduler.get_jobs():
        if job.id.startswith(f"task_{task_id}_"):
            scheduler.remove_job(job.id)


def register_existing_tasks(app):
    """
    在应用启动时，从数据库加载所有 enabled=1 的任务并注册到 APScheduler。
    同时顺带执行一次「清理 7 天前日志」的任务。
    """
    SessionLocal = app.config["DB_SESSION_FACTORY"]
    with SessionLocal() as db:
        tasks = db.query(Task).filter(Task.enabled.is_(True)).all()
        for task in tasks:
            register_task_jobs(app, task)

        # 启动时进行一次历史日志清理
        cleanup_old_logs(db)


def cleanup_old_logs(db):
    """
    删除 7 天前的日志记录。
    """
    threshold = datetime.utcnow() - timedelta(days=7)
    stmt = delete(TaskLog).where(TaskLog.run_at < threshold)
    db.execute(stmt)
    db.commit()


def run_task_job(task_id: int):
    """
    真正执行签到任务的函数。
    """
    # 为了避免循环依赖，这里在函数内部导入 create_app 使用的会话工厂
    from .db import get_engine, get_session_factory
    from utils.attendance import Task as AttendanceTask
    from utils.notification import sendQQmessage, wx_send

    engine = get_engine()
    SessionLocal = get_session_factory(engine)

    now = datetime.utcnow()

    with SessionLocal() as db:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return

        # 组装与原有 CLI 脚本兼容的 student 配置，复用旧的签到逻辑
        student = {
            "name": task.name,
            "class": task.class_id,
            "lat": task.lat,
            "lng": task.lng,
            "acc": task.acc or "30",
            "cookie": task.cookie,
            # 兼容旧字段命名
            "QmsgKEY": task.qq_key or "",
            "WXKey": task.wx_key or "",
        }

        # 调用旧的签到实现
        user_name, result_status = AttendanceTask(student)

        # 根据结果映射为可读中文说明
        status_map = {
            "success": "签到成功",
            "already_signed": "已签到，无需重复",
            "not_started": "未开始签到，请稍后",
            "no_sign_in": "当前无可用签到",
            "skip": "跳过（信息不完整或 cookie 失效）",
            "error": "执行出错",
        }
        status_desc = status_map.get(result_status, f"未知状态: {result_status}")

        # 发送通知：成功/已签到发“签到成功”，其他情况发“签到失败 + 原因”
        is_success = result_status in ("success", "already_signed")
        notify_msg = "签到成功！" if is_success else f"签到失败，原因：{status_desc}"

        try:
            if task.wx_key:
                wx_send(task.wx_key, notify_msg)
        except Exception:
            # 通知失败不影响主流程
            pass
        try:
            if task.qq_key:
                sendQQmessage(task.qq_key, notify_msg)
        except Exception:
            pass

        # 生成结构化日志文本，兼顾可读性与调试信息
        log_text_lines = [
            f"=================={now.strftime('%H:%M:%S')}===================",
            "=========== 用户和班级信息 ===============",
            f"任务 ID: {task.id}",
            f"用户姓名: {user_name or task.name}",
            f"班级标识: {task.class_id}",
            "=========== 签到结果 ===============",
            f"原始状态码: {result_status}",
            (
                f"签到结果: 签到成功（{status_desc}）"
                if is_success
                else f"签到结果: 签到失败，原因：{status_desc}"
            ),
            "=========== 位置信息 ===============",
            f"纬度(lat): {task.lat}",
            f"经度(lng): {task.lng}",
            f"精度(acc): {task.acc}",
            "===============================================",
        ]
        log_text = "\n".join(log_text_lines)

        # 映射到日志中的状态字段：success / error / skipped
        if result_status in ("success", "already_signed"):
            log_status = "success"
        elif result_status in ("not_started", "no_sign_in", "skip"):
            log_status = "skipped"
        else:
            log_status = "error"

        log = TaskLog(
            task_id=task.id,
            run_at=now,
            status=log_status,
            message=log_text,
        )
        db.add(log)

        # 先提交本次日志，再顺带清理一次 7 天前的旧日志
        db.commit()
        cleanup_old_logs(db)

