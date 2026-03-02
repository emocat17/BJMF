from app import create_app

app = create_app()

if __name__ == "__main__":
    # 开发模式运行
    app.run(host="0.0.0.0", port=8000, debug=True)

