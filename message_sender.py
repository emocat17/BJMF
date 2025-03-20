import re
import requests
from bs4 import BeautifulSoup
import json
import datetime
import sys

def get_current_time():
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")

QmsgKEY = "Your_Qmsg_Key"
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







