FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制应用文件
COPY app.py .
COPY index.html .

# 创建数据目录
RUN mkdir -p /data/待整理 /data/电影 /data/剧集

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 暴露端口
EXPOSE 8090

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8090')" || exit 1

# 启动应用
CMD ["python3", "app.py"]
