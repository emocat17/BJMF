"""
消息通知模块
负责发送QQ和微信消息通知
"""

import requests
from .user_info import get_current_time


def sendQQmessage(QmsgKEY):
    """
    发送QQ消息通知
    
    Args:
        QmsgKEY (str): Qmsg API密钥
    """
    try:
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
    except Exception as e:
        print(f"发送QQ消息时出错: {e}")


def wx_send(key):
    """
    发送微信消息通知
    
    Args:
        key (str): 微信Server酱API密钥
    """
    try:
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
    except Exception as e:
        print(f"发送微信消息时出错: {e}")