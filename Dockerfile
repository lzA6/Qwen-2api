# 使用官方的 Python 3.10 slim 版本作为基础环境
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# ！！！终极修正：使用 COPY . /app 来正确复制整个项目结构！！！
# 这会把你的本地的 app 文件夹、requirements.txt 等，全部复制到容器的 /app 目录下
COPY . /app

# 设置环境变量，告诉 Python 模块的搜索路径
ENV PYTHONPATH=/app

# 安装所有 Python 依赖，使用国内源加速
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 容器启动时要执行的命令
# 这个命令现在非常标准和稳定
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
