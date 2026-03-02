import base64
import io
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import qrcode
import requests
from bs4 import BeautifulSoup


@dataclass
class QRSessionState:
    """
    内存中的扫码会话状态，用于 Web 轮询。
    """

    token: str
    created_at: float
    is_scanned: bool = False
    is_confirmed: bool = False
    expired: bool = False
    # 登录成功后填充
    cookie: Optional[str] = None
    user_name: Optional[str] = None
    class_id: Optional[str] = None
    class_name: Optional[str] = None
    class_code: Optional[str] = None
    # 错误信息
    error: Optional[str] = None


class QRLoginService:
    """
    将 auto_add_user.py 中的 QRCodeLogin + StudentSession 适配为 Web 场景使用。
    注意：这里不再在本地生成图片文件，而是返回 base64 数据给前端展示。
    """

    def __init__(self, base_url: str = "https://bjmf.k8n.cn/weixin/qrlogin/student"):
        self.base_url = base_url
        self._sessions: Dict[str, QRSessionState] = {}
        self._lock = threading.Lock()
        # 会话过期时间（秒）
        self.session_ttl = 120

    def _new_requests_session(self) -> requests.Session:
        sess = requests.Session()
        sess.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36 "
                "MicroMessenger/7.0.10.1580(0x27000A50) Process/tools NetType/WIFI Language/zh_CN ABI/arm64",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "https://wx.qq.com/",
                "sec-ch-ua-platform": "Android",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        return sess

    def _extract_qr_url(self, html: str) -> str:
        """
        尽量兼容页面结构变化的二维码地址提取逻辑。
        优先使用原逻辑：div#qrcode 下的 img[src]；
        若找不到，则退化为在整页中寻找带 ticket= 的 img[src]。
        """
        soup = BeautifulSoup(html, "html.parser")

        # 1. 原脚本同款逻辑：div#qrcode 里的 img
        qrcode_div = soup.find("div", id="qrcode")
        if qrcode_div:
            img_tag = qrcode_div.find("img")
            if img_tag and img_tag.get("src"):
                return img_tag["src"]

        # 2. 兼容：有些页面可能直接在其他容器里放一个带 ticket 参数的二维码 img
        for img in soup.find_all("img"):
            src = img.get("src") or ""
            if "ticket=" in src:
                return src

        # 3. 找不到时，把 HTML 落地一份，方便后续排查
        try:
            import os

            debug_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "debug_qr.html"
            )
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception:
            # 调试文件写入失败不影响主流程，继续抛出错误
            pass

        raise ValueError("未找到二维码 img 标签，请查看 debug_qr.html 分析页面结构")

    def _qr_image_base64(self, url: str, sess: requests.Session) -> str:
        """
        这里有两种选择：
        1. 直接返回后端从目标站下载的二维码图片（更贴近原脚本）。
        2. 使用 qrcode 库重新生成二维码（若目标仅需扫码 URL）。

        为了兼容原逻辑，这里选择 1：下载图片然后转成 base64 返回。
        """
        resp = sess.get(url)
        resp.raise_for_status()
        img_bytes = resp.content
        return "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")

    def create_qr_session(self, token: str) -> Optional[Dict]:
        """
        创建一轮扫码登录会话，返回二维码 base64 和一些元信息。
        """
        sess = self._new_requests_session()
        try:
            html = sess.get(self.base_url).text
            qr_url = self._extract_qr_url(html)
            qr_b64 = self._qr_image_base64(qr_url, sess)
        except Exception as e:
            return {"error": f"获取二维码失败: {e}"}

        state = QRSessionState(token=token, created_at=time.time())
        with self._lock:
            self._sessions[token] = state

        # 启动一个后台线程轮询扫码状态
        thread = threading.Thread(target=self._poll_login_status, args=(token, sess), daemon=True)
        thread.start()

        return {
            "token": token,
            "qrcode": qr_b64,
            "expires_in": self.session_ttl,
        }

    def _poll_login_status(self, token: str, sess: requests.Session, max_attempts: int = 60):
        """
        轮询二维码扫码/确认状态，成功后获取 cookie 与用户、班级信息。
        """
        check_url = f"{self.base_url}?op=checklogin"

        # 为兼容从 web_signin 子目录直接运行的情况，这里动态修正 sys.path，
        # 确保可以导入项目根目录下的 utils.user_info
        try:
            from utils.user_info import get_user_and_class_info
        except ImportError:
            import os
            import sys

            # qr_login.py -> app -> web_signin -> BJMF(项目根目录)
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if root_dir not in sys.path:
                sys.path.append(root_dir)

            from utils.user_info import get_user_and_class_info

        for i in range(max_attempts):
            with self._lock:
                state = self._sessions.get(token)
                if not state:
                    return
                # 超时检查
                if time.time() - state.created_at > self.session_ttl:
                    state.expired = True
                    self._sessions[token] = state
                    return

            try:
                resp = sess.get(check_url)
                if resp.status_code != 200:
                    time.sleep(1)
                    continue

                try:
                    data = resp.json()
                except Exception:
                    time.sleep(1)
                    continue

                if not data.get("status"):
                    # 未扫码/未确认
                    time.sleep(1)
                    continue

                redirect_url = data.get("url")
                if not redirect_url:
                    time.sleep(1)
                    continue

                # 标记为已确认
                with self._lock:
                    state = self._sessions.get(token)
                    if not state:
                        return
                    state.is_scanned = True
                    state.is_confirmed = True
                    self._sessions[token] = state

                # 使用 StudentSession 逻辑获取 cookie
                cookie = self._get_cookie_from_redirect(redirect_url)

                # 调用现有逻辑获取用户 + 班级信息
                student = {"cookie": cookie}
                user_info, class_info = get_user_and_class_info(student)

                with self._lock:
                    state = self._sessions.get(token)
                    if not state:
                        return
                    state.cookie = cookie
                    state.user_name = user_info.get("name")
                    state.class_id = class_info.get("class_id")
                    state.class_name = class_info.get("class_name")
                    state.class_code = class_info.get("class_code")
                    self._sessions[token] = state

                return

            except Exception as e:
                with self._lock:
                    state = self._sessions.get(token)
                    if state:
                        state.error = f"轮询异常: {e}"
                        self._sessions[token] = state
                time.sleep(1)

        # 超过最大轮询次数
        with self._lock:
            state = self._sessions.get(token)
            if state:
                state.expired = True
                self._sessions[token] = state

    def _get_cookie_from_redirect(self, redirect_url: str) -> str:
        """
        复制 auto_add_user.StudentSession.access_login_url 的逻辑：
        访问重定向 URL 获取最终的 remember_student_* cookie。
        """
        sess = requests.Session()
        sess.headers.update(
            {
                "authority": "bj.k8n.cn",
                "scheme": "https",
                "path": "/student/uidlogin?",
                "sec-ch-ua": '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "dnt": "1",
                "upgrade-insecure-requests": "1",
                "prefer": "safe",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
                "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "sec-fetch-site": "cross-site",
                "sec-fetch-mode": "navigate",
                "sec-fetch-dest": "document",
                "referer": "https://login.b8n.cn/",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "priority": "u=0, i",
            }
        )

        url = "https://bj.k8n.cn/student/uidlogin?" + redirect_url.split("?")[1]
        resp = sess.get(url, allow_redirects=False)
        resp.raise_for_status()

        cookies = sess.cookies.get_dict()
        # 移除不必要的 cookie，与原脚本保持一致
        cookies.pop("s", None)
        cookie_pairs = [f"{k}={v}" for k, v in cookies.items()]
        if not cookie_pairs:
            raise ValueError("未获取到有效 cookie")
        return cookie_pairs[0]

    def get_session_state(self, token: str) -> Optional[QRSessionState]:
        with self._lock:
            return self._sessions.get(token)

