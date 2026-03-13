# 基础镜像（用Python 3.13 slim版，体积小、稳定）
FROM python:3.13-slim  

# 切换到容器内的 /app 目录作为工作目录
WORKDIR /app

# 把你电脑上的所有项目文件（包括app_complete.py、requirements.txt等）复制到容器的 /app 目录
COPY . .

# 在容器里安装 Python 依赖（从requirements.txt读取）
RUN pip install --no-cache-dir -r requirements.txt

# 声明容器会暴露 8000 端口（和你Flask代码里的端口保持一致）
EXPOSE 5000

# 容器启动时执行的命令：运行你的主程序 app_complete.py
CMD ["python3", "app_complete.py"]