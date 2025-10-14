"""
签到功能模块
负责执行签到任务
"""

import re
import requests
from bs4 import BeautifulSoup
from .user_info import get_user_and_class_info
from .notification import sendQQmessage, wx_send


def Task(student):
    """
    执行签到任务
    
    Args:
        student (dict): 学生配置信息
    """
    try:
        # 先获取用户和班级信息
        user_info, class_info = get_user_and_class_info(student)
        
        # 检查是否成功获取了用户信息，如果没有则跳过该用户
        user_name = user_info.get('name', '未找到')
        if user_name == "未找到":
            print(f"无法获取用户信息，可能是cookie过期或无效，跳过用户 {student['name']} 的签到任务")
            return
            
        # 使用从网页获取的班级ID，如果获取失败则使用配置文件中的
        ClassID = class_info.get('class_id', student['class'])
        if not ClassID or ClassID == "未找到" or not ClassID:
            ClassID = student['class']
            
        # 使用从网页获取的姓名，如果获取失败则使用配置文件中的
        name = user_info.get('name', student['name'])
        if not name or name == "未找到":
            name = student['name']
            
        # 检查是否成功获取了班级信息，如果没有也跳过该用户
        class_name = class_info.get('class_name', '未找到')
        if class_name == "未找到" and not ClassID:
            print(f"无法获取班级信息，跳过用户 {name} 的签到任务")
            return
            
        lat = student['lat']
        lng = student['lng']
        ACC = student['acc']
        Cookie_rs = re.search(r'remember_student_59ba36addc2b2f9401580f014c7f58ea4e30989d=[^;]+',
                                     student['cookie']).group(0)  # 提取cookie
        # print(f"实际需要的Cookie信息: {Cookie_rs}")
        QmsgKEY = student['QmsgKEY']
        WXKey = student['WXKey']
        url = f'http://g8n.cn/student/course/{ClassID}/punchs'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; X64; Linux; Android 9;) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Firefox/92.0  WeChat/x86_64 Weixin NetType/4G Language/zh_CN ABI/x86_64',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/wxpic,image/tpg,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Referer': f'http://g8n.cn/student/course/{ClassID}',
            'Cookie': Cookie_rs
        }

        response = requests.get(url, headers=headers)

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
                print("网络请求成功")
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
                        if QmsgKEY and QmsgKEY.strip():
                            sendQQmessage(QmsgKEY)
                            print("存在QmsgKEY，已发送消息")
                        # 如果QmsgKEY为空，则不输出任何内容

                        if WXKey and WXKey.strip():
                            wx_send(WXKey)
                            print("存在WXServerKey，已发送消息")
                        # 如果WXKey为空，则不输出任何内容
            else:
                print(f"请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"发生错误{e}，跳过该配置......")