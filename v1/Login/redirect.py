import re

import requests
from bs4 import BeautifulSoup


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
        self.cookie=None
        self.course_id=None

    def access_login_url(self,redirect_url:str)->str:
        """
           这里禁止重定向是因为跳转到了/student页面后只有's'会话的cookie,没有remember_student的cookie
           只有在这个跳转页里才发现了remember_student，有了remember_student，就可以用cookie去访问其他页面了
        """
        # url处理
        url = "https://bj.k8n.cn/student/uidlogin?" + redirect_url.split('?')[1]

        response=self.session.get(url, allow_redirects=False)
        print(f"状态码: {response.status_code}")
        # print(f"最终URL: {response.url}")
        # print(f"响应长度: {len(response.text)}")
        # print(f"响应预览: {response.text}")
        # 保存cookies供后续使用
        cookies = self.session.cookies.get_dict()
        #去除掉没用的cookie
        cookies.pop("s")

        # 使用列表推导式生成键值对字符串
        cookie= [f"{key}={value}" for key, value in cookies.items()][0]

        print(f"获取的Cookies: {cookie}")
        self.cookie=cookie
        return cookie

    def getClassId(self)->str:
        """访问其他页面"""
        url = "http://bj.k8n.cn/student"
        resp=self.session.get(url)
        print(f"学生页面状态码：{resp.status_code}")
        # print(f"学生页面预览页：{resp.text}")

        soup = BeautifulSoup(resp.text, 'html.parser')
        div_element = soup.find('div', class_='card mb-3 course')
        course_id = div_element.get('course_id')
        print(f"ClassID: {course_id}")
        self.course_id=course_id
        return course_id

    def other(self):
        """可以get其他子网获取信息:
        """
        pass

# 立即执行
if __name__ == '__main__':
    s = StudentSession()
    s.access_login_url("http://bj.k8n.cn/student?uid=2789785&tm=1764778952&sign=acf6e7872ea5036bf66c94d05bb435c4&option=&")