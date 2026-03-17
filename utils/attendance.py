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
        
    Returns:
        tuple: (用户名, 签到状态) 
               状态可能为: 'success'(成功), 'already_signed'(已签到), 'not_started'(未开始), 
                          'no_sign_in'(无签到), 'error'(错误), 'skip'(跳过)
    """
    try:
        # 先获取用户和班级信息
        user_info, class_info = get_user_and_class_info(student)
        
        # 检查是否成功获取了用户信息，如果没有则跳过该用户
        user_name = user_info.get('name', '未找到')
        if user_name == "未找到":
            print(f"无法获取用户信息，可能是cookie过期或无效，跳过用户 {student['name']} 的签到任务")
            return student.get('name', '未知'), 'skip'
            
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
            return name, 'skip'
            
        lat = student['lat']
        lng = student['lng']
        ACC = student['acc']
        
        # 使用 requests.Session 保持会话
        session = requests.Session()
        
        # 设置Headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; X64; Linux; Android 9;) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Firefox/92.0  WeChat/x86_64 Weixin NetType/4G Language/zh_CN ABI/x86_64',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/wxpic,image/tpg,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        }
        
        # 添加Cookie
        # 优先使用完整cookie字符串，如果格式不标准则尝试提取
        # requests session headers 需要字典或字符串，直接设置 header 即可
        headers['Cookie'] = student['cookie']
        session.headers.update(headers)
        
        # 1. 预热请求：访问个人中心以触发 remember_me 自动登录并获取 session cookie
        warmup_url = "https://bjmf.k8n.cn/student/my"
        try:
            session.get(warmup_url, timeout=10)
            # print("会话预热完成")
        except Exception as e:
            print(f"会话预热失败: {e}")

        # 2. 请求签到列表
        url = f'https://bjmf.k8n.cn/student/course/{ClassID}/punchs'
        # 更新Referer
        session.headers.update({'Referer': f'https://bjmf.k8n.cn/student/course/{ClassID}'})

        response = session.get(url, timeout=10)

        # 查找扫码签到项
        matches = []
        
        # 策略1: 查找 punchcard_ID 格式
        pattern_id = re.compile(r'punchcard_(\d+)')
        matches_id = pattern_id.findall(response.text)
        matches.extend(matches_id)
        
        # 策略2: 查找链接格式 /student/punchs/course/{ClassID}/{ID}
        # 注意：这里使用 \d+ 匹配 ClassID，以适应可能的变化
        # 支持多种签到类型: punchs (standard), punchw (weekly), puncha (assignment) 等
        pattern_link = re.compile(r'/student/punch\w+/course/\d+/(\d+)')
        matches_link = pattern_link.findall(response.text)
        matches.extend(matches_link)
        
        # 策略3: 检查是否直接跳转到了签到页面 (根据URL判断)
        # URL格式通常为: .../student/punchs/course/{ClassID}/{ID}
        current_url = response.url
        # print(f"Debug: Current URL: {current_url}")
        
        url_match = re.search(r'/student/punchs/course/\d+/(\d+)', current_url)
        if url_match:
            print(f"检测到直接跳转至签到页面，ID: {url_match.group(1)}")
            matches.append(url_match.group(1))
        
        # 去重
        matches = list(set(matches))

        if not matches:
            # 尝试检测是否已经签到
            soup_check = BeautifulSoup(response.text, 'html.parser')
            
            # 检查方式1: punch-success-info
            success_info = soup_check.find(class_='punch-success-info')
            if success_info and "已签到" in success_info.get_text():
                print(f"检测到已完成签到: {success_info.get_text(strip=True)}")
                return name, 'already_signed'

            # 检查方式2: punch-status
            status_div = soup_check.find(class_='punch-status')
            if status_div and "已签到" in status_div.get_text():
                print(f"检测到已完成签到: {status_div.get_text(strip=True)}")
                return name, 'already_signed'

            print("未找到在进行的签到/不在签到时间内")
            print(f"Debug: Status Code: {response.status_code}")
            
            # Save HTML for debugging
            with open("debug_html.txt", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Debug: HTML saved to debug_html.txt")
            
            # print(f"Debug: Response Text Preview: {response.text[:200]}") # Uncomment for more details
            return name, 'no_sign_in'

        # 处理每个签到项
        for match in matches:
            print(f"签到项: {match}")
            
            # 从HTML中提取实际的链接类型 (punchs, punchw, puncha 等)
            punch_type = 'punchs'  # 默认类型
            # 查找包含该签到ID的链接，获取实际的punch类型
            punch_pattern = re.compile(r'/student/(punch\w+)/course/\d+/' + str(match))
            punch_match = punch_pattern.search(response.text)
            if punch_match:
                punch_type = punch_match.group(1)
                print(f"检测到签到类型: {punch_type}")
            
            url1 = f"https://bjmf.k8n.cn/student/{punch_type}/course/{ClassID}/{match}"
            payload = {
                'id': match,
                'lat': lat,
                'lng': lng,
                'acc': ACC,
                'res': '',
                'gps_addr': ''
            }

            response = session.post(url1, data=payload, timeout=10)
            # x = BeautifulSoup(response.text, 'html.parser')

            if response.status_code == 200:
                print("网络请求成功")
                soup_response = BeautifulSoup(response.text, 'html.parser')
                title_div = soup_response.find('div', id='title')

                if title_div:
                    title_text = title_div.text.strip()
                    if "已签到" in title_text:
                        print("已签到！无需再次签到")
                        return name, 'already_signed'
                    elif "未开始" in title_text:
                        print("未开始签到,请稍后")
                        return name, 'not_started'
                    else:
                        print("本次签到成功")
                        return name, 'success'
                else:
                    # 如果没有找到title_div，可能是签到成功但没有显示
                    print("签到请求成功，但无法确定状态")
                    return name, 'success'
            else:
                print(f"请求失败，状态码: {response.status_code}")
                return name, 'error'
        
        # 如果没有匹配到任何签到项，返回无签到状态
        return name, 'no_sign_in'
    except Exception as e:
        print(f"发生错误{e}，跳过该配置......")
        return student.get('name', '未知'), 'error'