import json
import sys
import time
import os
from tool.sign_task import Task

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
        
        # 验证学生数据
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

if __name__ == "__main__":
    try:
        students = load_students_data()
        if not students:
            print("没有有效的学生数据，程序退出")
            sys.exit(1)
            
        # 遍历所有学生，进行签到
        for student in students:
            Task(student)
            print("-----------------------------------------------")
    except KeyboardInterrupt:
        print("程序被手动中断")
    except Exception as e:
        print(f"程序运行时发生未预期的错误: {e}")
    finally:
        print("程序执行完毕，自动退出")
        time.sleep(3)  # 减少等待时间
        sys.exit(0)