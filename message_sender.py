#负责发送消息
import requests
import datetime

# 设置代理，根据自己实际需求来;这里是因为Qmsg需要，不用Qmsg的话可以删掉；
#设置代理；用于Qmsg访问
proxy = "http://127.0.0.1:7890"
proxies = {
    "http": proxy,
    "https": proxy
}
# 获取当前时间
def get_current_time():
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")

# 发送QQ消息通知
def send_qq_message(QmsgKEY):
    url = f'https://qmsg.zendee.cn/send/{QmsgKEY}'
    current_time = get_current_time()  # 获取当前时间
    message = {
        "msg": f"{current_time}  签到成功！",
    }
    response = requests.post(url, data=message , proxies=proxies)
    if response.status_code == 200:
        print("QQ消息发送成功")
    else:
        print(f"QQ消息发送失败，状态码: {response.status_code}")

# 发送微信消息通知
def send_wx_message(WXKey):
    url = f'https://sctapi.ftqq.com/{WXKey}.send'
    current_time = get_current_time()  # 获取当前时间

    data = {
        'text': f"{current_time}  签到成功！",
        'desp': "签到任务完成"
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("WX消息发送成功")
    else:
        print(f"WX消息发送失败，状态码: {response.status_code}")
