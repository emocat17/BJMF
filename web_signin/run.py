import json
import os

from app import create_app


def _load_port_from_config() -> int:
    """
    从配置文件 / 环境变量中加载端口号。

    优先级：
    1. 环境变量 WEB_SIGNIN_PORT
    2. 当前目录下的 config.json 中的 "port"
    3. 默认 8000
    """
    # 默认端口改为 9988，与 Docker 中暴露的端口保持一致
    default_port = 9988

    # 1. 环境变量优先，便于 Docker / 部署平台覆盖
    env_port = os.getenv("WEB_SIGNIN_PORT")
    if env_port:
        try:
            port = int(env_port)
            if 1 <= port <= 65535:
                return port
        except ValueError:
            pass

    # 2. 读取配置文件（与本文件同目录下的 config.json）
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            port = int(data.get("port", default_port))
            if 1 <= port <= 65535:
                return port
        except Exception:
            # 配置解析失败时回退到默认端口
            pass

    return default_port


app = create_app()


if __name__ == "__main__":
    # 运行时根据配置文件 / 环境变量决定端口
    port = _load_port_from_config()
    app.run(host="0.0.0.0", port=port, debug=False)
