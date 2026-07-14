# ChatBot SNS

## 项目概述

### 项目定位
ChatBot SNS 是一个跨平台智能聊天机器人框架，以"核心引擎 + 适配器"架构同时支持终端、QQ 等多个平台。设计目标是提供一个可插拔 LLM、记忆、语音、插件的轻量级智能体框架，完全掌控架构而非依赖第三方框架。

### 开发目的
- 学习并实践事件驱动架构、异步编程、向量检索等工程能力
- 构建一个可个性化定制、有长期记忆的 AI 陪伴机器人
- 作为大厂面试项目展示全栈工程能力

### 核心功能
| 功能 | 说明 | 阶段 |
|------|------|------|
| 多 LLM 引擎 | 兼容 OpenAI / Ollama / 任意 OpenAI 格式 API | Phase 1 |
| 人格系统 | YAML 角色卡，支持多角色切换 | Phase 1 |
| 事件总线 | 发布/订阅模式，插件可注入预处理/后处理钩子 | Phase 1 |
| 终端适配器 | 命令行交互，开发调试用 | Phase 1 |
| 长期记忆 | ChromaDB + FastEmbed 向量检索，session 级隔离 | Phase 2 |
| 记忆管理器 | 短期 Buffer + 长期向量库统一管理 | Phase 2 |
| QQ 适配器 | OneBot v11 WebSocket，支持私聊和群聊 | Phase 2 |
| 语音合成 | Edge-TTS，免费无需 API Key | Phase 2 |

### 适配场景
- 个人 QQ 群/私聊 AI 助手
- 可扩展至微信、Telegram 等平台（新增适配器即可）
- 本地终端调试和开发

---

## 技术栈与运行环境

### 技术栈
| 类别 | 技术 | 说明 |
|------|------|------|
| 语言 | Python >= 3.11 | 使用 StrEnum、type union 等新特性 |
| 异步框架 | asyncio + aiohttp | WebSocket 客户端、非阻塞 IO |
| LLM 接口 | openai SDK | 兼容所有 OpenAI 格式 API |
| 向量数据库 | ChromaDB >= 1.5 | 持久化向量存储，SQLite 后端 |
| Embedding | FastEmbed + BAAI/bge-small-zh-v1.5 | ONNX Runtime，无需 GPU |
| 配置管理 | pydantic-settings + PyYAML | 类型安全 + YAML 可读性 |
| 日志 | loguru | 控制台彩色输出 + 文件按天滚动 |
| 语音合成 | edge-tts | 微软 Azure TTS 前端，300+ 语音 |
| 测试 | pytest + pytest-asyncio | 异步测试，18 个用例 |
| 容器化 | Docker + NapCat | QQ OneBot v11 协议实现 |

### 运行环境
- 操作系统：Windows / Linux / macOS
- Python >= 3.11
- Docker Desktop（仅 QQ 适配器需要，终端模式不需要）
- 网络：LLM API 端点可达

---

## 目录结构

```
ChatBot_SNS/
├── bot/
│   ├── __init__.py              # 包入口
│   ├── main.py                  # 启动入口，适配器路由
│   ├── config.py                # BotConfig + YAML 加载
│   ├── event_bus.py             # EventBus 发布/订阅
│   ├── models.py                # Message / Reply / LLMMessage
│   ├── pipeline.py              # 消息管道 + ConversationBuffer
│   ├── adapters/
│   │   ├── base.py              # BaseAdapter 抽象基类
│   │   ├── __init__.py
│   │   ├── terminal/
│   │   │   └── adapter.py       # 终端适配器
│   │   └── qq/
│   │       ├── adapter.py       # QQ WebSocket 适配器
│   │       ├── onebot.py        # OneBot v11 协议常量/工具
│   │       └── __init__.py
│   ├── llm/
│   │   ├── base.py              # BaseLLMEngine 抽象基类
│   │   ├── openai_engine.py     # OpenAI 兼容引擎
│   │   └── __init__.py
│   ├── memory/
│   │   ├── long_term.py         # ChromaDB 长期记忆
│   │   ├── manager.py           # MemoryManager 统一管理
│   │   └── __init__.py
│   ├── personality/
│   │   ├── engine.py            # PersonalityEngine 角色卡加载
│   │   ├── __init__.py
│   │   └── cards/
│   │       └── default.yml      # 默认角色卡"小智"
│   └── voice/
│       ├── tts.py               # Edge-TTS 语音合成
│       └── __init__.py
├── tests/                       # 18 个单元测试
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_event_bus.py
│   ├── test_llm_openai.py
│   ├── test_memory.py
│   ├── test_personality_engine.py
│   └── test_pipeline.py
├── docs/
│   ├── phase-1-interview-prep.md
│   └── phase-2-interview-prep.md
├── data/                        # 运行时数据（gitignore）
│   ├── chroma_db/               # ChromaDB 持久化
│   ├── logs/                    # 日志文件
│   └── ...
├── config.yml                   # 实际配置（gitignore）
├── config.example.yml           # 配置模板
├── requirements.txt             # 依赖列表
├── pyproject.toml               # pytest 配置
├── start.bat                    # Windows 一键启动脚本
├── todo_plan.md                 # 项目进度
├── work_log.md                  # 工作日志
└── .agents/agents.md            # Agent 上下文
```

---

## 部署与运行步骤

### 一、终端模式（开发调试，无需 Docker）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 复制配置文件
copy config.example.yml config.yml

# 3. 编辑 config.yml，填入 LLM API Key
#    adapter.adapter 保持 "terminal"

# 4. 启动
python -m bot.main
```

### 二、QQ 模式（完整部署，需 Docker）

#### 步骤 1：部署 NapCat 容器

```powershell
# 拉取镜像（国内需配置镜像加速器）
docker pull mlikiowa/napcat-docker:latest

# 启动容器
docker run -d -p 3000:3000 -p 3001:3001 -p 6099:6099 --name napcat --restart=always mlikiowa/napcat-docker

# 获取二维码扫码登录
docker cp napcat:/app/napcat/cache/qrcode.png ./qrcode.png
# 打开 qrcode.png，用手机 QQ 扫码
```

#### 步骤 2：配置 NapCat OneBot 适配器

1. 浏览器打开 `http://127.0.0.1:6099/webui`（Token 见 `docker logs napcat`）
2. 添加 OneBot v11 适配器，类型选 **正向 WebSocket**
3. Host 设为 `0.0.0.0`（Docker 容器内必须用 0.0.0.0，不能用 127.0.0.1）
4. Port 设为 `3001`
5. 设置一个 Token（如 `chatbot123`），保存

#### 步骤 3：配置 ChatBot

编辑 `config.yml`：

```yaml
adapter:
  adapter: "qq"
  qq_ws_url: "ws://localhost:3001"
  qq_token: "chatbot123"   # 与 NapCat 中设置的 Token 一致
```

#### 步骤 4：启动

```powershell
# 方式 A：一键启动（自动启动 Docker + NapCat + ChatBot）
start.bat

# 方式 B：手动启动
python -m bot.main
```

### 三、关机后重新启动

1. 确保 Docker Desktop 已启动（建议设为开机自启）
2. NapCat 容器会自动启动（--restart=always），并尝试自动登录 QQ
3. 运行 `start.bat` 或 `python -m bot.main`
4. 如果 QQ 登录态过期，重新扫码即可：
   ```powershell
   docker restart napcat
   docker cp napcat:/app/napcat/cache/qrcode.png ./qrcode.png
   ```

---

## 核心配置参数说明

配置文件 `config.yml` 完整参数：

### LLM 配置
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `llm.provider` | `"openai"` | LLM 供应商标识 |
| `llm.api_key` | `""` | API Key（必填） |
| `llm.base_url` | `"https://api.openai.com/v1"` | API 端点，可指向 Ollama 等 |
| `llm.model` | `"gpt-4o"` | 模型名称 |
| `llm.temperature` | `0.7` | 生成温度 0~2 |
| `llm.max_tokens` | `8192` | 输出 token 上限 |

### 人格配置
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `personality.card_dir` | `"bot/personality/cards"` | 角色卡目录 |
| `personality.default_card` | `"default"` | 默认角色卡名（对应 default.yml） |

### 记忆配置
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `memory.short_term_size` | `100` | 短期记忆窗口大小（消息条数） |
| `memory.chroma_db_path` | `"data/chroma_db"` | ChromaDB 持久化路径 |

### 适配器配置
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `adapter.adapter` | `"terminal"` | 适配器类型：`terminal` 或 `qq` |
| `adapter.qq_ws_url` | `"ws://localhost:3001"` | OneBot WebSocket 地址 |
| `adapter.qq_token` | `""` | WebSocket 认证 Token |

### 语音配置
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `voice.enabled` | `false` | 是否启用语音 |
| `voice.edge_voice` | `"zh-CN-XiaoxiaoNeural"` | 音色名称 |
| `voice.edge_rate` | `"+0%"` | 语速调整 |
| `voice.edge_volume` | `"+0%"` | 音量调整 |

### 其他
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `debug` | `false` | 调试模式，开启后输出 DEBUG 级日志 |

### 环境变量覆盖
所有配置均可通过 `BOT_` 前缀环境变量覆盖，优先级：环境变量 > config.yml > 默认值。

```bash
export BOT_LLM_API_KEY="sk-xxx"
export BOT_LLM_MODEL="deepseek-v4-flash"
export BOT_ADAPTER_ADAPTER="qq"
export BOT_QQ_WS_URL="ws://localhost:3001"
```

---

## 接口使用说明

### 角色卡自定义

在 `bot/personality/cards/` 目录下创建新的 `.yml` 文件即可添加角色：

```yaml
# bot/personality/cards/assistant.yml
name: "助手"
description: "一个高效的技术助手"
personality: "专业、严谨、逻辑清晰"
speaking_style: "用简洁的中文回答，必要时附上代码示例"
rules:
  - "回答要准确，不确定时说明"
  - "优先给出可操作的方案"
voice_params: {}
```

切换角色：修改 `config.yml` 中 `personality.default_card: "assistant"`

### 事件钩子（插件扩展点）

Pipeline 在消息处理流程中发布事件，外部代码可订阅注入逻辑：

```python
from bot.event_bus import EventBus, EventType

event_bus = EventBus()

# 消息预处理钩子（LLM 调用前）
@event_bus.subscribe(EventType.MESSAGE_PRE_PROCESS)
async def filter_message(message):
    # 敏感词过滤、日志记录等
    pass

# 消息后处理钩子（LLM 回复后）
@event_bus.subscribe(EventType.MESSAGE_POST_PROCESS)
async def post_process(message, reply):
    # 内容审核、格式调整等
    pass

# 回复发送前钩子
@event_bus.subscribe(EventType.REPLY_PRE_SEND)
async def before_send(reply):
    # TTS 转换、消息修饰等
    pass
```

### 运行测试

```bash
# 全部测试
python -m pytest tests/ -v

# 单个模块
python -m pytest tests/test_memory.py -v
```

---

## 更新日志

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-14 | v0.1.0 | Phase 1：核心骨架（LLM/人格/事件总线/终端适配器） |
| 2026-07-14 | v0.2.0 | Phase 2：ChromaDB 记忆/QQ 适配器/Edge-TTS/NapCat 部署 |