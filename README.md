# Video Parser

> 基于 FastAPI + Gradio + Qwen3-VL 的多平台视频解析、下载与 AI 内容提取系统

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115+-green.svg)
![Gradio](https://img.shields.io/badge/gradio-5.0+-orange.svg)
![Qwen3-VL](https://img.shields.io/badge/qwen3--vl-AI-purple.svg)

---

## 在线体验

无需部署，直接访问体验：

| 访问方式 | 地址 |
|---------|------|
| 🦆 SCNet AIHub | https://www.scnet.cn/ui/aihub/agent/wwxiaohuihui/video-parser |

⚡ 即开即用，体验多平台视频解析与 AI 内容提取！

---

## 项目介绍

Video Parser 是一个专业的 AI 驱动视频解析与内容提取系统，支持多平台无水印视频下载，并集成 Qwen3-VL 视觉语言模型智能分析视频内容。

### 核心特性

- **多平台支持**: 抖音、哔哩哔哩、小红书、快手、好看视频等
- **无水印下载**: 智能解析视频直链，绕过水印限制
- **在线播放**: 支持浏览器内直接播放视频
- **AI 内容提取**: 基于 Qwen3-VL 模型智能分析视频内容
- **Web 界面**: 基于 Gradio 的友好操作界面
- **RESTful API**: 标准化接口，支持二次开发
- **自动文档**: FastAPI 自动生成 Swagger/ReDoc 文档

---

## 功能清单

| 功能名称 | 功能说明 | 技术栈 | 状态 |
|---------|---------|--------|------|
| 多平台解析 | 支持抖音、B站、小红书等平台 | Python + BeautifulSoup | ✅ 稳定 |
| 无水印下载 | 智能解析直链，绕过水印 | httpx + requests | ✅ 稳定 |
| 在线播放 | 浏览器直接播放 | Gradio + HTML5 | ✅ 稳定 |
| AI 内容提取 | Qwen3-VL 智能分析视频 | OpenAI SDK + Qwen3-VL | ✅ 稳定 |
| Web 界面 | Gradio 友好操作界面 | Gradio 5.0+ | ✅ 稳定 |
| RESTful API | 标准接口支持二次开发 | FastAPI 0.115+ | ✅ 稳定 |
| 自动文档 | Swagger/ReDoc 文档 | FastAPI | ✅ 稳定 |
| Docker 部署 | 一键容器化部署 | Docker + Compose | ✅ 稳定 |

---

## 支持的平台

| 平台 | 状态 | 平台 | 状态 |
|------|------|------|------|
| 抖音 | ✅ | 小红书 | ✅ |
| 哔哩哔哩 | ✅ | 快手 | ✅ |
| 好看视频 | ✅ |  |  |

---

## 技术架构

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 主要开发语言 |
| FastAPI | 0.115+ | Web 框架 |
| Gradio | 5.0+ | Web UI 框架 |
| Qwen3-VL | latest | AI 视觉语言模型 |
| httpx | latest | HTTP 客户端 |
| Uvicorn | 0.34+ | ASGI 服务器 |
| Pydantic | 2.5+ | 数据验证 |
| BeautifulSoup | 4.12+ | HTML 解析 |

---

## 安装说明

### 环境要求

- Python 3.10+
- ffmpeg（B站视频合并需要）
- Docker / Docker Compose（可选）

### 安装依赖

```bash
pip install -r requirements.txt
```

---

## 使用说明

### 方式一：Docker 部署（推荐）

#### 1. 配置环境变量

```bash
cp .env.example .env
vim .env  # 编辑配置
```

**必填配置：**

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `QWEN_API_KEY` | ModelScope API 密钥 | `ms-xxxxxxxx` |

**可选配置：**

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `QWEN_API_BASE_URL` | API 基础地址 | `https://api-inference.modelscope.cn/v1` |
| `QWEN_MODEL_ID` | 模型 ID | `Qwen/Qwen3-VL-8B-Instruct` |
| `MAX_FRAMES` | 视频分析提取帧数 | `6` |

> API 密钥获取地址：https://modelscope.cn/my/myaccesstoken

#### 2. 使用 Docker Compose

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

#### 3. 使用 Docker 命令

```bash
# 打包镜像
docker build -t video-parser:latest .

# 运行容器
docker run -d \
  --name video-parser \
  -p 5001:5001 \
  -p 7860:7860 \
  --env-file .env \
  -v $(pwd)/static/videos:/app/static/videos \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  video-parser:latest
```

#### 4. 访问应用

- **Web 界面**：http://localhost:7860
- **API 文档**：http://localhost:5001/docs

### 方式二：本地部署

#### 1. 环境要求

- Python 3.10+
- ffmpeg（B站视频合并需要）

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，配置 API 密钥
vim .env
```

#### 4. 启动服务

**启动后端 API 服务（端口 5001）：**

```bash
python api.py
```

**启动 Gradio 前端（端口 7860）：**

```bash
python app.py
```

#### 5. 访问应用

- **Web 界面**：http://localhost:7860
- **API 文档**：http://localhost:5001/docs
- **ReDoc 文档**：http://localhost:5001/redoc

---

## 配置说明

### 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `QWEN_API_BASE_URL` | Qwen API 基础地址 | `https://api-inference.modelscope.cn/v1` |
| `QWEN_API_KEY` | ModelScope API 密钥 | 无（必填） |
| `QWEN_MODEL_ID` | 模型 ID | `Qwen/Qwen3-VL-8B-Instruct` |
| `MAX_FRAMES` | 视频分析提取帧数 | `6` |
| `API_SERVER_URL` | 后端 API 服务地址 | `http://127.0.0.1:5001` |
| `DOMAIN` | 服务域名（生产环境） | 无 |

---

## 项目结构

```
video-parser/
├── api.py                 # FastAPI 后端服务入口
├── app.py                 # Gradio 前端界面（含AI内容提取）
├── qwen3vl.py             # AI视频内容分析工具（命令行版）
├── requirements.txt       # Python 依赖
├── Dockerfile             # Docker 镜像配置
├── docker-compose.yml     # Docker Compose 配置
├── docker-entrypoint.sh   # Docker 启动脚本
├── .env.example           # 环境变量示例
├── configs/               # 配置文件
│   ├── general_constants.py
│   ├── logging_config.py
│   └── business_config.json
├── src/
│   ├── api/               # API 路由
│   ├── downloaders/       # 各平台下载器实现
│   │   ├── base_downloader.py
│   │   ├── douyin_downloader.py
│   │   ├── bilibili_downloader.py
│   │   ├── xiaohongshu_downloader.py
│   │   ├── kuaishou_downloader.py
│   │   └── haokan_downloader.py
│   └── downloader_factory.py
├── utils/                 # 工具函数
│   ├── web_fetcher.py
│   ├── vigenere_cipher.py
│   └── common_utils.py
├── static/                # 静态资源
│   └── videos/            # 下载的视频
├── downloads/             # Gradio 下载目录
└── cache/                 # 播放缓存目录
```

---

## 开发指南

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
vim .env

# 启动后端 API 服务
python api.py

# 启动 Gradio 前端
python app.py
```

### Docker 开发

```bash
# 使用 Docker Compose
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 常用命令

```bash
# ===== Docker Compose 命令 =====
# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# ===== Docker 命令 =====
# 停止容器
docker stop video-parser

# 启动容器
docker start video-parser

# 重启容器
docker restart video-parser

# 删除容器
docker rm -f video-parser

# 进入容器
docker exec -it video-parser bash
```

---

## API 接口

### 解析视频

**POST** `/api/parse`

请求体：
```json
{
  "text": "https://v.douyin.com/xxx"
}
```

请求头：
```
X-Timestamp: 毫秒时间戳
X-GCLT-Text: 随机明文
X-EGCT-Text: 加密后的文本
```

响应：
```json
{
  "retcode": 200,
  "retdesc": "成功",
  "data": {
    "video_id": "xxx",
    "platform": "抖音",
    "title": "视频标题",
    "video_url": "https://...",
    "cover_url": "https://...",
    "audio_url": "https://..."
  },
  "succ": true
}
```

### 获取下载链接

**POST** `/api/download`

请求体：
```json
{
  "video_url": "https://...",
  "video_id": "xxx"
}
```

响应：
```json
{
  "retcode": 200,
  "retdesc": "成功",
  "data": {
    "download_url": "https://..."
  },
  "succ": true
}
```

---

## 示例链接

| 平台 | 示例地址 |
|------|----------|
| 抖音 | `https://www.douyin.com/note/7580598241298069157` |
| 哔哩哔哩 | `https://www.bilibili.com/video/BV1TaqYBcEJc` |
| 小红书 | `https://www.xiaohongshu.com/explore/68ab2dd1000000001c0045d0` |
| 快手 | `https://www.kuaishou.com/short-video/3x8zha3ipq6bg8q` |
| 好看视频 | `https://haokan.baidu.com/v?vid=13766973483433940333` |

---

## AI 视频内容提取

本项目集成了 Qwen3-VL 视觉语言模型，可智能分析视频内容并生成文字描述。

### Web 界面使用

1. 解析视频链接
2. 点击「在线播放」加载视频
3. 点击「AI提取视频内容」按钮
4. 等待 AI 分析完成，查看内容描述

### 命令行工具

```bash
# 列出所有视频文件
python qwen3vl.py --list

# 分析指定视频
python qwen3vl.py --video downloads/video.mp4

# 使用自定义提示词
python qwen3vl.py --video video.mp4 --prompt "这个视频讲的是什么故事？"

# 指定提取帧数（默认6帧）
python qwen3vl.py --video video.mp4 --frames 8

# 交互式模式
python qwen3vl.py --interactive
```

### 工作原理

1. 使用 ffmpeg 从视频中均匀提取关键帧
2. 将帧图片转换为 base64 编码
3. 调用 Qwen3-VL API 分析图片内容
4. 生成视频内容的详细描述

---

## 常见问题

<details>
<summary>Q: B 站视频无法下载？</summary>

A: B 站视频为音视频分离，需要安装 ffmpeg 进行合并。使用 `sudo apt install ffmpeg`（Ubuntu）或 `brew install ffmpeg`（macOS）安装。
</details>

<details>
<summary>Q: 部分平台视频无法下载？</summary>

A: 某些平台可能需要特殊的请求头（Referer）才能下载，可以在代码中添加相应请求头。
</details>

<details>
<summary>Q: AI 内容提取失败？</summary>

A: AI 内容提取需要先播放视频（加载到本地缓存），并确保 ffmpeg 已安装用于提取视频帧。
</details>

<details>
<summary>Q: 视频链接有时效性吗？</summary>

A: 是的，视频链接有时效性，解析后请尽快下载。
</details>

<details>
<summary>Q: 如何添加新平台支持？</summary>

A: 在 `src/downloaders/` 下创建新的下载器类，继承 `BaseDownloader` 基类，实现相关方法，然后在 `downloader_factory.py` 中注册。
</details>

---

## 技术交流群

欢迎加入技术交流群，分享你的使用心得和反馈建议：

 ![image-20260131100545915](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20260131100545915.png)

---

## 作者联系

- **微信**: laohaibao2025
- **邮箱**: 75271002@qq.com

![微信二维码](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Screenshot_20260123_095617_com.tencent.mm.jpg)

---

## 打赏

如果这个项目对你有帮助，欢迎请我喝杯咖啡 ☕

**微信支付**

![微信支付](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20250914152855543.png)

---

## Star History

如果觉得项目不错，欢迎点个 Star ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=wwwzhouhui/video-parser&type=Date)](https://star-history.com/#wwwzhouhui/video-parser&Date)

---

## License

MIT License

---

## 免责声明

本项目仅供学习交流使用，请勿用于非法用途。因使用本项目造成的任何后果，由使用者自行承担。
