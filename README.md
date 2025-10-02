# Qwen-2api (通义千问高性能API代理) 🚀

<p align="center">
  <a href="https://github.com/lzA6/Qwen-2api/blob/main/LICENSE"><img src="https://img.shields.io/github/license/lzA6/Qwen-2api?color=blue" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Framework-FastAPI-green.svg" alt="Framework">
  <img src="https://img.shields.io/badge/Proxy-Nginx-purple.svg" alt="Proxy">
  <img src="https://img.shields.io/badge/Deployment-Docker-blueviolet.svg" alt="Deployment">
</p>

这是一个企业级的、高性能的通义千问网页版API代理服务。它不仅将API封装成与OpenAI格式兼容的标准接口，还通过**Nginx粘性会话**、**多账号轮询**和**模型策略路由**等高级功能，提供了极致的稳定性和灵活性。

## ✨ 核心特性

-   **🚀 企业级架构**: 采用 **Nginx + FastAPI** 的生产级架构，Nginx负责负载均衡与会话保持，FastAPI负责核心AI逻辑，性能卓越。
-   **🎯 终极粘性会话**: 利用 Nginx 对 `Authorization` 头进行哈希，100%确保同一用户的连续请求命中同一后台实例，从根本上解决流式对话内容重复与错乱问题。
-   **🔑 多账号支持**: 可配置多个国内站账号，并通过策略路由将特定模型的请求（如`Qwen3-Max-Preview`）定向到专属账号。
-   **🌍 全功能覆盖**: 支持文本、视觉、以及国际站的图像和视频生成模型。
-   **🔒 令牌认证**: 内置 `API_MASTER_KEY` 认证，保护您的API服务不被滥用。
-   **🐳 一键部署**: 提供标准的 Docker Compose 配置，无论是本地还是服务器，都能轻松启动。

---

## 🏗️ 架构原理解析

本项目采用双容器微服务架构，以实现性能与稳定性的最大化。

```
[用户/客户端] ---> [🌐 Nginx (总机)] ---> [🤖 Python FastAPI (工人)] ---> [☁️ 通义千问官网]
```

1.  **Nginx (总机)**: 作为API网关，负责处理所有外部流量、实现基于`API_KEY`的粘性会话，并将请求安全地转发给后台的Python服务。
2.  **Python FastAPI (工人)**: 负责处理核心业务逻辑，包括：验证API密钥、根据模型选择合适的通义千问账号、以及将官网的累积式数据流实时转换为标准的增量流。

---

## 🚀 快速开始 (本地部署)

通过 Docker，只需几步即可在您的电脑上拥有一个私有的、高性能的API服务。

### 前提条件

-   已安装 [**Docker**](https://www.docker.com/products/docker-desktop/) 和 **Docker Compose**。
-   已安装 [**Git**](https://git-scm.com/)。

### 第 1 步：获取项目代码

打开您的命令行（终端），克隆本项目到您的电脑上。

```bash
git clone https://github.com/lzA6/Qwen-2api.git
cd Qwen-2api
```

### 第 2 步：获取核心认证信息

本项目通过模拟网页版请求实现，因此需要您提供一次性的个人认证信息。

1.  使用您的浏览器登录 **[通义千问官网](https://tongyi.aliyun.com/chat)**。
2.  按 `F12` 打开开发者工具，并切换到 **网络 (Network)** 面板。
3.  随便发送一条消息，在网络请求列表中找到一个名为 `completions` 的请求。
4.  点击该请求，在右侧的 **标头 (Headers)** 选项卡中，向下滚动到 **请求标头 (Request Headers)** 部分。
5.  **仔细、完整地**找到并复制以下两项的值：
    -   `cookie`
    -   `x-xsrf-token`

> **💡 提示**: 如果您需要使用多账号或国际站功能，请用同样的方法获取并保存对应账号的认证信息。

### 第 3 步：配置您的项目

这是最关键的一步，您需要将您的私人信息配置到项目中。

1.  在 `Qwen-2api` 文件夹中，找到名为 `.env.example` 的文件。
2.  **将它复制并重命名为 `.env`**。
3.  用文本编辑器打开这个新的 `.env` 文件，将您在**第 2 步**中获取到的信息，以及您自定义的API密钥，填写到对应的位置。

**一个最简化的 `.env` 配置示例：**
```env
# .env (最简配置示例)

# 服务监听端口 (Nginx将监听此端口)
LISTEN_PORT=8082

# 设置一个复杂的主密钥，用于保护你的API
API_MASTER_KEY=your_super_secret_master_key_123

# 留空即可，表示所有模型都走账号1
MODEL_TO_ACCOUNT_MAP='{}'

# --- 国内站账号 1 (默认账号) ---
CN_ACCOUNT_1_COOKIE="在这里粘贴你的Cookie"
CN_ACCOUNT_1_XSRF_TOKEN="在这里粘贴你的XSRF-Token"

# --- 国内站账号 2 (如果你只有一个账号，请将这里也设置成和账号1一样) ---
CN_ACCOUNT_2_COOKIE="在这里粘贴你的Cookie"
CN_ACCOUNT_2_XSRF_TOKEN="在这里粘贴你的XSRF-Token"

# ... 其他国际站配置 ...
```

### 第 4 步：创建共享网络 (仅首次需要)

由于本项目采用多容器架构，需要创建一个共享网络让它们互相通信。

```bash
docker network create shared_network
```

### 第 5 步：启动服务！

回到您的命令行（确保当前仍在 `Qwen-2api` 文件夹内），运行以下命令：

```bash
docker compose up -d --build
```
Docker 将会自动构建镜像并在后台启动Nginx和Python服务。

### 第 6 步：测试您的本地API

打开另一个命令行窗口，使用 `curl` 命令来测试：

```bash
curl http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_super_secret_master_key_123" \
  -d '{
    "model": "qwen-plus",
    "messages": [{"role": "user", "content": "你好，请介绍一下你自己！"}]
  }'
```
**注意：** 请将 `your_super_secret_master_key_123` 替换为您在 `.env` 文件中设置的 `API_MASTER_KEY`。

如果成功返回了通义千问的回答，恭喜您，本地部署成功！

---

## ☁️ 部署到 Hugging Face (实验性)

Hugging Face Spaces 的免费实例目前**不支持** Docker Compose 多容器部署。因此，如需部署到HF，需要采用**简化的单容器架构**。

> **注意**: 这意味着您将失去Nginx带来的粘性会话和性能优势，但这对于轻量级使用或公开演示仍然是一个很好的选择。

详细步骤请参考[此文档](https://huggingface.co/docs/spaces/containers)进行单容器Dockerfile部署，并确保在`README.md`头部添加`sdk: docker`和`app_port: 8082`的元数据。

---

## 📖 API 参考

### 获取模型列表

-   **Endpoint**: `GET /v1/models`
-   **认证**: `Bearer <API_MASTER_KEY>`
-   **响应**: 返回一个兼容OpenAI格式的可用模型列表。

### 创建聊天补全

-   **Endpoint**: `POST /v1/chat/completions`
-   **认证**: `Bearer <API_MASTER_KEY>`
-   **请求体**:
    ```json
    {
      "model": "qwen-plus",
      "messages": [{"role": "user", "content": "你好！"}],
      "stream": true
    }
    ```
-   **响应**: 返回一个标准的SSE（Server-Sent Events）流或一个JSON对象。

---

## ❓ 常见问题 (FAQ)

-   **Q: 为什么需要 `docker network create`？**
    A: 因为本项目包含 `nginx` 和 `qwen-local` 两个服务，它们需要在同一个虚拟网络中才能互相通信。这是一个标准的Docker微服务实践。

-   **Q: 部署后访问API提示 `403 Forbidden`？**
    A: 这是因为您的 `API_MASTER_KEY` 配置正确，但您的请求头 `Authorization: Bearer ...` 中的密钥不正确或缺失。请检查您的密钥。

-   **Q: 我的认证信息会过期吗？**
    A: 会的。网页版的认证信息通常有较长的有效期（数周甚至数月），但不是永久的。如果服务开始报错，您可能需要重复**第 2 步**来获取新的认证信息并更新您的 `.env` 文件，然后重启服务 (`docker compose up -d --build`)。

## 📜 License

本项目采用 [Apache License 2.0](LICENSE) 开源。
