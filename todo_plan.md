# ChatBot SNS - 项目进度

## Phase 1 ✅ 核心骨架 (2026-07-14)
- [x] 项目结构、配置系统（pydantic-settings + YAML + 环境变量）
- [x] 消息模型（Message / Reply / LLMMessage）
- [x] 事件总线（EventBus / EventType）
- [x] LLM 抽象引擎 + OpenAI 兼容引擎（含 Ollama）
- [x] 人格引擎 + 默认角色卡（YAML CharacterCard）
- [x] 消息管道 + 短期记忆 Buffer
- [x] 终端适配器 + 优雅退出
- [x] 启动配置预检（_check_config）
- [x] 面试准备文档（docs/phase-1-interview-prep.md）

## Phase 2 ✅ 记忆与平台接入 (2026-07-14)
- [x] ChromaDB 长期记忆（FastEmbed 向量检索，session 级隔离）
- [x] MemoryManager 统一管理短期/长期记忆
- [x] QQ OneBot v11 适配器（WebSocket 收发消息，支持私聊和群聊）
- [x] Edge-TTS 语音合成（免费、无需 API Key、支持中英文）
- [x] 参数调优：max_tokens=8192, short_term_size=100
- [x] 18 个单元测试全部通过
- [x] QQ 适配器实际部署测试 — NapCat Docker 部署完成

## Phase 3 ⬜ 语音与插件
- [ ] GPT-SoVITS 集成（高品质音色克隆）
- [ ] Whisper ASR（语音转文字）
- [ ] 音色切换支持
- [ ] 插件系统（Plugin Loader + Hook API）

## Phase 4 ⬜ 运维与增强
- [ ] 内置插件（天气 / 新闻 / 提醒）
- [ ] Docker 部署方案
- [ ] 服务器运维脚本
- [ ] 多角色动态切换
