import re
import requests
from bs4 import BeautifulSoup
import json
import datetime
import sys


# 获取当前时间
def get_current_time():
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")


# 读取外部 JSON 文件中的数据
with open('data.json', 'r') as file:
    json_data = json.load(file)
    ClassID = json_data['class']
    X = json_data['lat']  # 纬度
    Y = json_data['lng']  # 经度
    ACC = json_data['acc']  # 海拔
    Cookie_rs = re.search(r'remember_student_59ba36addc2b2f9401580f014c7f58ea4e30989d=[^;]+',
                                 json_data['cookie']).group(0)  # json_data['cookie'])中提取信息
    QmsgKEY = json_data['QmsgKEY']  # 获取QmsgKEY


# 发送QQ消息通知
def send_message():
    url = f'https://qmsg.zendee.cn/send/{QmsgKEY}'
    current_time = get_current_time()  # 获取当前时间
    message = {
        "msg": f"{current_time}  签到成功！",
    }
    response = requests.post(url, data=message)
    if response.status_code == 200:
        print("消息发送成功")
    else:
        print(f"消息发送失败，状态码: {response.status_code}")

# 签到任务
def Task():
    current_time = get_current_time()  # 获取当前时间
    print(f"当前时间: {current_time}")
    print(f"进入检索...")

    url = f'http://g8n.cn/student/course/{ClassID}/punchs'  # url根据实际内容更改
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; X64; Linux; Android 9;) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Firefox/92.0  WeChat/x86_64 Weixin NetType/4G Language/zh_CN ABI/x86_64',

        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/wxpic,image/tpg,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',

        'Referer': f'http://g8n.cn/student/course/{ClassID}',

        'Cookie': Cookie_rs
    }


    response = requests.get(url, headers=headers)
    print(f"进入界面响应: {response}")

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
            'lat': X,
            'lng': Y,
            # 'acc': ACC,  # 海拔
            # 'res': '',  # 拍照签到
            # 'gps_addr': ''  # GPS地址为空
        }

        response = requests.post(url1, headers=headers, data=payload)

        if response.status_code == 200:
            print("请求成功")
            soup_response = BeautifulSoup(response.text, 'html.parser')
            # print(soup_response)  # 打印响应内容,以下内容根据实际调整;可以打印出来看看签到成功的表头信息
            title_div = soup_response.find('div', id='title') # 获取响应中的div标签信息,判断是否签到成功

            # 用于判断是否签到成功来发送通知;如果下列逻辑不管用的话直接把下方的if title_div逻辑去掉,保留send_message()即可
            # send_message()

            if title_div:
                title_text = title_div.text.strip()
                # print(title_text)
                if "已签到" in title_text:
                    print("已经签到！")
                else:
                    # 还未签到,则发送消息通知(仅在第一次签到时发送)
                    if QmsgKEY:
                        send_message()
                        print("存在QmsgKEY，已发送消息")
                    else:
                        print("QmsgKEY为空，未发送消息")
        else:
            print(f"请求失败，状态码: {response.status_code}")


if __name__ == "__main__":
    # send_message()  # Just Test
    try:
        Task()
    except KeyboardInterrupt:
        print("程序被手动中断")
    finally:
        print("程序执行完毕，自动退出")
        sys.exit(0)
