"""
用户和班级信息获取模块
负责从网页获取用户和班级信息
"""

import re
import requests
from bs4 import BeautifulSoup
import datetime


def get_current_time():
    """
    获取当前时间
    
    Returns:
        str: 格式化的当前时间字符串
    """
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")


def get_user_and_class_info(student):
    """
    获取用户和班级信息
    
    Args:
        student (dict): 学生配置信息
        
    Returns:
        tuple: (用户信息字典, 班级信息字典)
    """
    try:
        Cookie_rs = re.search(r'remember_student_59ba36addc2b2f9401580f014c7f58ea4e30989d=[^;]+',
                             student['cookie']).group(0)  # 提取cookie
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; X64; Linux; Android 9;) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Firefox/92.0  WeChat/x86_64 Weixin NetType/4G Language/zh_CN ABI/x86_64',
            'Cookie': Cookie_rs
        }
        
        # 获取用户个人信息
        url_my = "https://bjmf.k8n.cn/student/my"
        response_my = requests.get(url_my, headers=headers)
        
        user_info = {}
        class_info = {}
        
        if response_my.status_code == 200:
            # 提取用户信息
            gconfig_match = re.search(r'var gconfig=\{([^}]+)\}', response_my.text)
            if gconfig_match:
                gconfig_content = gconfig_match.group(1)
                
                # 提取用户名
                uname_match = re.search(r"uname:'([^']+)'", gconfig_content)
                
                user_info['name'] = uname_match.group(1) if uname_match else "未找到"
        else:
            print(f"获取用户信息页面失败，状态码: {response_my.status_code}")
        
        # 获取班级信息
        url_class = "https://bjmf.k8n.cn/student"
        response_class = requests.get(url_class, headers=headers)
        
        if response_class.status_code == 200:
            # 提取班级信息
            gconfig_match = re.search(r'var gconfig=\{([^\}]+)\}', response_class.text)
            if gconfig_match:
                gconfig_content = gconfig_match.group(1)
                
                # 提取班级相关信息
                cname_match = re.search(r"cname:'([^']+)'", gconfig_content)
                ctype_match = re.search(r"type:'([^']+)'", gconfig_content)
                class_id_match = re.search(r"id:'([^']+)'", gconfig_content)  # 提取班级ID
                
                class_info['cname'] = cname_match.group(1) if cname_match else "未找到"
                class_info['ctype'] = ctype_match.group(1) if ctype_match else "未找到"
                class_info['class_id'] = class_id_match.group(1) if class_id_match else "未找到"  # 添加班级ID提取
            
            # 如果从gconfig没有获取到班级ID，尝试从页面其他地方获取
            if class_info.get('class_id') == "未找到":
                # 查找课程链接获取课程ID
                soup_class = BeautifulSoup(response_class.text, 'html.parser')
                links = soup_class.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    course_match = re.search(r'/student/course/(\d+)', href)
                    if course_match:
                        class_info['class_id'] = course_match.group(1)
                        class_info['course_id'] = course_match.group(1)  # 课程ID
                        class_info['class_name'] = link.get_text().strip()
                        break
            
            # 提取课程ID和班级码
            soup_class = BeautifulSoup(response_class.text, 'html.parser')
            
            # 查找课程链接获取课程ID
            links = soup_class.find_all('a', href=True)
            for link in links:
                href = link['href']
                course_match = re.search(r'/student/course/(\d+)', href)
                if course_match:
                    class_info['course_id'] = course_match.group(1)  # 课程ID
                    class_info['class_name'] = link.get_text().strip()
                    break
                    
            # 更精确地查找班级码
            # 查找卡片中的班级码信息
            cards = soup_class.find_all('div', class_='card')
            for card in cards:
                card_text = card.get_text()
                # 查找类似"班级码 XXXX"的模式
                class_code_match = re.search(r'班级码\s*([A-Z0-9]{4,10})', card_text)
                if class_code_match:
                    class_info['class_code'] = class_code_match.group(1)
                    break
            
            # 如果没找到，使用备选方法
            if 'class_code' not in class_info:
                page_text = response_class.text
                # 查找更精确的班级码模式
                class_code_matches = re.findall(r'\b[A-Z0-9]{4,8}\b', page_text)
                # 过滤掉明显不是班级码的内容（如纯数字、时间戳等）
                filtered_codes = [code for code in class_code_matches 
                                if not (code.isdigit() and (len(code) > 6 or int(code) > 2030))]
                # 优先选择长度为5-6的字母数字组合
                preferred_codes = [code for code in filtered_codes 
                                 if len(code) >= 5 and len(code) <= 6 and not code.isdigit()]
                if preferred_codes:
                    class_info['class_code'] = preferred_codes[0]
                elif filtered_codes:
                    class_info['class_code'] = filtered_codes[0]
                else:
                    class_info['class_code'] = "未找到"
        else:
            print(f"获取班级信息页面失败，状态码: {response_class.status_code}")
        
        # 输出信息
        current_time = get_current_time()  # 获取当前时间
        # print(f"当前时间: {current_time}")
        print(f"==============={current_time}===================")
        print("=========== 用户和班级信息 ===============")
        print(f"用户姓名: {user_info.get('name', '未找到')}")
        print(f"班级名称: {class_info.get('class_name', '未找到')}")
        print(f"班级代号: {class_info.get('class_id', '未找到')}")
        print(f"班级码: {class_info.get('class_code', '未找到')}")
        return user_info, class_info
        
    except Exception as e:
        print(f"获取用户信息时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return {}, {}