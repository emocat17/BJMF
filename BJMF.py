import sys
import time
import os
from utils import (
    load_config, 
    save_config, 
    get_students,
    get_user_and_class_info,
    sendQQmessage,
    wx_send,
    send_summary_notification,
    Task
)

#设置代理；网络连接错误时尝试
# proxies = {
#     "http": "http://127.0.0.1:7890",
#     "https": "http://127.0.0.1:7890"
# }

if __name__ == "__main__":
    try:
        # 获取脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建data.json的绝对路径
        config_path = os.path.join(script_dir, 'data.json')
        
        # 遍历所有学生，进行签到
        # 先读取原始配置文件用于更新
        original_config = load_config(config_path)
        students = original_config.get('students', [])
        
        # 收集所有签到结果
        attendance_results = []
        
        for i, student in enumerate(students):
            # 如果class字段为空，则先获取用户和班级信息来填充
            if not student.get('class') or student['class'].strip() == "":
                print(f"用户 {student['name']} 的class字段为空，正在获取班级信息...")
                user_info, class_info = get_user_and_class_info(student)
                
                # 检查是否成功获取了用户信息，如果没有则跳过该用户
                user_name = user_info.get('name', '未找到')
                if user_name == "未找到":
                    print(f"无法获取用户信息，可能是cookie过期或无效，跳过用户 {student['name']} 的签到任务")
                    attendance_results.append((student['name'], 'skip'))
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
                    attendance_results.append((student['name'], 'skip'))
                    print("===============================================")
                    print("===============================================\n\n\n")
                    continue
            
            # 执行签到任务并收集结果
            result = Task(student)
            if result:
                attendance_results.append(result)
            print("===============================================")
            print("===============================================\n\n\n")
        
        # 保存更新后的配置到文件
        save_config(original_config, config_path)
        
        # 发送汇总通知
        wx_key = original_config.get('WXKey', '')
        if wx_key and wx_key.strip():
            send_summary_notification(wx_key, attendance_results)
        else:
            print("未配置WXKey，跳过汇总通知")
    except KeyboardInterrupt:
        print("程序被手动中断")
    finally:
        print("程序执行完毕，自动退出")
        time.sleep(3)
        sys.exit(0)
