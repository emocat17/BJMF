# BJMF 自动签到 Backup

- Thanks To [JasonYANG170/AutoCheckBJMF](https://github.com/JasonYANG170/AutoCheckBJMF)
- 仅根据自己学校的班级魔方需求更改简化代码，仅保留GPS自动签到+QQ/WX通知签到情况，其他功能请到项目[AutoCheckBJMF](https://github.com/JasonYANG170/AutoCheckBJMF)项目查看其他内容
- 可配置多人签到
## 功能

- 自动从指定课程中获取签到项
- 通过模拟表单提交，实现自动签到
- 签到成功后，发送消息通知（通过 Qmsg 服务,选配,可以不用配置）

## 安装依赖

在使用该脚本之前，请确保安装以下依赖项：
```bash
    pip install -r requirements.txt
```


## 配置

该脚本需要读取一个名为 `data.json` 的文件，其中包含必要的配置信息。请参考以下格式配置 `data.json` 文件：
```json
{
    "class": "xxxxxx",
    "lat": "xxxxxx",
    "lng": "xxxxxx",
    "acc": "xxxxxx",
    "cookie": "your_cookie",
    "QmsgKEY": "your_Qmsg_key",
    "WXKey": "your_WX_key"
}
```
- 只需要配置json文件即可;
- py文件可根据实际需求更改

### 参数说明:

- `class` - BJMF里的课程 `ID`
- `lat` - 纬度
- `lng` - 经度
- `acc` - 海拔高度
- `cookie` - 从浏览器中获取的 `cookie` 信息，用于模拟登录状态
- `QmsgKEY` - Qmsg 服务的消息推送密钥，用于QQ发送消息(选填)
- `WXKey` - Server酱-Turbo版,用于微信通知消息(选填)

### 参数获取方法
- `class` - 使用抓包工具(比如`HttpCanary`,教程[点击这里](https://blog.csdn.net/weixin_53891182/article/details/124739048) ); 抓取一次签到过程,在过滤(Url关键词或者其他)界面中查找`g8n`
  - (具体视实际情况而定,我的是`g8n`,之后应该只有一条POST请求,为`https://g8n.cn/student/punchs/course/xxxxxx/yyyyyy`, 其中的`xxxxxx`就是六位数的课程ID,`yyyyyy`就是具体的签到任务,这里不用管yyyyyy,代码中会自动获取)
- `lat` 和 `lng` - 使用地图工具获取当前位置的经纬度,
  - 比如[高德地图的坐标拾取器](https://lbs.amap.com/tools/picker), 进去搜索自己的位置即可获取经纬度
- `acc` - 海拔高度
  - 随便写个数字即可, 这里不用管
- `cookie` - 从浏览器中获取的 `cookie` 信息，用于模拟登录状态
  - 同样使用抓包工具获取 
- `QmsgKEY` - Qmsg 服务的消息推送密钥，用于发送QQ成功签到通知
  - Qmsg 官网注册账号即可获取 `https://qmsg.zendee.cn/`, 教程在官网自行查询
- `WXKey` - Server酱-Turbo版 服务的消息推送密钥，用于发送微信成功签到通知
  - Server酱-Turbo版 官网微信扫码关注公众号获取 `https://sct.ftqq.com/`, 教程在官网自行查询

### 抓包软件使用方法
- 签到前打开抓包工具
- 进入VX进行签到
- 返回到抓包工具, 过滤(Url关键词或者其他)界面中查找`g8n`找到Post请求, 复制其中的`cookie`和`classID`
- 更详细方法请自行搜索
- 电脑打开微信也可以在网址栏查看`class ID`,F12可以查看发送请求的`Cookie`(目前只看到了`classID`,`Cookie`可以尝试`F12`->`网络`中进行`POST`包的过滤查找,目前未尝试)
- 更详细的使用和安装方法:[点击链接](https://blog.csdn.net/weixin_53891182/article/details/124739048)
<img src="doc/img1.jpg" alt="抓包界面" style="width: 50%; height: auto;">

### 使用方法

- 配置 `data.json` 文件，确保填入正确的课程信息和其他配置项
- 运行脚本 `BJMF.py`：

```bash
python BJMF.py
```

脚本将自动完成签到操作，并在成功签到后发送通知(如果有配置 Qmsg 服务的话)。

### 自动方法:
- 使用一台常年不关的电脑或者服务器设置定时任务即可自动签到
  - windows 系统: 使用计划任务设置定时任务 [教程](https://blog.csdn.net/weixin_38792396/article/details/121490505)
    - 此电脑(右键)->管理->系统工具->任务计划程序->任务计划程序库
  - linux 系统: 使用 `crontab` 设置定时任务 [教程](https://geek-docs.com/python/python-ask-answer/815_python_execute_python_script_via_crontab.html)
  - 或者使用云服务定时任务, 比如腾讯云函数, 阿里云函数计算, 百度云函数计算等 教程自行搜索

### 未来打算
- 多人签到(√)
- 一检测到新任务就签到(×)
- 画饼:
  - 打包成 `exe` , 供电脑上没有安装`python`环境的电脑签到(×)
  - 打包成 `app` , 供手机上使用自动任务完成签到(×)
