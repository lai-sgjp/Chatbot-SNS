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
