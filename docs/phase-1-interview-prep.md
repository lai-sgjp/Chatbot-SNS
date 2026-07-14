# Phase 1 — 核心骨架 · 面试准备文档

> 本项目是一个跨平台智能聊天机器人，Phase 1 构建了核心骨架：事件驱动架构 + LLM 抽象引擎 + 人格系统 + 配置系统。
> 本文档整理了 Phase 1 涉及的技术难点，并关联国内外大厂（腾讯、阿里、网易、米哈游、Google）在相关领域的面试题。

---

## 1. 架构设计：事件驱动 + 适配器模式

### 技术难点

**平台无关性的消息抽象**
- 需要同时支持终端、QQ、微信、Telegram 等多个平台
- 定义 BaseAdapter 抽象基类，规定 start() 和 send(Reply) 两个核心接口
- 具体平台只关心"如何监听"和"如何发送"，不关心消息处理逻辑

**事件总线的设计取舍**
- Phase 1 用进程内 EventBus 而非消息队列，减少运维复杂度
- 未来扩展：EventBus 可桥接到 Redis/RabbitMQ，对已有代码零改动
- 事件类型用 StrEnum 而非普通枚举 → 日志友好、天然可序列化

**消息管道的责任链**
- 消息处理是流水线：预处理→人格注入→记忆加载→LLM→后处理→TTS
- 每个环节通过 EventBus 的 publish/subscribe 机制可被插件扩展

### 大厂面试题

> **腾讯** *"设计一个支持多端接入的智能客服系统。要求：一个核心引擎，同时服务微信公众号、小程序、PC 网页。"*
> 切入点：本题的 Adapter 模式 + Pipeline 架构可直接复用。重点讲通过抽象接口解耦平台差异，以及事件总线在核心和各端之间传递消息。

> **阿里巴巴** *"淘宝的消息推送系统每天处理百亿级消息，请画出架构图并说明如何保证消息不丢失不重复。"*
> 切入点：对比 EventBus（进程内同步）和工业级消息队列的区别。讨论何时需要引入消息队列——跨进程、持久化、削峰填谷。

> **Google** *"Design a logging system that supports multiple output backends (file, network, cloud storage) with pluggable formatters."*
> 切入点：和 Adapter 模式完全一致。BaseAdapter 是 output backend 的抽象，EventBus 可用作日志事件的发布通道。

> **米哈游** *"原神聊天系统需要支持多语言、多平台、表情包、语音消息，核心消息管道如何设计？"*
> 切入点：Message 的 raw 字段可携带平台特有元数据，Pipeline 中 EventBus 钩子可插入语音转文字、表情转义等处理器。


---

## 2. 异步编程：asyncio 与消息管道

### 技术难点

**asyncio 中阻塞调用的处理**
- input() 是同步阻塞的，直接调用会阻塞事件循环
- 解法：loop.run_in_executor(None, input, prompt) 将阻塞调用交给线程池

**Windows 上的信号处理限制**
- loop.add_signal_handler() 在 Windows 上抛出 NotImplementedError
- 解法：try/except 兜底，Windows 用户用 Ctrl+C 的默认行为

**asyncio 中异常传播**
- 事件总线的 handler 抛出异常会中断 publish 调用链
- 解法：每个 handler 包裹 try/except，单个失败不影响其他 handler

### 大厂面试题

> **腾讯** *"Python asyncio 中 await 和 run_in_executor 的区别？什么场景下该用哪个？举一个你在实际项目中遇到的阻塞问题。"*
> 切入点：await 用于真正的异步 IO（网络请求、文件读写），run_in_executor 用于 CPU 密集型或阻塞调用（如 input()）。TerminalAdapter 是典型案例。

> **阿里巴巴** *"协程和线程的区别？在 Web 服务中为什么用协程处理 IO 密集型请求比线程更优？"*
> 切入点：协程协作式调度（用户态），线程抢占式调度（内核态）。协程上下文切换成本极低（~1us vs 1us+），适合大量并发 IO。LLM 调用 99% 时间在等网络响应，asyncio 期间可调度其他协程。

> **Google** *"What happens when you await a coroutine? Describe the event loop mechanism in detail."*
> 切入点：await 将控制权交还给事件循环，事件循环检查可运行协程队列，取出下一个调度执行。asyncio 使用 epoll(Linux)/IOCP(Windows) 实现 IO 多路复用。

> **网易** *"MMORPG 的 AOI 算法需要每秒处理几万个玩家的位置更新。如果用 Python，如何利用 asyncio？"*
> 切入点：每个 session 独立的消息队列和 buffer 天然适合 asyncio 并发模型，可用 gather 或 TaskGroup 并发执行。

---

## 3. LLM 抽象层：多供应商兼容设计

### 技术难点

**统一的 LLM 调用接口**
- OpenAI、Ollama、其他兼容 API 请求格式基本一致但细节不同
- 解法：BaseLLMEngine 抽象基类，规定 chat(messages) → str 一个接口

**流式 vs 非流式兼容**
- Phase 1 用非流式简单可靠，未来需要打字机效果
- 解法：chat() 加 stream: bool = False 参数，返回 str | AsyncIterator[str]

**Token 管理**
- 不同模型上下文窗口不同（4K ~ 1M），Buffer 需根据模型调整
- 解法：ConversationBuffer max_size 由配置驱动，用户按模型设置

### 大厂面试题

> **百度/阿里** *"设计一个 LLM Gateway 统一管理多家大模型调用，考虑鉴权、限流、降级、结果缓存。"*
> 切入点：BaseLLMEngine 模式 + EngineFactory 动态选择实现。扩展点：令牌桶限流、主模型失败自动降级、语义缓存。

> **米哈游** *"游戏 NPC 对话中如何平衡 LLM 的创造性和可控性？提示词工程的具体实践。"*
> 切入点：CharacterCard 的三级约束——personality 控制性格底色，speaking_style 控制语言风格，rules 控制硬约束。

> **Google** *"Your chatbot keeps generating harmful responses despite safety prompts. Design a defense-in-depth strategy."*
> 切入点：多层防线——System Prompt（第一道）、MESSAGE_POST_PROCESS 钩子内容审核、插件输出后过滤、回复级规则检查。

> **腾讯** *"大模型推理延迟优化：流式输出、KV Cache、Speculative Decoding。你会如何利用？"*
> 切入点：Pipeline 未来支持流式 AsyncIterator，第一个 token 即返回用户降低感知延迟。KV Cache SDK 默认启用，Speculative Decoding 需要模型侧支持。

---

## 4. 配置系统：YAML + 环境变量 + 类型安全

### 技术难点

**多层配置源叠加**
- 配置文件(YAML) → 环境变量 → 默认值，优先级从高到低
- 解法：pydantic-settings env_prefix + 平坦字段（llm_model vs llm.model）+ @property 重建嵌套接口

**类型安全**
- 用户 YAML 字符串需要变成类型化 Python 对象
- 解法：pydantic BaseModel + Literal/bool 类型注解，解析时自动校验

**密钥安全**
- API Key 不应该硬编码提交到 Git
- 解法：config.yml 写入 .gitignore，config.example.yml 作为模板。也支持纯环境变量注入

### 大厂面试题

> **腾讯** *"微服务可能有几百个配置项，如何设计安全、灵活、可追溯的配置中心？"*
> 切入点：从三层配置源扩展到分布式配置中心（etcd/Apollo/Nacos），讨论热更新、版本管理、变更审计、灰度发布。

> **阿里巴巴** *"Nacos 的配置变更如何实时推送到客户端？客户端如何保证变更期间服务不中断？"*
> 切入点：对比静态配置，讨论长轮询机制、配置缓存与回退、变更事件的监听回调。

> **Google(SRE)** *"Design a secure secrets management system. API keys, database passwords, TLS certificates."*
> 切入点：.gitignore + 环境变量是基础。生产应使用专用密钥管理（Secret Manager/Vault/AWS Secrets Manager），含自动轮转和访问审计。

> **网易** *"项目从本地开发到生产部署，配置如何做差异化管理？"*
> 切入点：config.yml（本地私有）+ config.example.yml（仓库提交）是雏形。扩展到多环境可使用 config.<env>.yml 分层覆盖或 docker-compose。


---

## 5. 人格引擎：提示词工程与角色卡片

### 技术难点

**结构化的人格表示**
- 性格、说话风格、规则等是松散的自然语言描述
- 解法：CharacterCard 数据类，每个字段有明确语义和默认值，YAML 编写可读性好

**System Prompt 动态组装**
- 不同角色卡有不同的强调重点
- 解法：build_system_prompt() 按固定模板 + 变量填充。未来可升级 Jinja2

**多角色切换**
- 不同 session 可使用不同人格
- 解法：PersonalityEngine 在 session 级别持有不同 card，通过 session_id 路由

### 大厂面试题

> **百度** *"System Prompt 和 User Prompt 的最佳实践？如何防止提示词注入？"*
> 切入点：System Prompt 设角色规则（不可见不可改），User Prompt 是输入。防御：rules 放最后、EventBus 预处理检查输入、后处理检查回复是否泄露规则。

> **米哈游** *"50+ NPC 各自独特的对话风格，提示词模板如何复用与差异化？"*
> 切入点：CharacterCard 继承体系——基础配置放在默认值，每个 NPC 覆盖差异化字段。可建立卡片继承（骑士→圣骑士，法师→大法师）。

> **Google(PM/AI)** *"Character.AI 用户花大量时间角色扮演。如何设计角色系统保持自由度又不偏离设定？"*
> 切入点：三层约束——软约束（性格风格指导方向，允许灵活发挥）、硬规则（rules 必须遵守）、记忆回溯（阶段性总结修正偏离）。

> **腾讯 AI Lab** *"多轮对话中如何保持角色一致性？50 句话后角色跑偏怎么解决？"*
> 切入点：短期 Buffer + 长期记忆向量检索。每次生成前检索最近 K 条相关历史注入上下文。阶段性用 LLM 自检（self-reflection）。

---

## 6. Python 元编程：数据类、抽象基类、枚举

### 技术难点

**@dataclass vs BaseModel**
- Message/Reply 用 @dataclass 轻量零依赖
- CharacterCard、配置类用 BaseModel 需要校验和序列化

**ABC 设计粒度**
- BaseLLMEngine 只抽象 chat()，最小接口原则
- BaseAdapter 只有 start() + send()，不给实现者负担

**StrEnum 的优势**
- EventType 用 StrEnum(Python 3.11+) 而非 IntEnum
- 值就是字符串，日志调试时直接可读

### 大厂面试题

> **腾讯** *"Python ABC 和 Protocol 有什么区别？分别在什么场景使用？"*
> 切入点：ABC 通过继承建立 is-a 关系，适合有方法实现共享的场景。Protocol 是结构子类型（duck typing），适合看起来像即可的场景。

> **字节/微软** *"dataclass 和 namedtuple 有什么区别？什么时候用 pydantic BaseModel？"*
> 切入点：namedtuple 不可变性能更好功能有限。dataclass 可变有 __post_init__。BaseModel 有校验序列化 JSON Schema，适合配置和 API 边界。

> **阿里巴巴** *"设计一个插件系统，允许第三方注册自定义事件处理器，接口设计如何确保兼容性？"*
> 切入点：就是 EventBus！定义好 EventType 枚举、Handler 签名 Callable[..., Awaitable[None]]、subscribe/unsubscribe 生命周期管理。

---

## 7. 工程实践：测试策略、日志、优雅退出

### 技术难点

**异步代码单元测试**
- 协程需要事件循环，pytest-asyncio auto 模式自动管理
- Mock LLM：AsyncMock + Mock(spec=BaseLLMEngine) 类型安全

**日志分层**
- loguru 统一日志：控制台彩色输出 + 文件按天滚动归档
- INFO 日常、DEBUG 调试、WARNING 配置提示

**优雅退出**
- Ctrl+C 先停止消息循环再退出
- 解法：adapter.stop() + asyncio CancelledError 异常处理

### 大厂面试题

> **Google SET** *"How do you test code that makes external API calls? Design a testing strategy."*
> 切入点：三层策略——单元测试 Mock LLM 调用测试 Pipeline 逻辑；集成测试配置真实 API 但限频；E2E 完整终端→LLM 回复链路。

> **腾讯** *"IM 类应用性能测试：每秒 1000 条消息并发处理，如何设计压测方案？"*
> 切入点：模拟 1000 并发 session，消息经过完整 Pipeline。关注吞吐量、EventBus handler 执行耗时、内存泄漏（Buffer 是否正确释放）。

---

## 附录

### Q：为什么不用现成框架（NoneBot、Koishi）？

NoneBot 聚焦 QQ 消息处理，我们需要可插拔 LLM/记忆/TTS 的智能体框架，且希望完全掌控架构。定制框架长期维护成本更低。

### Q：短期记忆和长期记忆的区别？

短期记忆（ConversationBuffer）是当前会话原始历史，放 LLM 上下文。长期记忆（Phase 2 ChromaDB）是从多轮对话提取的关键事实，向量化按相关性检索。

### Q：为什么用平坦化配置而非纯嵌套？

pydantic-settings 对嵌套 BaseSettings 的环境变量映射有限，平坦字段 + @property 重建嵌套访问是兼顾环境变量易用性和代码可读性的方案。用户写 YAML 时仍然是嵌套的。
