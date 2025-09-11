import re
import requests
from bs4 import BeautifulSoup
from tool.time_utils import get_current_time
from tool.message_sender import sendQQmessage, wx_send

# 签到任务
def Task(student):
    try:
        current_time = get_current_time()  # 获取当前时间
        print(f"当前时间: {current_time}")
        # print(f"进入检索...")
        name = student['name']
        ClassID = student['class']
        lat = student['lat']
        lng = student['lng']
        ACC = student['acc']
        Cookie_rs = re.search(r'remember_student_59ba36addc2b2f9401580f014c7f58ea4e30989d=[^;]+',
                                     student['cookie']).group(0)  # 提取cookie
        print(f"当前任务：{name},{ClassID},{lat},{lng},{ACC}")
        # print(f"实际需要的Cookie信息: {Cookie_rs}")
        QmsgKEY = student['QmsgKEY']
        WXKey = student['WXKey']
        # wx_send(WXKey) # Test1
        sendQQmessage(QmsgKEY) # Test2
        url = f'http://g8n.cn/student/course/{ClassID}/punchs'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; X64; Linux; Android 9;) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Firefox/92.0  WeChat/x86_64 Weixin NetType/4G Language/zh_CN ABI/x86_64',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/wxpic,image/tpg,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Referer': f'http://g8n.cn/student/course/{ClassID}',
            'Cookie': Cookie_rs
        }

        response = requests.get(url, headers=headers)
        print(f"进入_{name}_账号界面响应: {response}")

        # 查找扫码签到项
        pattern = re.compile(r'punchcard_(\d+)')
        matches = pattern.findall(response.text)
        if not matches:
            print("未找到在进行的签到/不在签到时间内")
            return

        # 处理每个签到项
        for match in matches:
            print(f"签到项: {match}")
            url1 = f"http://g8n.cn/student/punchs/course/{ClassID}/{match}"
            payload = {
                'id': match,
                'lat': lat,
                'lng': lng,
                'acc': ACC,
                'res': '',
                'gps_addr': ''
            }

            response = requests.post(url1, headers=headers, data=payload)
            # x = BeautifulSoup(response.text, 'html.parser')

            if response.status_code == 200:
                print("请求成功")
                soup_response = BeautifulSoup(response.text, 'html.parser')
                title_div = soup_response.find('div', id='title')

                if title_div:
                    title_text = title_div.text.strip()
                    if "已签到" in title_text:
                        print("已签到！无需再次签到")
                    elif "未开始" in title_text:
                        print("未开始签到,请稍后")
                    else:
                        print("本次签到成功")
                        # 任意选择一种通知方式
                        if QmsgKEY:
                            sendQQmessage(QmsgKEY)
                            print("存在QmsgKEY，已发送消息")
                        else:
                            print("QmsgKEY为空，未发送消息")

                        if WXKey:
                            wx_send(WXKey)
                            print("存在WXServerKey，已发送消息")
                        else:
                            print("WXServerKey为空，未发送消息")
            else:
                print(f"请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"发生错误{e}，跳过该配置......")