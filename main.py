import json
import sys
import time
from tool.sign_task import Task

# 读取外部 JSON 文件中的数据
with open('data.json', 'r') as file:
    json_data = json.load(file)
    students = json_data['students']  # 获取所有学生的数据

if __name__ == "__main__":
    try:
        # 遍历所有学生，进行签到
        for student in students:
            Task(student)
            print("-----------------------------------------------")
    except KeyboardInterrupt:
        print("程序被手动中断")
    finally:
        print("程序执行完毕，自动退出")
        time.sleep(10)
        sys.exit(0)