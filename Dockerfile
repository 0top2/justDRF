# 1. 找一个装好 Python 3.10 的基础镜像
FROM python:3.10-slim

# 2. 设置容器内的工作目录
WORKDIR /app

# 3. 把打包清单复制进去，并安装依赖
# (为了安装 mysqlclient，可能需要先安装系统级依赖)
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 把当前目录下的所有代码复制到容器里
COPY . .

# 5. 告诉容器，启动时执行什么命令
# 这里我们用 gunicorn 启动，监听 8000 端口
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]