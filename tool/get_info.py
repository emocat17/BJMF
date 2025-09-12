import requests
import json
import re
import os

def load_students_data(use_test_file=False, test_file_name='data_test.json'):
    """加载学生数据"""
    try:
        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 根据参数选择使用测试文件还是正式文件
        if use_test_file:
            data_file_path = os.path.join(script_dir, '..', test_file_name)
        else:
            data_file_path = os.path.join(script_dir, '..', 'data.json')
        
        print(f"尝试加载文件: {data_file_path}")
        
        # 读取JSON文件
        with open(data_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        students = data.get('students', [])
        print(f" 成功加载 {len(students)} 个学生配置")
        return students
    except FileNotFoundError:
        print(f" 未找到 {test_file_name if use_test_file else 'data.json'} 文件")
        return []
    except json.JSONDecodeError as e:
        print(f" {test_file_name if use_test_file else 'data.json'} 格式错误: {e}")
        return []
    except Exception as e:
        print(f" 加载 {test_file_name if use_test_file else 'data.json'} 时发生错误: {e}")
        return []

def extract_remember_cookie(cookie_str):
    """从完整cookie中提取remember_student cookie"""
    cookie_match = re.search(r'remember_student_59ba36addc2b2f9401580f014c7f58ea4e30989d=[^;]+', cookie_str)
    if cookie_match:
        return cookie_match.group(0)
    return None

def login_and_get_user_info(student):
    """使用cookie登录并获取用户信息"""
    name = student.get('name', 'Unknown')
    full_cookie = student.get('cookie', '')
    
    print(f"=== 学生: {name} ===")
    print(f" 学生数据: {student}")
    
    # 提取关键cookie
    remember_cookie = extract_remember_cookie(full_cookie)
    if not remember_cookie:
        print(" 未找到 remember_student cookie")
        return None, None
    
    print(f" 使用的关键 Cookie: {remember_cookie}")
    
    # 构造请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; X64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Cookie': remember_cookie,
    }
    
    return headers, student

def get_user_profile(headers):
    """获取用户个人信息"""
    # 创建新的session确保无缓存
    session = requests.Session()
    session.headers.update(headers)
    
    # 访问个人页面
    profile_url = "https://bjmf.k8n.cn/student/my"
    
    try:
        response = session.get(profile_url, timeout=10)
        # 提取用户姓名和学号
        content = response.text
        
        # 查找姓名 (从JavaScript变量中提取)
        name_pattern = r'uname[\'"]?\s*:\s*[\'"]([^\'"]+)[\'"]'
        name_match = re.search(name_pattern, content)
        
        name = name_match.group(1).strip() if name_match else ""
        
        # 查找学号 (优先从HTML中查找正确的学号)
        # 首先尝试从用户信息区域查找学号 (在姓名下方的div中)
        id_pattern = r'<div class="font-weight-bold">[^<]+</div>\s*<div>(\d{9})</div>'
        id_match = re.search(id_pattern, content)
        
        # 如果没找到，尝试其他模式查找9位数字的学号
        if not id_match:
            id_pattern = r'(\d{9})'
            id_matches = re.findall(id_pattern, content)
            # 过滤掉可能的时间戳等非学号的9位数字
            valid_ids = [id for id in id_matches if not id.startswith(('1757596', '2024'))]
            if valid_ids:
                student_id = valid_ids[0]
            else:
                student_id = ""
        else:
            student_id = id_match.group(1).strip() if id_match else ""
        
        print(f" 姓名: {name}")
        print(f" 学号: {student_id}")
        
        # 检查是否成功获取到用户信息
        # 以姓名是否返回的字段长度为空来判断cookie是否错误
        if len(name) == 0:
            print(" 未能获取到有效的用户信息")
            print(" cookie已过期或不正确，请重新获取")
            return None
        
        return {
            "name": name,
            "student_id": student_id
        }
            
    except requests.exceptions.RequestException as e:
        print(f" 个人页面访问异常: {e}")
        return None

def update_data_json(student_name, course_id, use_test_file=False, test_file_name='data_test.json'):
    """更新data.json文件中的班级信息"""
    try:
        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 根据参数选择使用测试文件还是正式文件
        if use_test_file:
            data_file_path = os.path.join(script_dir, '..', test_file_name)
        else:
            data_file_path = os.path.join(script_dir, '..', 'data.json')
        
        print(f" 尝试更新文件: {data_file_path}")
        
        # 读取现有数据
        with open(data_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        print(f" 文件中找到 {len(data.get('students', []))} 个学生")
        
        # 查找并更新对应学生的班级信息
        updated = False
        for i, student in enumerate(data.get('students', [])):
            print(f" 检查第{i+1}个学生: {student.get('name', 'Unknown')}")
            if student.get('name') == student_name:
                print(f" 找到匹配学生: {student_name}")
                if not student.get('class') or student.get('class') == "":
                    student['class'] = course_id
                    updated = True
                    print(f" 已更新学生 {student_name} 的班级信息为: {course_id}")
                else:
                    print(f" 学生 {student_name} 的班级信息已存在: {student.get('class')}")
                break
            else:
                print(f" 学生名称不匹配: {student.get('name', 'Unknown')} != {student_name}")
        
        # 如果找到并更新了学生信息，则写回文件
        if updated:
            with open(data_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            print(f" {test_file_name if use_test_file else 'data.json'} 文件更新成功")
        elif not updated and student_name:
            print(f" 未找到学生 {student_name} 或无需更新")
        
        return updated
    except FileNotFoundError:
        print(f" 未找到 {test_file_name if use_test_file else 'data.json'} 文件")
        return False
    except json.JSONDecodeError as e:
        print(f" {test_file_name if use_test_file else 'data.json'} 格式错误: {e}")
        return False
    except Exception as e:
        print(f" 更新 {test_file_name if use_test_file else 'data.json'} 时发生错误: {e}")
        return False

def get_class_info(headers):
    """获取班级信息"""
    # 创建新的session确保无缓存
    session = requests.Session()
    session.headers.update(headers)
    
    # 访问主页
    home_url = "https://bjmf.k8n.cn/student"
    
    try:
        response = session.get(home_url, timeout=10)
        
        # 不再以状态码200作为判断依据，而是以姓名是否返回的字段长度为空来判断cookie是否错误
        content = response.text
        
        # 查找班级码
        class_code_pattern = r'班级码[：:]\s*([A-Z0-9]+)'
        codes = re.findall(class_code_pattern, content)
        
        # 如果没有找到班级码，尝试其他模式
        if not codes:
            # 查找类似 "班级码 3GPDWY" 的模式
            alt_pattern = r'班级码\s+([A-Z0-9]{4,8})'
            codes = re.findall(alt_pattern, content)
        
        # 查找班级名称
        class_name_pattern = r'([\d]{4}级[^<>\n\r]{2,10})'
        names = re.findall(class_name_pattern, content)
        
        # 如果没有找到班级名称，尝试其他模式
        if not names:
            # 查找类似 "2024级研究生" 的模式
            alt_name_pattern = r'(\d{4}级[^<>\n\r]{3,15})'
            names = re.findall(alt_name_pattern, content)
        
        # 查找班级链接，提取课程ID
        class_links = re.findall(r'https://bjmf\.k8n\.cn/student/course/(\d+)', content)
        
        # 如果没有找到班级链接，尝试其他模式
        if not class_links:
            # 查找相对链接模式
            relative_links = re.findall(r'href=[\'"]/student/course/(\d+)[\'"]', content)
            if relative_links:
                class_links = relative_links
        
        # 组织班级信息
        classes = []
        if codes or names or class_links:
            # 如果找到了班级码、班级名称或班级链接
            max_len = max(len(codes), len(names), len(class_links), 1)
            for i in range(max_len):
                code = codes[i] if i < len(codes) else "未知"
                name = names[i] if i < len(names) else "未知"
                course_id = class_links[i] if i < len(class_links) else "未知"
                classes.append({
                    "class_code": code,
                    "class_name": name,
                    "course_id": course_id
                })
        else:
            # 尝试其他方式查找班级信息
            general_pattern = r'([^<>]{2,15}(?:班|班级|级)[^<>]{0,10})'
            general_matches = re.findall(general_pattern, content)
            for match in general_matches[:3]:  # 取前3个匹配项
                classes.append({
                    "class_code": "未知",
                    "class_name": match.strip(),
                    "course_id": "未知"
                })
        
        return classes
            
    except requests.exceptions.RequestException as e:
        return []

def main(use_test_file=False, test_file_name='data_test.json'):
    print("使用Cookie登录并获取用户信息和班级信息")
    print("=" * 60)
    
    students = load_students_data(use_test_file, test_file_name)
    if not students:
        print(" 未找到学生数据")
        return
    
    print(f" 共找到 {len(students)} 个学生配置")
    
    # 添加调试信息，打印所有学生名字
    print(" 所有学生名单:")
    for i, student in enumerate(students):
        print(f"   {i+1}. {student.get('name', 'Unknown')}")
    
    # 收集所有需要更新的学生信息
    updates = []
    
    # 处理所有学生
    print(f"\n开始处理学生列表，共 {len(students)} 个学生")
    for i, student in enumerate(students):
        print(f"\n--- 处理学生列表索引 {i} ---")
        print(f" 当前学生数据: {student}")
        student_name = student.get('name', 'Unknown')
        print(f"--- 开始处理学生 {student_name} (索引: {i}) ---")
        print(f"  学生姓名: {student_name}")
        print(f"  学生索引: {i}")
        
        # 检查是否是特定学生
        # 已移除对chenhao的特殊处理，所有学生执行相同流程
        
        # 检查学生数据是否完整
        if not student.get('name') or not student.get('cookie'):
            print(f" 学生 {student_name} 数据不完整，跳过处理")
            print(f"--- 学生 {student_name} 处理完成 ---")
            continue
        else:
            print(f" 学生 {student_name} 数据完整，继续处理")
            print(f"  姓名: {student.get('name')}")
            print(f"  Cookie长度: {len(student.get('cookie', ''))}")
            
        headers, student_info = login_and_get_user_info(student)
        
        if headers and student_info:
            print(f" 学生 {student_name} 登录成功")
            # 获取用户个人信息
            user_profile = get_user_profile(headers)
            
            # 检查是否成功获取用户信息
            if not user_profile:
                print(f" 无法获取学生 {student_name} 的用户信息")
                print(" cookie已过期，请重新获取/请检查cookie是否正确")
                print(f"--- 学生 {student_name} 处理完成 ---")
                continue
            
            # 获取班级信息
            class_info = get_class_info(headers)
            
            # 检查data.json中的班级信息，如果为空则记录需要更新
            current_class = student.get('class', '')
            if not current_class or current_class == "":
                print(f"\n 检测到学生 {student_name} 的班级信息为空，尝试自动获取...")
                # 从班级信息中获取第一个课程ID
                course_id = "未知"
                if class_info and len(class_info) > 0:
                    course_id = class_info[0].get('course_id', '未知')
                
                if course_id != "未知":
                    # 记录需要更新的学生信息
                    updates.append((student_name, course_id))
                    print(f" 准备更新学生 {student_name} 的班级信息为: {course_id}")
                else:
                    print(" 未能获取到有效的班级代号，无法更新data.json")
            else:
                print(f"\n 学生 {student_name} 的班级信息已存在: {current_class}")
            
            # 输出完整信息（只对第一个学生输出详细信息，避免重复输出）
            if i == 0:
                print("\n" + "=" * 60)
                print(" 最终结果:")
                if user_profile:
                    print(f" 用户姓名: {user_profile['name']}")
                    print(f" 用户学号: {user_profile['student_id']}")
                else:
                    print(" 未能获取用户信息")
                
                if class_info:
                    print("\n 班级信息:")
                    for i, cls in enumerate(class_info):
                        print(f"   {i+1}. 班级码: {cls['class_code']}")
                        print(f"      班级名称: {cls['class_name']}")
                        if cls.get('course_id') and cls['course_id'] != "未知":
                            print(f"      班级代号: {cls['course_id']}")
                print("=" * 60)
        else:
            print(f"\n 学生 {student_name} 登录失败")
            print(" cookie已过期，请重新获取/请检查cookie是否正确")
        print(f"--- 学生 {student_name} 处理完成 ---")
    
    # 批量更新所有需要更新的学生信息
    if updates:
        print(f"\n 开始批量更新 {len(updates)} 个学生的班级信息...")
        for student_name, course_id in updates:
            print(f" 更新学生 {student_name} 的班级信息为: {course_id}")
            update_data_json(student_name, course_id, use_test_file, test_file_name)
    
    print("\n程序执行完成")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='获取用户信息和班级信息')
    parser.add_argument('--test', action='store_true', help='使用测试文件')
    parser.add_argument('--test-file', type=str, default='data_test.json', help='指定测试文件名，默认为data_test.json')
    
    args = parser.parse_args()
    
    main(use_test_file=args.test, test_file_name=args.test_file)