import re
import requests
from bs4 import BeautifulSoup
import json
import datetime
import sys

# 获取当前时间
def get_current_time():
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")

# 读取外部 JSON 文件中的数据
with open('data.json', 'r') as file:
    json_data = json.load(file)
    students = json_data['students']  # 获取所有学生的数据

# 发送QQ消息通知
def sendQQmessage(QmsgKEY):
    url = f'https://qmsg.zendee.cn/send/{QmsgKEY}'
    current_time = get_current_time()  # 获取当前时间
    message = {
        "msg": f"{current_time}  签到成功！",
    }
    response = requests.post(url, data=message)
    if response.status_code == 200:
        print("QQ消息发送成功")
    else:
        print(f"QQ消息发送失败，状态码: {response.status_code}")


def wx_send(key):
    url = f'https://sctapi.ftqq.com/{key}.send'
    current_time = get_current_time()  # 获取当前时间

    data = {
        'text': f"{current_time}  签到成功！",
        'desp': "123123"
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("QQ消息发送成功")
    else:
        print(f"QQ消息发送失败，状态码: {response.status_code}")

# 签到任务
def Task(student):
    try:
        current_time = get_current_time()  # 获取当前时间
        print(f"当前时间: {current_time}")
        print(f"进入检索...")

        ClassID = student['class']
        lat = student['lat']
        lng = student['lng']
        ACC = student['acc']
        Cookie_rs = re.search(r'remember_student_59ba36addc2b2f9401580f014c7f58ea4e30989d=[^;]+',
                                     student['cookie']).group(0)  # 提取cookie
        QmsgKEY = student['QmsgKEY']
        WXKey = student['WXKey']
        # sendQQmessage(QmsgKEY) # 测试QQ推送
        # wx_send(WXKey) # 测试WX推送
        url = f'http://g8n.cn/student/course/{ClassID}/punchs'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; X64; Linux; Android 9;) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Firefox/92.0  WeChat/x86_64 Weixin NetType/4G Language/zh_CN ABI/x86_64',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/wxpic,image/tpg,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Referer': f'http://g8n.cn/student/course/{ClassID}',
            'Cookie': Cookie_rs
        }

        response = requests.get(url, headers=headers)
        print(f"进入界面响应: {response}")

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

                if title_div: # title_div根据签到后界面的主题显示判断是否签到成功
                    title_text = title_div.text.strip()
                    if "已签到" in title_text:
                        print("已签到！无需再次签到")
                    elif "未开始" in title_text:
                        print("未开始签到,请稍后")
                    else:
                        print("本次签到成功")
                        # 任意选择一种通知方式,若为空则不发送
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
    except:
        print("发生错误，跳过该配置")

if __name__ == "__main__":
    try:
        # 遍历所有学生，进行签到
        for student in students:
            Task(student)
            print("-----------------------------------------------")
    except KeyboardInterrupt:
        print("程序被手动中断")
    finally:
        print("程序执行完毕，自动退出")
        sys.exit(0)
