# ChatBot SNS - 项目进度

## Phase 1 ✅ 核心骨架 (2026-07-14)
- [x] 项目结构、配置系统（pydantic-settings + YAML + 环境变量）
- [x] 消息模型（Message / Reply / LLMMessage）
- [x] 事件总线（EventBus / EventType）
- [x] LLM 抽象引擎 + OpenAI 兼容引擎（含 Ollama）
- [x] 人格引擎 + 默认角色卡（YAML CharacterCard）
- [x] 消息管道 + 短期记忆 Buffer（已提升至 100 轮）
- [x] 终端适配器 + 优雅退出
- [x] 15 个单元测试全部通过
- [x] 启动配置预检（_check_config）
- [x] 面试准备文档（docs/phase-1-interview-prep.md）

## Phase 2 ⬜ 记忆与平台接入
- [ ] ChromaDB 长期记忆
- [ ] QQ OneBot 适配器（Lagrange / go-cqhttp）
- [ ] 语音基础支持（Edge-TTS）

## Phase 3 ⬜ 语音引擎
- [ ] GPT-SoVITS 集成
- [ ] Whisper ASR
- [ ] 音色切换支持

## Phase 4 ⬜ 插件与运维
- [ ] 插件系统（Plugin Loader + Hook API）
- [ ] 内置插件（天气 / 新闻 / 提醒）
- [ ] Docker 部署方案
- [ ] 服务器运维脚本
