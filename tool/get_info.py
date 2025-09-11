import requests
import json
import re
import os

def load_students_data():
    """加载学生数据"""
    try:
        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 构造data.json的绝对路径
        data_file_path = os.path.join(script_dir, '..', 'data.json')
        
        print(f"尝试加载文件: {data_file_path}")
        
        # 由于脚本在tool文件夹中，需要使用相对路径访问上层目录的data.json
        with open(data_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get('students', [])
    except FileNotFoundError:
        print("未找到 data.json 文件")
        return []
    except json.JSONDecodeError as e:
        print(f"data.json 格式错误: {e}")
        return []
    except Exception as e:
        print(f"读取 data.json 时发生错误: {e}")
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
    
    # 提取关键cookie
    remember_cookie = extract_remember_cookie(full_cookie)
    if not remember_cookie:
        print("❌ 未找到 remember_student cookie")
        return None, None
    
    print(f"🔑 使用的关键 Cookie: {remember_cookie}")
    
    # 构造请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; X64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Cookie': remember_cookie,
    }
    
    return headers, student

def get_user_profile(headers):
    """获取用户个人信息"""
    print("\n=== 获取用户个人信息 ===")
    
    # 访问个人页面
    profile_url = "https://bjmf.k8n.cn/student/my"
    print(f"🌐 访问个人页面: {profile_url}")
    
    try:
        response = requests.get(profile_url, headers=headers, timeout=10)
        print(f"📊 个人页面响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 个人页面访问成功，开始提取用户信息...")
            # 提取用户姓名和学号
            content = response.text
            
            # 查找姓名 (从JavaScript变量中提取)
            name_pattern = r'uname[\'"]?\s*:\s*[\'"]([^\'"]+)[\'"]'
            name_match = re.search(name_pattern, content)
            if not name_match:
                # 备用方案：从HTML中查找
                name_match = re.search(r'>([^<>\n\r]{2,4})\s*同学<', content)
                if not name_match:
                    name_match = re.search(r'>(蔡永昊)<', content)  # 特定姓名匹配
            
            name = name_match.group(1).strip() if name_match else "未找到"
            
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
                    student_id = "未找到"
            else:
                student_id = id_match.group(1).strip() if id_match else "未找到"
            
            print(f"👤 姓名: {name}")
            print(f"🆔 学号: {student_id}")
            
            return {
                "name": name,
                "student_id": student_id
            }
        else:
            print(f"❌ 个人页面访问失败，状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 个人页面访问异常: {e}")
        return None

def get_class_info(headers):
    """获取班级信息"""
    print("\n=== 获取班级信息 ===")
    
    # 访问主页
    home_url = "https://bjmf.k8n.cn/student"
    print(f"🌐 访问主页: {home_url}")
    
    try:
        response = requests.get(home_url, headers=headers, timeout=10)
        print(f"📊 主页响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 主页访问成功，开始提取班级信息...")
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
            
            # 组织班级信息
            classes = []
            if codes or names:
                # 如果找到了班级码或班级名称
                max_len = max(len(codes), len(names), 1)
                for i in range(max_len):
                    code = codes[i] if i < len(codes) else "未知"
                    name = names[i] if i < len(names) else "未知"
                    classes.append({
                        "class_code": code,
                        "class_name": name
                    })
            else:
                # 尝试其他方式查找班级信息
                general_pattern = r'([^<>]{2,15}(?:班|班级|级)[^<>]{0,10})'
                general_matches = re.findall(general_pattern, content)
                for match in general_matches[:3]:  # 取前3个匹配项
                    classes.append({
                        "class_code": "未知",
                        "class_name": match.strip()
                    })
            
            if classes:
                print("📋 班级信息:")
                for i, cls in enumerate(classes):
                    print(f"   {i+1}. 班级码: {cls['class_code']}")
                    print(f"      班级名称: {cls['class_name']}")
            else:
                print("⚠️ 未提取到班级信息")
                # 显示部分内容供调试
                print("📄 页面内容预览:")
                print(content[:500])
            
            return classes
        else:
            print(f"❌ 主页访问失败，状态码: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 主页访问异常: {e}")
        return []

def main():
    print("🔍 使用Cookie登录并获取用户信息和班级信息")
    print("=" * 60)
    
    students = load_students_data()
    if not students:
        print("❌ 未找到学生数据")
        return
    
    print(f"📊 共找到 {len(students)} 个学生配置")
    
    # 处理第一个学生
    if students:
        student = students[0]
        headers, student_info = login_and_get_user_info(student)
        
        if headers and student_info:
            # 获取用户个人信息
            user_profile = get_user_profile(headers)
            
            # 获取班级信息
            class_info = get_class_info(headers)
            
            # 输出完整信息
            print("\n" + "=" * 60)
            print("📋 最终结果:")
            if user_profile:
                print(f"👤 用户姓名: {user_profile['name']}")
                print(f"🆔 用户学号: {user_profile['student_id']}")
            
            if class_info:
                print("\n📚 班级信息:")
                for cls in class_info:
                    print(f"   班级码: {cls['class_code']}")
                    print(f"   班级名称: {cls['class_name']}")
            print("=" * 60)
        else:
            print("\n❌ 登录失败")
    
    print("\n程序执行完成")

if __name__ == "__main__":
    main()