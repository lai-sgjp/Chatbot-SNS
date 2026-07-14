# ChatBot SNS - 工作日志

## 2026-07-14 - Phase 1 核心骨架
- 初始化项目结构和依赖
- 消息模型、配置系统（平坦化 BaseSettings + @property）
- 事件总线（EventBus + EventType StrEnum）
- LLM 抽象引擎 + OpenAI 兼容引擎
- 人格引擎 + 默认角色卡"小智"（YAML CharacterCard）
- 消息管道 + 短期记忆 Buffer
- 终端适配器（TerminalAdapter + run_in_executor）
- 启动入口 main.py + _check_config 配置预检
- 15 个单元测试编写通过
- 项目文档（todo_plan.md, work_log.md, agents.md）
- Git 仓库初始化并推送至 GitHub（ChatBot-SNS）
- 面试准备文档（docs/phase-1-interview-prep.md）
- 参数调优：max_tokens=8192, short_term_size=100

## 2026-07-14 - Phase 2 记忆与平台接入
- ChromaDB 长期记忆模块（LongTermMemory + FastEmbed）
- MemoryManager 统一管理短期/长期记忆
- QQ OneBot v11 适配器（WebSocket + aiohttp）
- Edge-TTS 语音合成模块（TTSManager）
- 更新配置系统：chroma_db_path, qq_ws_url, voice 配置
- 更新消息管道：Pipeline 集成 MemoryManager
- 更新启动入口：支持 QQ 适配器启动
- 适配 ChromaDB FastEmbed 兼容性（兜底 DefaultEmbeddingFunction）
- 3 个新测试 + 更新 1 个旧测试
- 18 个测试全部通过

## 2026-07-14 - QQ 适配器部署测试（NapCat Docker）
- 调研发现 Lagrange.OneBot V1 已被官方 sunset，旧签名服务器 43.129.225.97:8080 失效
- Lagrange V2 签名 API 为白名单制（需 GPG + QQ 群内注册），无法自建 Docker 签名器
- 改用 NapCat（基于 NTQQ 官方客户端，无需签名服务器）作为 OneBot v11 实现
- 配置 Docker 镜像加速器（daocloud）并拉取 mlikiowa/napcat-docker 镜像
- 启动 NapCat 容器（端口 3000 HTTP / 3001 WS / 6099 WebUI）
- 更新 config.yml：adapter 从 terminal 切换为 qq，ws://localhost:3001
- NapCat WebUI: http://127.0.0.1:6099/webui?token=3ef967497091
- NapCat 配置 OneBot v11 正向 WebSocket（host=0.0.0.0 port=3001 token=chatbot123）
- 修复 Docker 容器内 127.0.0.1 绑定导致宿主机无法连接的问题
- 修复 config.py from_yaml 未正确映射 qq_ws_url/qq_token 顶层字段的问题
- QQ 适配器实际部署测试通过：WebSocket 连接成功，消息收发正常
- 更新 config.example.yml：清理乱码、对齐 Phase 2 配置结构
- 18 个单元测试全部通过
- Phase 2 全部完成
- 创建 README.md：项目概述/技术栈/目录结构/部署步骤/配置参数/接口使用说明
- 创建 start.bat：Windows 一键启动脚本（Docker + NapCat + ChatBot）
- 配置 NapCat autoLoginAccount 实现开机自动登录
- 创建 Phase 2 面试准备文档（向量检索/记忆管理/OneBot协议/Docker部署/TTS/配置系统/异步测试）
