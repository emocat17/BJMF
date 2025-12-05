import requests
import re
import qrcode
import time
from bs4 import BeautifulSoup
from PIL import Image

# 导入自定义模块
from utils.user_info import get_user_and_class_info


class QRCodeLogin:
    def __init__(self, url="https://bjmf.k8n.cn/weixin/qrlogin/student"):
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
        # 直接从img标签获取二维码URL
        qrcode_div = soup.find('div', id='qrcode')
        img_tag = qrcode_div.find('img')
        qrcode_url = img_tag['src']
        print(f"找到二维码图片URL: {qrcode_url}")
        
        # 从URL中提取ticket参数
        ticket_pattern = r'ticket=([^\s"\']+)'
        ticket_match = re.search(ticket_pattern, qrcode_url)
        ticket = ticket_match.group(1) if ticket_match else None
        
        # 返回包含二维码URL的字典
        return {
            'qrcode_url': qrcode_url,
            'ticket': ticket
        }

    def create_qrcode_image(self, params, filename=None):
        """创建二维码图片"""
        # 直接使用从HTML中获取的二维码图片URL
        qrcode_img_url = params['qrcode_url']
        print(f" 二维码图片URL: {qrcode_img_url}")
        
        # 下载二维码图片
        response = self.session.get(qrcode_img_url)
        if response.status_code == 200:
            with open("login_qrcode.png", "wb") as f:
                f.write(response.content)
            print(f" 二维码已保存: login_qrcode.png")
            print(f" 请用微信扫描二维码登录")
            # 显示二维码
            image = Image.open('login_qrcode.png')
            image.show()
        else:
            print(f" 下载二维码失败，状态码: {response.status_code}")

    def poll_login_status(self, max_attempts=20):
        """轮询登录状态"""
        check_url = f"{self.base_url}?op=checklogin"

        for i in range(max_attempts):
            print(f"轮询检查登录状态... ({i + 1}/{max_attempts})")

            try:
                response = self.session.get(check_url)
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
        """运行完整的二维码登录流程"""
        print("=" * 50)
        print("微信扫码登录流程开始")
        print("=" * 50)
        
        # 获取登录页面HTML
        html = self.session.get(self.base_url).text
        # 提取二维码内容
        params = self.extract_qr_content(html)
        
        # 创建二维码图片
        print("\n1. 生成二维码图片...")
        self.create_qrcode_image(params)

        print("\n2. 请用微信扫描二维码...")
        
        # 轮询登录状态
        print("\n3. 等待扫码确认...")
        return self.poll_login_status()


class StudentSession:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "authority": "bj.k8n.cn",
            "scheme": "https",
            "path": "/student/uidlogin?",
            "sec-ch-ua": '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "dnt": "1",
            "upgrade-insecure-requests": "1",
            "prefer": "safe",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-fetch-site": "cross-site",
            "sec-fetch-mode": "navigate",
            "sec-fetch-dest": "document",
            "referer": "https://login.b8n.cn/",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "priority": "u=0, i",
        })
        self.cookie = None
        self.course_id = None

    def access_login_url(self, redirect_url: str) -> str:
        """
        访问登录URL获取cookie
        """
        # url处理
        url = "https://bj.k8n.cn/student/uidlogin?" + redirect_url.split('?')[1]

        response = self.session.get(url, allow_redirects=False)
        print(f"状态码: {response.status_code}")
        
        # 保存cookies供后续使用
        cookies = self.session.cookies.get_dict()
        # 去除掉没用的cookie
        cookies.pop("s")

        # 使用列表推导式生成键值对字符串
        cookie = [f"{key}={value}" for key, value in cookies.items()][0]

        print(f"获取的Cookies: {cookie}")
        self.cookie = cookie
        return cookie

    def getClassId(self) -> str:
        """访问其他页面获取ClassID"""
        url = "http://bj.k8n.cn/student"
        resp = self.session.get(url)
        print(f"学生页面状态码：{resp.status_code}")

        soup = BeautifulSoup(resp.text, 'html.parser')
        div_element = soup.find('div', class_='card mb-3 course')
        course_id = div_element.get('course_id')
        print(f"ClassID: {course_id}")
        self.course_id = course_id
        return course_id


def main():
    """主函数"""
    # 创建QRCodeLogin实例
    qr_login = QRCodeLogin()
    
    # 运行登录流程，获取登录成功后的跳转URL
    ok = False
    url = ""
    for retry in range(3):
        print(f"\n\n尝试 #{retry + 1}: \n", end="")
        ok, url = qr_login.run()
        if ok: 
            break

    if ok:
        # 创建StudentSession实例，获取cookie
        s = StudentSession()
        cookie = s.access_login_url(url)
        
        # 使用获取到的cookie调用get_user_and_class_info函数
        student = {
            'cookie': cookie
        }
        
        print("\n" + "=" * 50)
        print("开始获取用户和班级信息")
        print("=" * 50)
        
        # 调用user_info.py中的函数获取信息
        user_info, class_info = get_user_and_class_info(student)
        
        # 清理临时文件
        import os
        if os.path.exists("login_qrcode.png"):
            os.remove("login_qrcode.png")
            print("\n二维码图片已清理")
        
        # 将获取到的信息写入data.json
        print("\n" + "=" * 50)
        print("开始写入用户信息到data.json")
        print("=" * 50)
        
        import json
        import os
        
        # 定义data.json文件路径
        data_file = "data.json"
        
        # 读取现有的data.json文件
        existing_data = {
            "students": []
        }
        
        if os.path.exists(data_file):
            with open(data_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        
        # 构建新的学生信息
        full_name = user_info.get("name", "")
        
        # 处理用户名：如果存在同名的拼音格式，就使用相同的格式；否则使用中文姓名
        # 例如：如果已经有"caiyonghao"，就使用相同格式；否则使用"蔡永昊"
        student_name = full_name
        
        # 检查是否存在同名的拼音格式
        for student in existing_data["students"]:
            if student["name"] == full_name.lower():
                # 如果已经存在拼音格式，就使用拼音格式
                student_name = student["name"]
                break
        
        new_student = {
            "name": student_name,
            "class": class_info.get("class_id", ""),
            "lat": "",  # 自行添加
            "lng": "",  # 自行添加
            "acc": "30",  # 使用默认值
            "cookie": cookie,
            "QmsgKEY": "",  # 默认为空
            "WXKey": ""  # 默认为空
        }
        
        # 检查新用户是否已经存在于现有数据中
        # 可以通过name或cookie来判断
        existing_names = [student["name"] for student in existing_data["students"]]
        
        if new_student["name"] not in existing_names:
            # 添加新用户
            existing_data["students"].append(new_student)
            print(f"用户 {new_student['name']} 已添加到data.json")
        else:
            # 更新现有用户信息
            for i, student in enumerate(existing_data["students"]):
                if student["name"] == new_student["name"]:
                    existing_data["students"][i] = new_student
                    print(f"用户 {new_student['name']} 信息已更新")
                    break
        
        # 将更新后的数据写回到data.json文件
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        
        print("data.json更新完成")
        
        # 打印更新后的data.json内容
        print("\n" + "=" * 50)
        print("更新后的data.json内容：")
        print("=" * 50)
        with open(data_file, "r", encoding="utf-8") as f:
            print(json.dumps(json.load(f), ensure_ascii=False, indent=2))
    else:
        print("\n登录失败，无法获取用户信息")


if __name__ == '__main__':
    main()
