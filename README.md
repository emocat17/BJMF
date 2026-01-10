# 班级魔方多人GPS自动签到

- Thanks To [JasonYANG170/AutoCheckBJMF](https://github.com/JasonYANG170/AutoCheckBJMF) ，根据自己学校的签到进行了简化
- 仅根据自己学校的班级魔方需求更改简化代码,仅支持GPS签到(可在范围外)，其他功能请到项目[AutoCheckBJMF](https://github.com/JasonYANG170/AutoCheckBJMF)项目查看其他内容
- 可配置多人签到
- 可配置QQ/WX通知签到情况
- 如果你觉得好用,`Please Star`orz

## 代码结构

项目已进行模块化重构，提高了代码的可维护性和可读性：

```
BJMF/
├── BJMF.py                 # 主程序，负责整体流程控制
├── auto_add_user.py        # 自动添加用户工具，通过微信扫码获取用户信息并写入配置data.json
├── .env                    # (可选) 环境变量配置文件，用于配置公共参数
└── utils/                  # 工具模块目录
    ├── __init__.py         # 模块初始化文件
    ├── config_manager.py   # 配置文件管理模块
    ├── user_info.py        # 用户信息获取模块
    ├── notification.py     # 通知发送模块
    └── attendance.py       # 签到任务执行模块
```

### 各模块职责

- **BJMF.py**: 主程序入口，负责读取配置、遍历用户、调用签到任务
- **auto_add_user.py**: 自动添加用户工具，通过微信扫码获取用户信息并写入data.json配置文件；支持读取.env公共配置
- **config_manager.py**: 处理配置文件的读取和保存
- **user_info.py**: 获取用户信息和班级信息
- **notification.py**: 处理QQ和微信消息发送
- **attendance.py**: 执行签到任务的核心逻辑

## 功能

- 自动从指定课程中获取签到项
- 通过模拟表单提交，实现自动签到
- 签到成功后,发送QQ/WX消息通知(可选配,可以不用配置)
- 支持通过微信扫码快速添加用户
- 支持 `.env` 配置公共参数，简化多人配置

## 更新说明

- 2026.01.10
  - `auto_add_user.py` 优化: 支持通过 `.env` 文件配置公共参数(经纬度、通知Key等)，简化配置流程
  - `auto_add_user.py` 优化: 增加二维码自动清理机制，避免垃圾文件堆积及文件占用问题
  - `utils/attendance.py` 修复: 优化签到状态检测逻辑，增加对"已签到"状态的HTML解析，解决正则匹配失败导致的误报问题

- 2025.12.15
  - 更新 `utils/attendance.py` ,改用 requests.Session()防止获取签到项失败问题；同时增加了对 response.url 的检测

- 2025.12.04 v2版本
  - 新增 `auto_add_user.py` 工具，实现微信扫码自动获取用户信息并写入配置文件data.json
  - 简化了用户添加流程，无需手动获取Cookie和班级ID

## 安装依赖

在使用该脚本之前，请确保安装以下依赖项：
```bash
pip install -r requirements.txt
```

## 配置指南

### 方法一：自动添加用户 (推荐)

最简单的方法，无需手动抓包或查找 Cookie。

1. **(可选) 配置公共参数**：
   在项目根目录下创建 `.env` 文件（可参考下方模板），填入经纬度等公共信息。
   ```properties
   # 是否启用公共配置 (True/False)
   ENABLE_COMMON_CONFIG=True

   # 公共配置参数
   COMMON_LAT=xxxxxx  # 纬度
   COMMON_LNG=xxxxxx  # 经度
   COMMON_ACC=30      # 精度
   COMMON_QMSG_KEY=   # Qmsg推送Key(可选)
   COMMON_WX_KEY=     # Server酱推送Key(可选)
   ```

2. **运行自动工具**：
   ```bash
   python auto_add_user.py
   ```

3. **扫码登录**：
   使用微信扫描弹出的二维码，程序会自动获取 Cookie 和班级信息并保存到 `data.json`。

### 方法二：手动配置 (高级)

如果你需要手动配置 `data.json`，可以按照以下步骤获取参数。

#### 1. data.json 格式
```json
{
    "students": [
        {
            "name": "用户备注",
            "class": "110141",
            "lat": "30.123456",
            "lng": "120.123456",
            "acc": "30",
            "cookie": "从浏览器获取的Cookie字符串",
            "QmsgKEY": "",
            "WXKey": ""
        }
    ]
}
```

#### 2. 参数获取说明

- **Cookie 获取方法 (PC端浏览器)**：
  1. 电脑微信登录并打开签到页面：`http://g8n.cn/student/login?ref=%2Fstudent`
  2. 按 `F12` 打开开发者工具，切换到 **网络 (Network)** 标签。
  3. 刷新页面，在左侧请求列表中找到第一个请求（通常是数字或 student）。
  4. 点击该请求，在右侧 **标头 (Headers)** -> **请求标头 (Request Headers)** 中找到 `Cookie`。
  5. 复制 `Cookie:` 后面的所有内容（通常以 `PHPSESSID=...` 或 `remember_student_...` 开头）。
  
  ![浏览器查看Cookie](doc/img5.jpg)

- **Class (班级ID)**：
  - 在上述浏览器页面的网址栏中，可以看到类似 `course/110141` 的内容，`110141` 即为班级ID。
  - 或者在页面中查看。
  ![浏览器查看班级码](doc/img4.jpg)

- **经纬度 (Lat/Lng)**：
  - 使用 [高德地图坐标拾取器](https://lbs.amap.com/tools/picker) 获取。

- **推送 Key (可选)**：
  - **Qmsg酱**: [官网](https://qmsg.zendee.cn/) 注册获取 Key。
  - **Server酱**: [官网](https://sct.ftqq.com/) 扫码获取 Key。

## 使用方法

1. **配置用户**：使用上述任意一种方法完成用户配置（生成 `data.json`）。
2. **执行签到**：
   ```bash
   python BJMF.py
   ```
3. **自动化运行**：
   - **Windows**: 使用"任务计划程序"设置定时任务。
   - **Linux**: 使用 `crontab` 设置定时任务。
   - **云函数**: 可部署至云函数平台。

## 注意事项

- 程序会自动检测并填充空的 class 字段。
- 签到二维码/Cookie 具有时效性，如果签到失败（提示 Cookie 无效），请重新运行 `auto_add_user.py` 更新凭证。
