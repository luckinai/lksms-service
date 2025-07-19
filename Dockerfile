FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 正确配置Debian 12的镜像源
RUN echo "Types: deb" > /etc/apt/sources.list.d/debian.sources && \
    echo "URIs: https://mirrors.ustc.edu.cn/debian/" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Suites: bookworm bookworm-updates" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Components: main" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg" >> /etc/apt/sources.list.d/debian.sources && \
    echo "" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Types: deb" >> /etc/apt/sources.list.d/debian.sources && \
    echo "URIs: https://mirrors.ustc.edu.cn/debian-security/" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Suites: bookworm-security" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Components: main" >> /etc/apt/sources.list.d/debian.sources && \
    echo "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg" >> /etc/apt/sources.list.d/debian.sources

# 配置pip使用国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip config set global.timeout 300

# 更新包列表并安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 复制并安装Python依赖
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --timeout 300 --retries 5 -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]