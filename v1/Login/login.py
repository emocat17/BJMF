import requests
import re
import qrcode
import time
from bs4 import BeautifulSoup
from Login.redirect import  StudentSession
from PIL import Image

class QRCodeLogin:
    def __init__(self,url="https://login.b8n.cn/qr/weixin/student/2"):
        self.base_url = url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36 MicroMessenger/7.0.10.1580(0x27000A50) Process/tools NetType/WIFI Language/zh_CN ABI/arm64',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://wx.qq.com/',
            'sec-ch-ua-platform': 'Android',
            'X-Requested-With': 'XMLHttpRequest',
        })

    def extract_qr_content(self, html):
        """从HTML中提取二维码内容"""
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        script = scripts[2]

        # re匹配（sess、tm、sign）
        pattern = r'https?://[^\s"\']+'
        urls = re.findall(pattern, str(script))[0]

        sess_pattern = r'[?&]sess=([^&]+)'
        tm_pattern = r'[?&]tm=([^&]+)'
        sign_pattern = r'[?&]sign=([^&]+)'

        sess_match = re.search(sess_pattern, urls)
        tm_match = re.search(tm_pattern, urls)
        sign_match = re.search(sign_pattern, urls)

        sess = sess_match.group(1) if sess_match else None
        tm = tm_match.group(1) if tm_match else None
        sign = sign_match.group(1) if sign_match else None

        # print(f"sess: {sess}")
        # print(f"tm: {tm}")
        # print(f"sign: {sign}")
        params = {
            'sess': sess,
            'tm': tm,
            'sign': sign
        }
        return params

    def create_qrcode_image(self, params, filename=None):
        """创建二维码图片"""
        # 构建URL
        wx_url = "http://login.b8n.cn/weixin/login/student/2"
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        qr_url = f"{wx_url}?{query_string}"

        # print(f" 二维码内容: {qr_url}")

        # 生成二维码
        img = qrcode.make(qr_url)
        img.save("login_qrcode.png")

        print(f" 二维码已保存: login_qrcode.png")
        print(f" 请用微信扫描二维码登录")
        image = Image.open('login_qrcode.png')
        # 显示二维码
        image.show()

    def poll_login_status(self, max_attempts=20):
        """轮询登录状态"""
        check_url = f"{self.base_url}?op=checklogin"

        for i in range(max_attempts):
            print(f"轮询检查登录状态... ({i + 1}/{max_attempts})")

            try:
                response = self.session.get(check_url)
                # print("轮询响应" + response.text)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('status'):
                            redirect_url = data.get('url')
                            print(f"登录成功！获取跳转URL: {redirect_url}")

                            return True, redirect_url
                        else:
                            print(f"等待扫码... ")
                    except:
                        print("响应不是JSON格式")

            except Exception as e:
                print(f"请求失败: {e}")

            time.sleep(1)  # 等待1秒

        print("二维码已过期")
        return False, None

    def run(self):
        html = self.session.get(self.base_url).text
        params = self.extract_qr_content(html)

        """运行完整流程"""
        print("=" * 50)
        print("微信扫码登录流程开始")
        print("=" * 50)

        # 创建二维码图片
        print("\n1. 生成二维码图片...")
        self.create_qrcode_image(params)

        print("\n2. 请用微信扫描二维码...")

        # 轮询登录状态
        print("\n3. 等待扫码确认...")
        return self.poll_login_status()

    def external_getCookieAndCourseId(self):
        # 爬取并生成二维码
        ok = False
        url = ""
        for retry in range(3):
            print(f"\n\n尝试 #{retry + 1}: \n", end="")
            ok, url = scraper.run()
            if ok: break

        if ok:
            s = StudentSession()
            cookie = s.access_login_url(url)
            course_id = s.getClassId()
            return cookie, course_id
        return None, None

if __name__ == '__main__':
    scraper = QRCodeLogin()
    scraper.external_getCookieAndCourseId()
