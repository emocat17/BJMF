import requests
from tool.time_utils import get_current_time

# 发送QQ消息通知
def sendQQmessage(QmsgKEY):
    url = f"https://qmsg.zendee.cn/send/{QmsgKEY}"
    # headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    current_time = get_current_time()  # 获取当前时间
    message = {
        "msg": f"{current_time}  签到成功！",
    }
    # response = requests.post(url, data=message, proxies=proxies)
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
        print("WX消息发送成功")
    else:
        print(f"WX消息发送失败，状态码: {response.status_code}")