import re
import requests
from bs4 import BeautifulSoup
from tool.time_utils import get_current_time
from tool.message_sender import sendQQmessage, wx_send

# 设置请求超时时间
REQUEST_TIMEOUT = 10

# 签到任务
def Task(student):
    try:
        # 验证学生数据
        required_fields = ['name', 'class', 'lat', 'lng', 'acc', 'cookie']
        for field in required_fields:
            if field not in student or not student[field]:
                print(f"错误: 学生配置缺少必要字段 '{field}' 或字段为空")
                return
                
        current_time = get_current_time()  # 获取当前时间
        print(f"当前时间: {current_time}")
        
        name = student['name']
        ClassID = student['class']
        lat = student['lat']
        lng = student['lng']
        ACC = student['acc']
        
        # 安全地提取cookie
        try:
            Cookie_rs_match = re.search(r'remember_student_59ba36addc2b2f9401580f014c7f58ea4e30989d=[^;]+',
                                       student['cookie'])
            if not Cookie_rs_match:
                print(f"错误: {name} 的cookie格式不正确，未找到有效的认证信息")
                return
            Cookie_rs = Cookie_rs_match.group(0)  # 提取cookie
        except Exception as e:
            print(f"错误: {name} 的cookie解析失败: {e}")
            return
            
        print(f"当前任务：{name},{ClassID},{lat},{lng},{ACC}")
        QmsgKEY = student.get('QmsgKEY', '')
        WXKey = student.get('WXKey', '')
        
        url = f'http://g8n.cn/student/course/{ClassID}/punchs'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; X64; Linux; Android 9;) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Firefox/92.0  WeChat/x86_64 Weixin NetType/4G Language/zh_CN ABI/x86_64',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/wxpic,image/tpg,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Referer': f'http://g8n.cn/student/course/{ClassID}',
            'Cookie': Cookie_rs
        }

        # 发送GET请求获取签到页面
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            print(f"进入_{name}_账号界面响应: {response.status_code}")
            
            if response.status_code != 200:
                print(f"错误: 获取 {name} 签到页面失败，状态码: {response.status_code}")
                return
        except requests.exceptions.Timeout:
            print(f"错误: 获取 {name} 签到页面超时")
            return
        except requests.exceptions.RequestException as e:
            print(f"错误: 获取 {name} 签到页面时发生网络异常: {e}")
            return

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

            # 发送签到请求
            try:
                response = requests.post(url1, headers=headers, data=payload, timeout=REQUEST_TIMEOUT)
            except requests.exceptions.Timeout:
                print(f"错误: {name} 签到请求超时")
                continue
            except requests.exceptions.RequestException as e:
                print(f"错误: {name} 签到时发生网络异常: {e}")
                continue

            if response.status_code == 200:
                print("请求成功")
                try:
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
                            # 发送通知消息
                            if QmsgKEY:
                                try:
                                    if sendQQmessage(QmsgKEY):
                                        print("存在QmsgKEY，消息发送成功")
                                    else:
                                        print("存在QmsgKEY，但消息发送失败")
                                except Exception as e:
                                    print(f"发送QQ消息时发生异常: {e}")
                            else:
                                print("QmsgKEY为空，未发送消息")

                            if WXKey:
                                try:
                                    if wx_send(WXKey):
                                        print("存在WXServerKey，消息发送成功")
                                    else:
                                        print("存在WXServerKey，但消息发送失败")
                                except Exception as e:
                                    print(f"发送微信消息时发生异常: {e}")
                            else:
                                print("WXServerKey为空，未发送消息")
                    else:
                        print("页面结构异常，未找到标题信息")
                except Exception as e:
                    print(f"解析响应页面时发生错误: {e}")
            else:
                print(f"请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"发生未预期的错误{e}，跳过该配置......")