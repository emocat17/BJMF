import datetime

# 获取当前时间
def get_current_time():
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")