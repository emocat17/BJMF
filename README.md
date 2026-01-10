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

- 2025.10.14 v2版本
  - 调整文件结构

- 2025.9.14 v2版本
  - 班级码自动获取
  - 输出用户相关信息用于核对

## 安装依赖

在使用该脚本之前，请确保安装以下依赖项：
```bash
pip install -r requirements.txt
```

## 配置

### 1. 基础配置 (data.json)

该脚本主要读取 `data.json` 文件中的配置信息。
**推荐使用 `auto_add_user.py` 自动生成**，生成后格式如下：

```json
{
    "students": [
        {
            "name": "xxx",
            "class": "xxxxxx",
            "lat": "xxxxxx",
            "lng": "xxxxxx",
            "acc": "xxx",
            "cookie": "xxxx",
            "QmsgKEY": "",
            "WXKey": ""
        }
    ]
}
```

### 2. 公共参数配置 (.env) [推荐]

为了方便批量添加用户，项目支持使用 `.env` 文件配置公共参数。
在项目根目录下创建 `.env` 文件并写入以下内容：

```properties
# 是否启用公共配置 (True/False)
ENABLE_COMMON_CONFIG=True

# 公共配置参数 (启用后，auto_add_user.py 添加新用户时将默认使用这些值)
COMMON_LAT=xxxxxx
COMMON_LNG=xxxxxx
COMMON_ACC=30
COMMON_QMSG_KEY=
COMMON_WX_KEY=
```

启用后，运行 `auto_add_user.py` 添加新用户时，会自动填充上述公共参数，无需每次手动编辑 `data.json`。

### 参数说明

- `name`: 用户备注名
- `class`: 课程ID (自动获取)
- `lat`: 纬度 (使用地图工具获取，如[高德地图坐标拾取器](https://lbs.amap.com/tools/picker))
- `lng`: 经度
- `acc`: 精度/海拔 (默认30即可)
- `cookie`: 用户凭证 (自动获取)
- `QmsgKEY`: Qmsg酱推送Key (选填)
- `WXKey`: Server酱推送Key (选填)

## 使用方法

### 自动添加用户

1. 确保已安装依赖。
2. (可选) 配置 `.env` 文件中的公共参数（如经纬度）。
3. 运行自动添加用户工具：
   ```bash
   python auto_add_user.py
   ```
4. 使用微信扫描弹出的二维码进行登录。
5. 程序会自动获取用户信息、班级信息，并结合 `.env` 中的配置写入 `data.json`。

### 执行签到任务

1. 确保 `data.json` 已配置好。
2. 运行签到程序：
   ```bash
   python BJMF.py
   ```
3. 程序会自动遍历配置文件中的所有用户执行签到任务。

### 自动化运行

- **Windows**: 使用"任务计划程序"设置定时任务 [教程](https://blog.csdn.net/weixin_38792396/article/details/121490505)
- **Linux**: 使用 `crontab` 设置定时任务 [教程](https://geek-docs.com/python/python-ask-answer/815_python_execute_python_script_via_crontab.html)
- **云函数**: 可部署至腾讯云/阿里云函数计算 (需自行研究配置)

## 注意事项

- 程序会自动检测并填充空的 class 字段。
- 只有在 `.env` 中设置 `ENABLE_COMMON_CONFIG=True` 时，公共参数才会生效。
- 签到二维码/Cookie 具有时效性，如果签到失败请尝试重新扫码更新 Cookie。
