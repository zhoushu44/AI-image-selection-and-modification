# ============================================
# Dockerfile - AI 图片编辑应用
# 一劳永逸方案：所有依赖都在 requirements.txt 中管理
# ============================================

# 基础镜像（Python 3.13 slim 版，最新稳定版本）
FROM python:3.13-slim  

# 工作目录
WORKDIR /app

# 复制项目文件到容器
COPY . .

# 安装 Python 依赖（一劳永逸：所有依赖都在 requirements.txt 中）
# 包括：flask, requests, pillow, supabase 等
RUN pip install --no-cache-dir -r requirements.txt

# 设置 Flask 生产环境
ENV FLASK_ENV=production

# 暴露 5000 端口
EXPOSE 5000

# 启动应用
CMD ["python3", "app_complete.py"]