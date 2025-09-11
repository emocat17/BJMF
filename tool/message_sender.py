import requests
from tool.time_utils import get_current_time

# 设置请求超时时间
REQUEST_TIMEOUT = 10

# 发送QQ消息通知
def sendQQmessage(QmsgKEY):
    # 检查QmsgKEY是否为空
    if not QmsgKEY:
        print("QQ消息发送失败，QmsgKEY为空")
        return False
        
    try:
        url = f"https://qmsg.zendee.cn/send/{QmsgKEY}"
        current_time = get_current_time()  # 获取当前时间
        message = {
            "msg": f"{current_time}  签到成功！",
        }
        
        response = requests.post(url, data=message, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            print("QQ消息发送成功")
            return True
        else:
            print(f"QQ消息发送失败，状态码: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("QQ消息发送失败，请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"QQ消息发送失败，网络异常: {e}")
        return False
    except Exception as e:
        print(f"QQ消息发送失败，未知错误: {e}")
        return False


def wx_send(key):
    # 检查key是否为空
    if not key:
        print("微信消息发送失败，key为空")
        return False
        
    try:
        url = f'https://sctapi.ftqq.com/{key}.send'
        current_time = get_current_time()  # 获取当前时间

        data = {
            'text': f"{current_time}  签到成功！",
            'desp': "签到成功"
        }
        
        response = requests.post(url, data=data, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            print("WX消息发送成功")
            return True
        else:
            print(f"WX消息发送失败，状态码: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("微信消息发送失败，请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"微信消息发送失败，网络异常: {e}")
        return False
    except Exception as e:
        print(f"微信消息发送失败，未知错误: {e}")
        return False