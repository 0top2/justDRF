# 1. 基础镜像
FROM python:3.10-slim

# 2. 设置工作目录
WORKDIR /app

# =========== 【关键修改】开始 ===========
# 这一步就是告诉 Linux：别去国外下载了，去阿里云下载！
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# 现在再去安装依赖，速度会飞快
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
# =========== 【关键修改】结束 ===========

# 3. 复制依赖清单并安装
COPY requirements.txt .
# 注意：这里 pip 也加了阿里云镜像加速
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 4. 复制代码
COPY . .

# 5. 启动命令
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]