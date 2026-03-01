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


def send_summary_notification(wx_key, results):
    """
    发送签到汇总通知
    
    Args:
        wx_key (str): 微信Server酱API密钥
        results (list): 签到结果列表，每个元素为 (用户名, 状态) 的元组
    """
    if not wx_key or not wx_key.strip():
        return
    
    try:
        # 统计结果
        success_list = []
        failed_list = []
        
        for name, status in results:
            if status == 'success':
                success_list.append(name)
            elif status == 'already_signed':
                success_list.append(name)  # 已签到也算成功
            else:
                failed_list.append(name)
        
        # 生成标题
        if len(failed_list) == 0:
            title = "全部签到成功"
        else:
            title = "部分失败"
        
        # 生成描述
        desp_parts = []
        if success_list:
            success_str = "，".join([f"{name}成功" for name in success_list])
            desp_parts.append(success_str)
        if failed_list:
            failed_str = "，".join([f"{name}失败" for name in failed_list])
            desp_parts.append(failed_str)
        
        desp = "，".join(desp_parts)
        
        # 发送通知
        url = f'https://sctapi.ftqq.com/{wx_key}.send'
        data = {
            'text': title,
            'desp': desp
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print(f"汇总通知发送成功: {title}")
        else:
            print(f"汇总通知发送失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"发送汇总通知时出错: {e}")