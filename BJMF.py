import re
import requests
from bs4 import BeautifulSoup
import json
import datetime
import sys
import time
#设置代理；用于Qmsg访问,网络连接错误时尝试
# proxies = {
#     "http": "http://127.0.0.1:7890",
#     "https": "http://127.0.0.1:7890"
# }

# 获取当前时间
def get_current_time():
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")

# 读取外部 JSON 文件中的数据

config_file = 'data.json'

with open(config_file, 'r', encoding='utf-8') as file:
    json_data = json.load(file)
    students = json_data['students']  # 获取所有学生的数据

# 获取用户信息和班级信息
def get_user_and_class_info(student):
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

# 签到任务
def Task(student):
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

# 保存更新后的配置到文件
def save_config(config_data, config_file):
    """保存配置数据到文件"""
    try:
        with open(config_file, 'w', encoding='utf-8') as file:
            json.dump(config_data, file, ensure_ascii=False, indent=4)
        print(f"配置文件 {config_file} 更新成功")
    except Exception as e:
        print(f"保存配置文件时出错: {e}")

if __name__ == "__main__":
    # 检查是否是测试消息发送模式
    if len(sys.argv) > 1 and (sys.argv[1] == 'test_send' or sys.argv[1] == 'test_msg'):
        # 测试消息发送功能
        print("测试消息发送功能...")
        if students:
            student = students[0]  # 使用第一个学生配置
            QmsgKEY = student['QmsgKEY']
            WXKey = student['WXKey']
            
            # 测试Qmsg消息发送
            if QmsgKEY and QmsgKEY.strip():
                print("正在测试发送QQ消息...")
                sendQQmessage(QmsgKEY)
                print("存在QmsgKEY，已发送消息")
            else:
                print("QmsgKEY为空，不发送QQ消息")
            
            # 测试微信消息发送
            if WXKey and WXKey.strip():
                print("正在测试发送微信消息...")
                wx_send(WXKey)
                print("存在WXServerKey，已发送消息")
            else:
                print("WXKey为空，不发送微信消息")
    else:
        try:
            # 遍历所有学生，进行签到
            # 先读取原始配置文件用于更新
            with open(config_file, 'r', encoding='utf-8') as file:
                original_config = json.load(file)
            
            for i, student in enumerate(students):
                # 如果class字段为空，则先获取用户和班级信息来填充
                if not student.get('class') or student['class'].strip() == "":
                    user_info, class_info = get_user_and_class_info(student)
                    
                    # 检查是否成功获取了用户信息，如果没有则跳过该用户
                    user_name = user_info.get('name', '未找到')
                    if user_name == "未找到":
                        print(f"{student['name']}_cookie过期/无效")
                        print("==========================================")
                        print("==========================================\n\n")
                        continue
                    
                    # 获取从网页获取的班级ID
                    class_id = class_info.get('class_id')
                    if class_id and class_id != "未找到":
                        # 更新内存中的学生配置
                        student['class'] = class_id
                        # 更新原始配置数据
                        original_config['students'][i]['class'] = class_id
                        print(f"已为用户 {student['name']} 设置class字段为: {class_id}")
                    else:
                        print(f"无法获取用户 {student['name']} 的班级ID")
                        print("==========================================")
                        print("==========================================\n\n")
                        continue
                
                Task(student)
                print("==========================================")
                print("==========================================\n\n")
            
            # 保存更新后的配置到文件
            save_config(original_config, config_file)
        except KeyboardInterrupt:
            print("程序被手动中断")
        finally:
            print("程序执行完毕，自动退出")
            time.sleep(3)
            sys.exit(0)
