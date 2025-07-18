# 使用 Python 3.9 的基础映像
FROM python:3.9-slim

# 安装 ffmpeg，用于音频格式转换
RUN apt-get update && apt-get install -y ffmpeg

# 设置工作目录
WORKDIR /app

# 复制应用程序文件
COPY app.py /app
COPY requirements.txt /app

# 安装 Python 依赖
RUN pip install -r requirements.txt

# 暴露端口
EXPOSE 8080

# 运行应用
CMD ["python", "app.py"]
