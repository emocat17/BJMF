import sys
import time
from utils import (
    load_config, 
    save_config, 
    get_students,
    get_user_and_class_info,
    sendQQmessage,
    wx_send,
    Task
)

#设置代理；用于Qmsg访问,网络连接错误时尝试
# proxies = {
#     "http": "http://127.0.0.1:7890",
#     "https": "http://127.0.0.1:7890"
# }

if __name__ == "__main__":
    try:
        # 遍历所有学生，进行签到
        # 先读取原始配置文件用于更新
        original_config = load_config('data.json')
        students = original_config.get('students', [])
        
        for i, student in enumerate(students):
            # 如果class字段为空，则先获取用户和班级信息来填充
            if not student.get('class') or student['class'].strip() == "":
                print(f"用户 {student['name']} 的class字段为空，正在获取班级信息...")
                user_info, class_info = get_user_and_class_info(student)
                
                # 检查是否成功获取了用户信息，如果没有则跳过该用户
                user_name = user_info.get('name', '未找到')
                if user_name == "未找到":
                    print(f"无法获取用户信息，可能是cookie过期或无效，跳过用户 {student['name']} 的签到任务")
                    print("===============================================")
                    print("===============================================\n\n\n")
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
                    print("===============================================")
                    print("===============================================\n\n\n")
                    continue
            
            Task(student)
            print("===============================================")
            print("===============================================\n\n\n")
        
        # 保存更新后的配置到文件
        save_config(original_config, 'data.json')
    except KeyboardInterrupt:
        print("程序被手动中断")
    finally:
        print("程序执行完毕，自动退出")
        time.sleep(3)
        sys.exit(0)
