# Qwen Multi-Account Local API (v7.2) 🚀

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Framework-FastAPI-green.svg" alt="Framework">
  <img src="https://img.shields.io/badge/Deployment-Docker-blueviolet.svg" alt="Deployment">
  <img src="https://img.shields.io/badge/License-MIT-lightgrey.svg" alt="License">
</p>

这是一个基于 FastAPI 的高性能通义千问本地代理服务。它不仅将网页版API封装成与 OpenAI 格式兼容的标准接口，还支持**多账号轮询**、**模型策略路由**和**密钥认证**等高级功能。

无论您是想在**本地快速运行**，还是希望**免费部署到云端**拥有一个公开网址，本文档都将为您提供终极详细的指导。

## ✨ 核心特性

-   **🔑 多账号支持**: 可配置多个国内站账号，并通过策略路由将特定模型的请求定向到专属账号。
-   **🛡️ 高稳定性**: 基于个人长期有效的认证信息，服务稳定可靠，杜绝因前端更新导致的频繁失效。
-   **🌍 全功能覆盖**: 支持文本、视觉、以及国际站的图像和视频生成模型。
-   **🔒 企业级安全**: 内置 `API_MASTER_KEY` 认证，保护您的API服务不被滥用。
-   **⚡ 高性能架构**: 采用 FastAPI + 异步IO，为高并发而生。
-   **🐳 一键部署**: 提供终极简化的 Docker Compose 配置，无论是本地还是云端，都能轻松启动。

---

## 部署方案选择

您可以根据需求选择最适合您的部署方式：

-   [**方案一：本地部署**](#-方案一本地部署) - **(推荐新手)** 在您自己的电脑上快速运行，用于本地开发和测试。
-   [**方案二：Hugging Face 云端部署**](#-方案二hugging-face-云端部署) - **(推荐进阶)** 免费将服务部署到云端，获得一个可公开访问的API网址。

---

## ⚙️ 方案一：本地部署

通过 Docker，只需四步即可在您的电脑上拥有一个私有的、高性能的API服务。

### 前提条件

-   已安装 [**Docker**](https://www.docker.com/products/docker-desktop/) 和 **Docker Compose**。
-   已安装 [**Git**](https://git-scm.com/)。

### 第 1 步：获取项目代码

打开您的命令行（终端），克隆本项目到您的电脑上。

```bash
git clone https://github.com/你的GitHub用户名/qwen-local.git
cd qwen-local
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

1.  在 `qwen-local` 文件夹中，找到名为 `.env.example` 的文件。
2.  **将它复制并重命名为 `.env`**。
3.  用文本编辑器打开这个新的 `.env` 文件，将您在**第 2 步**中获取到的信息，以及您自定义的API密钥，填写到对应的位置。

**一个最简化的 `.env` 配置示例：**
```env
# .env (最简配置示例)

# 服务监听端口
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

# --- 国际站账号 (可选) ---
INTL_COOKIE=""
INTL_AUTHORIZATION=""
INTL_BX_UA=""
```

### 第 4 步：启动服务！

回到您的命令行（确保当前仍在 `qwen-local` 文件夹内），运行以下命令：

```bash
docker compose up -d --build
```
Docker 将会自动构建镜像并在后台启动服务。

### 第 5 步：测试您的本地API

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

## ☁️ 方案二：Hugging Face 云端部署

此方案可以将您的API服务免费部署到云端，并获得一个公开的HTTPS网址。

### 第 1 步：创建 Hugging Face Space

1.  访问 [Hugging Face New Space](https://huggingface.co/new-space) 页面。
2.  **Space name**: 给它起一个全局唯一的名字，例如 `my-qwen-api`。
3.  **License**: 选择 `mit`。
4.  **Space SDK**: **务必选择 `Docker`**，模板选择 **`Blank`**。
5.  **Public/Private**: 选择 `Public` 以享受免费资源。
6.  点击 **Create Space**。

### 第 2 步：配置云端环境变量 (Secrets)

这是**云端部署最核心的一步**。我们需要把本地 `.env` 文件里的所有配置，安全地设置到Hugging Face的后台。

1.  在您刚刚创建的Space页面，点击 **Settings** 选项卡。
2.  在左侧菜单中，点击 **Secrets**。
3.  点击 **New secret**，然后**逐一添加**您在本地 `.env` 文件中配置的所有变量。

**您需要添加以下所有Secrets：**
| Secret Name              | Secret Value                               |
| ------------------------ | ------------------------------------------ |
| `LISTEN_PORT`            | `8082`                                     |
| `API_MASTER_KEY`         | `your_super_secret_master_key_123`         |
| `MODEL_TO_ACCOUNT_MAP`   | `{"Qwen3-Max-Preview": 2}` (或`{}`)        |
| `CN_ACCOUNT_1_COOKIE`    | `您账号1的Cookie值`                        |
| `CN_ACCOUNT_1_XSRF_TOKEN`| `您账号1的Token值`                         |
| `CN_ACCOUNT_2_COOKIE`    | `您账号2的Cookie值`                        |
| `CN_ACCOUNT_2_XSRF_TOKEN`| `您账号2的Token值`                         |
| `INTL_COOKIE`            | `您的国际站Cookie` (如果不需要可留空)      |
| `INTL_AUTHORIZATION`     | `您的国际站Authorization` (如果不需要可留空) |
| `INTL_BX_UA`             | `您的国际站bx-ua` (如果不需要可留空)         |

### 第 3 步：准备并推送代码

1.  **修改 `README.md` 以适配Hugging Face**
    用文本编辑器打开您本地 `qwen-local` 文件夹中的 `README.md` 文件（也就是本文档），在**最顶部**加入以下内容：
    ```yaml
    ---
    title: Qwen Local API
    emoji: 🚀
    colorFrom: blue
    colorTo: green
    sdk: docker
    app_port: 8082
    ---
    ```
    *（`sdk: docker` 和 `app_port: 8082` 这两行是告诉Hugging Face如何运行您的项目的关键！）*

2.  **推送代码到Hugging Face**
    回到您的命令行（确保在 `qwen-local` 文件夹内），执行以下命令：
    ```bash
    # 设置您的Git身份 (如果是第一次使用)
    git config --global user.name "你的GitHub或HF用户名"
    git config --global user.email "你的邮箱"

    # 关联并推送代码
    git init
    git remote add huggingface https://huggingface.co/spaces/[你的HF用户名]/[你的Space名]
    git add .
    git commit -m "Deploy to Hugging Face"
    git push huggingface main
    ```
    *（推送时，用户名为您的HF用户名，密码为您在[HF Access Tokens页面](https://huggingface.co/settings/tokens)创建的`write`权限的Token。）*

### 第 4 步：测试您的云端API

推送成功后，Hugging Face会自动部署您的服务。等待Space状态变为 `Running` 后，您就可以使用它的公开网址进行测试了！

```bash
# 将URL替换成您的Space地址
curl https://[你的HF用户名]-[你的Space名].hf.space/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_super_secret_master_key_123" \
  -d '{
    "model": "qwen-plus",
    "messages": [{"role": "user", "content": "你好，你现在部署在Hugging Face上了吗？"}]
  }'
```

---

## 💡 高级功能：模型策略路由

您可以通过修改 `.env` 文件（或HF Secrets）中的 `MODEL_TO_ACCOUNT_MAP` 变量，来指定特定模型使用哪个账号处理。

**示例：**
假设您的“账号2”开通了`Qwen3-Max-Preview`的资格，而“账号1”没有。您可以这样配置：
`MODEL_TO_ACCOUNT_MAP='{"Qwen3-Max-Preview": 2}'`

这样配置后：
-   所有对 `qwen-plus`, `qwen-max` 等模型的请求，将自动由**账号1**处理。
-   所有对 `Qwen3-Max-Preview` 模型的请求，将自动由**账号2**处理。

---

## ❓ 常见问题 (FAQ)

-   **Q: 部署后访问API提示 `403 Forbidden`？**
    A: 这是因为您的 `API_MASTER_KEY` 配置正确，但您的请求头 `Authorization: Bearer ...` 中的密钥不正确或缺失。请检查您的密钥。

-   **Q: 部署后服务无法启动，查看日志提示 `KeyError` 或 `AttributeError`？**
    A: 这通常意味着您在Hugging Face Secrets中漏掉了某个必需的环境变量，或者变量名写错了。请仔细核对**第 2 步**中的Secret列表。

-   **Q: 我的 `Access Token` 会过期吗？**
    A: 会的。网页版的认证信息通常有较长的有效期（数周甚至数月），但不是永久的。如果服务开始报错，您可能需要重复**第 2 步**来获取新的认证信息并更新您的 `.env` 文件或HF Secrets。

## 📜 License

本项目采用 [MIT License](LICENSE) 开源。
