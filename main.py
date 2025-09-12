import json
import sys
import time
import os
import subprocess
import sysconfig
from tool.sign_task import Task
from tool.cookie_validator import validate_cookie
from tool.time_utils import get_current_time
from tool.get_info import get_user_profile, get_class_info, extract_remember_cookie

def load_students_data():
    """加载学生数据，增强异常处理"""
    try:
        # 检查文件是否存在
        if not os.path.exists('data.json'):
            print("错误: data.json 文件不存在，请创建该文件或复制 data.json.example 为 data.json")
            return []
        
        # 读取外部 JSON 文件中的数据
        with open('data.json', 'r', encoding='utf-8') as file:
            json_data = json.load(file)
            
        # 检查数据格式
        if 'students' not in json_data:
            print("错误: data.json 文件格式不正确，缺少 'students' 字段")
            return []
            
        students = json_data['students']  # 获取所有学生的数据
        
        # 验证学生数据（不自动获取班级信息）
        for i, student in enumerate(students):
            required_fields = ['name', 'class', 'lat', 'lng', 'acc', 'cookie']
            for field in required_fields:
                if field not in student:
                    print(f"警告: 第{i+1}个学生配置缺少 '{field}' 字段")
        
        return students
    except json.JSONDecodeError as e:
        print(f"错误: data.json 文件格式不正确，JSON 解析失败: {e}")
        return []
    except Exception as e:
        print(f"错误: 读取 data.json 文件时发生异常: {e}")
        return []

def load_students_data_and_update_class_info():
    """加载学生数据并自动获取班级信息"""
    try:
        # 检查文件是否存在
        if not os.path.exists('data.json'):
            print("错误: data.json 文件不存在，请创建该文件或复制 data.json.example 为 data.json")
            return []
        
        # 读取外部 JSON 文件中的数据
        with open('data.json', 'r', encoding='utf-8') as file:
            json_data = json.load(file)
            
        # 检查数据格式
        if 'students' not in json_data:
            print("错误: data.json 文件格式不正确，缺少 'students' 字段")
            return []
            
        students = json_data['students']  # 获取所有学生的数据
        
        # 验证学生数据并自动获取班级信息
        for i, student in enumerate(students):
            required_fields = ['name', 'class', 'lat', 'lng', 'acc', 'cookie']
            for field in required_fields:
                if field not in student:
                    print(f"警告: 第{i+1}个学生配置缺少 '{field}' 字段")
            
            # 如果班级信息为空，尝试自动获取
            if 'class' not in student or not student['class']:
                print(f"检测到第{i+1}个学生 {student.get('name', 'Unknown')} 的班级信息为空，尝试自动获取...")
                try:
                    # 调用get_info.py自动获取班级信息
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    get_info_path = os.path.join(script_dir, 'tool', 'get_info.py')
                    
                    # 使用当前Python解释器运行get_info.py
                    python_exe = sys.executable
                    result = subprocess.run([python_exe, get_info_path], 
                                          capture_output=True, text=True, cwd=script_dir)
                    
                    if result.returncode == 0:
                        print("自动获取班级信息成功")
                        # 重新加载更新后的数据
                        with open('data.json', 'r', encoding='utf-8') as file:
                            json_data = json.load(file)
                        students = json_data['students']
                    else:
                        print(f"自动获取班级信息失败: {result.stderr}")
                except Exception as e:
                    print(f"调用自动获取班级信息时发生异常: {e}")
        
        return students
    except json.JSONDecodeError as e:
        print(f"错误: data.json 文件格式不正确，JSON 解析失败: {e}")
        return []
    except Exception as e:
        print(f"错误: 读取 data.json 文件时发生异常: {e}")
        return []

def validate_all_cookies(students):
    """验证所有学生的cookie有效性"""
    print("开始验证所有学生的cookie有效性...")
    all_valid = True
    valid_students = []
    
    for i, student in enumerate(students):
        # 构造请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; X64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Cookie': student.get('cookie', ''),
        }
        
        # 验证cookie是否有效
        is_valid, user_info = validate_cookie(headers)
        
        if is_valid:
            print(f" 学生 {student.get('name', 'Unknown')} 的cookie有效")
            valid_students.append(student)
        else:
            print(f" 学生 {student.get('name', 'Unknown')} 的cookie无效")
            all_valid = False
    
    return all_valid, valid_students

if __name__ == "__main__":
    try:
        # 输出当前时间
        current_time = get_current_time()
        print(f"程序开始执行，当前时间: {current_time}")
        
        # 加载学生数据并自动获取班级信息
        students = load_students_data_and_update_class_info()
        if not students:
            print("没有有效的学生数据，程序退出")
            sys.exit(1)
        
        # 遍历所有学生，进行签到
        for student in students:
            try:
                print("==============")
                
                # 构造请求头
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; X64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                    'Cookie': student.get('cookie', ''),
                }
                
                # 验证cookie是否有效
                is_valid, user_info = validate_cookie(headers)
                
                if is_valid:
                    print("cookie有效性验证：有效")
                    # 输出用户信息
                    print(f" 姓名: {user_info['name']}")
                    print(f" 学号: {user_info['student_id']}")
                    print(f"{user_info['name']}  {user_info['student_id']}")
                        
                    # 获取班级信息
                    class_info = get_class_info(headers) if headers['Cookie'] else []
                    if class_info:
                        # 只显示第一个班级信息
                        cls = class_info[0]
                        class_code = cls.get('class_code', '未知')
                        class_name = cls.get('class_name', '未知')
                        course_id = cls.get('course_id', '未知') if cls.get('course_id') and cls['course_id'] != "未知" else '未知'
                        print(f"{class_code} {class_name}  {course_id}")
                    else:
                        print("未知 未知  未知")
                    
                    # 执行签到任务并捕获输出
                    try:
                        Task(student)
                    except Exception as task_e:
                        print(f"签到任务执行失败: {task_e}")
                else:
                    print("cookie有效性验证：无效")
                    print(f"{student.get('name', 'Unknown')}  未知")
                    print("未知 未知  未知")
                    print()
                    print("未找到在进行的签到/不在签到时间内")
                    
                print("==============")
            except Exception as e:
                print(f"处理学生 {student.get('name', 'Unknown')} 时发生错误: {e}，跳过该用户")
                print("==============")
                continue
                
    except KeyboardInterrupt:
        print("程序被手动中断")
    except Exception as e:
        print(f"程序运行时发生未预期的错误: {e}")
    finally:
        print("程序执行完毕，自动退出")
        time.sleep(3)  # 减少等待时间
        sys.exit(0)