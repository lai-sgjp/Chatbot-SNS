# Phase 2 — 记忆与平台接入 · 面试准备文档

> Phase 2 在 Phase 1 核心骨架之上，增加了 ChromaDB 长期记忆、QQ OneBot v11 适配器、Edge-TTS 语音合成，
> 并通过 NapCat Docker 完成了 QQ 消息收发的端到端部署验证。
> 本文档整理 Phase 2 涉及的核心技术点和工程规范，关联大厂面试题。

---

## 1. 向量数据库与语义检索：ChromaDB + FastEmbed

### 技术难点

**为什么需要长期记忆**
- 短期记忆（ConversationBuffer）是 FIFO 滑动窗口，超出 max_size 后旧消息被丢弃
- 用户 50 轮前说过的关键信息（如"我叫小明"）会从上下文消失
- 长期记忆将对话向量化存储，按语义相关性检索，突破上下文窗口限制

**Embedding 模型选型**
- 使用 BAAI/bge-small-zh-v1.5（中文优化，384 维向量）
- 通过 FastEmbed 框架加载（ONNX Runtime 后端，无需 GPU）
- 备选方案：OpenAI text-embedding-3-small（需 API Key）、m3e-base（中文开源）

**ChromaDB 的持久化机制**
- PersistentClient 将数据写入 SQLite + parquet 文件，重启不丢失
- Collection 级别的 metadata 过滤（session_id 隔离不同会话的记忆）
- 向量检索返回 documents + metadatas + distances，distance 越小越相关

**优雅降级策略**
- ChromaDB 初始化可能因 ONNX 模型下载失败、权限问题等出错
- LongTermMemory 设计了 _disabled 标志位：初始化失败后所有操作静默跳过
- _safe_op 包装器统一捕获 PermissionError 和通用异常，不影响主流程

### 工程规范

```
# 缓存路径重定向——所有第三方库缓存统一到项目 data/ 目录
os.environ.setdefault("CHROMA_CACHE_DIR", os.path.join(project_data, "chroma_cache"))
os.environ.setdefault("HF_HOME", os.path.join(project_data, "hf_cache"))
```
- 不污染用户 HOME 目录（C:\Users\...\.cache）
- Monkey-patch ONNX 模型下载路径，确保可移植性
- 所有环境变量用 setdefault 而非直接赋值，尊重用户已有配置

### 大厂面试题

> **Google AI** *"Design a memory system for a conversational AI that can recall facts from 1000 conversations ago. What are the trade-offs between vector search and keyword search?"*
> 切入点：向量检索捕捉语义相似性（"我喜欢猫" vs "我养了一只喵星人"），关键词检索精确匹配但缺乏泛化。生产系统常用混合检索（Hybrid Search）：BM25 关键词 + 向量召回，再 rerank。

> **字节跳动** *"抖音推荐系统的召回阶段如何工作？为什么不用 SQL LIKE 做内容检索？"*
> 切入点：推荐系统的召回和聊天机器人的记忆检索本质相同——从海量候选中快速找到 Top-K 相关项。SQL LIKE 是精确匹配 O(n) 扫描，向量检索用 HNSW/IVF 近似最近邻 O(log n)。

> **腾讯 AI Lab** *"RAG（Retrieval-Augmented Generation）的完整链路？Embedding 模型如何选型？"*
> 切入点：RAG = 检索 + 生成。本项目 Pipeline 中 MemoryManager.get_context() 就是 RAG 的检索阶段，将检索到的记忆拼入 System Prompt。模型选型考虑维度、语言、速度、部署方式。

> **米哈游** *"游戏 NPC 需要记住玩家 200 小时游戏历程中的关键对话。如何设计记忆系统？"*
> 切入点：分层记忆——短期 Buffer 保留最近对话上下文，长期向量库存关键事实，阶段性摘要（LLM 自总结）压缩冗长对话。按 session_id 隔离不同 NPC 的记忆。

---

## 2. 记忆管理器：短期 + 长期统一架构

### 技术难点

**双层记忆架构**
- 短期：ConversationBuffer（内存中的 FIFO 队列，max_size=100）
- 长期：LongTermMemory（ChromaDB 持久化向量库）
- MemoryManager 作为 Facade 统一管理，对外暴露 get_context() 和 store_interaction()

**上下文拼接策略**
```python
async def get_context(self, session_id, user_message, n_memories=5):
    buffer = self._get_buffer(session_id)
    memories = await self.long_term.query_memories(query=user_message, ...)
    context = list(buffer.get_messages())
    return context, memories
```
- 短期记忆作为 LLM 的多轮对话历史（role=user/assistant 交替）
- 长期记忆以"相关记忆"摘要形式注入 System Prompt 尾部
- 检索 Top-3 记忆（避免注入过多噪声），每条截断 200 字

**Session 隔离**
- 每个会话（私聊/群聊）有独立的 session_id（如 private_3911471413 / group_123456）
- 短期 Buffer 按 session_id 分字典存储
- 长期记忆用 ChromaDB metadata where 过滤 session_id

### 大厂面试题

> **阿里巴巴** *"设计一个多租户的知识库系统，不同租户的数据如何隔离？查询性能如何保证？"*
> 切入点：本项目 session_id 隔离是多租户隔离的简化版。生产方案：物理隔离（每个租户独立 DB/Collection）vs 逻辑隔离（metadata where 过滤）。前者安全但成本高，后者灵活但需 ACL 校验。

> **百度** *"对话系统的上下文管理：是全量历史还是摘要？如何平衡上下文长度和效果？"*
> 切入点：全量历史受 token 限制不可持续。策略：近期对话保留原文 + 远期对话 LLM 摘要 + 关键事实向量检索。MemoryManager 的双层架构正是这个思路的落地。

> **Google** *"How would you implement conversation summarization to compress long-term memory? When do you trigger summarization?"*
> 切入点：触发条件——对话轮数阈值或 Buffer 即将溢出时。用 LLM 提取关键事实（人名、偏好、事件），存储为向量记忆条目，原始对话可清除释放上下文。

---

## 3. OneBot v11 协议与 QQ 适配器

### 技术难点

**OneBot v11 协议**
- OneBot v11 是 QQ 机器人事实标准（继承自 go-cqhttp / CQHTTP）
- 事件格式：JSON，包含 post_type（message/notice/request/meta_event）
- 消息事件包含 user_id、group_id、raw_message、message_type（private/group）
- 动作请求：send_private_msg / send_group_msg，通过 WebSocket JSON 发送

**WebSocket 客户端模式**
```python
session = aiohttp.ClientSession(headers=headers)
async with session.ws_connect(self._ws_url) as ws:
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            await self._handle_event(json.loads(msg.data))
```
- ChatBot 作为 WebSocket 客户端连接到 OneBot 实现的 WebSocket 服务端
- 这是"正向 WebSocket"模式（Forward WebSocket）
- 对比："反向 WebSocket"是 OneBot 实现连接到 ChatBot 的服务端（Lagrange 的默认模式）

**事件路由**
- meta_event/lifecycle：连接建立时的心跳，仅日志记录
- message 事件：按 message_type 分发到私聊/群聊处理
- session_id 策略：私聊用 private_{user_id}，群聊用 group_{group_id}

### 大厂面试题

> **腾讯（QQ/微信团队）** *"设计一个 IM 消息推送系统，支持百万级长连接。WebSocket 还是 MQTT？心跳机制如何设计？"*
> 切入点：WebSocket 适合 Web 端双向通信，MQTT 适合移动端低功耗推送。百万连接需要分布式网关（连接层）+ 消息路由层。心跳间隔和超时需平衡电量和实时性。

> **字节跳动** *"飞书机器人接入第三方应用，协议层如何设计才能兼容多个 IM 平台？"*
> 切入点：和本项目的 Adapter 模式一致——抽象 BaseAdapter 接口，每个平台实现具体适配器。OneBot v11 协议是 QQ 特定标准，飞书有自己的事件订阅 API，但消息抽象（Message/Reply）可以共享。

> **Google** *"Design a real-time collaborative editing system. How do you handle conflict resolution with concurrent WebSocket connections?"*
> 切入点：虽然场景不同，但 WebSocket 长连接管理是相通的——连接池、心跳保活、断线重连、消息序号保证。CRDT/OT 是协同编辑特有的冲突解决算法。

---

## 4. Edge-TTS 语音合成

### 技术难点

**为什么选 Edge-TTS**
- 免费、无需 API Key、不需要 GPU
- 基于微软 Azure TTS 的前端接口，支持 300+ 语音（中英文等）
- 输出 MP3 格式，延迟约 200-500ms

**流式音频处理**
```python
audio_buffer = io.BytesIO()
async for chunk in communicate.stream():
    if chunk["type"] == "audio":
        audio_buffer.write(chunk["data"])
```
- Edge-TTS 的 stream() 返回异步迭代器，逐块产出音频数据
- 可以边生成边播放（未来前端对接时降低首字延迟）
- 不需要临时文件，内存中 BytesIO 完成全部操作

**语音参数控制**
- voice：音色选择（zh-CN-XiaoxiaoNeural 女声 / zh-CN-YunxiNeural 男声）
- rate：语速（+0% 默认，+50% 加速）
- volume：音量（+0% 默认，-20% 降音量）

### 大厂面试题

> **字节跳动（火山引擎）** *"TTS 系统的延迟由哪些环节组成？如何优化首字延迟（TTFB）？"*
> 切入点：文本预处理（分词/韵律）→ 声学模型推理 → 声码器 → 音频编码。流式 TTS 将文本分句并行推理，第一句完成即开始播放。Edge-TTS 的 stream() 天然支持流式。

> **米哈游** *"原神角色配音如何实现 AI 语音？音色克隆的技术方案？"*
> 切入点：Edge-TTS 是通用 TTS（无法克隆特定音色）。音色克隆方案：GPT-SoVITS（少量样本微调）、VITS（端到端）、sovits-svc（歌唱转换）。Phase 3 计划集成 GPT-SoVITS。

> **Google** *"Speech synthesis quality metrics: MOS, CMOS, MUSHRA. How do you evaluate TTS naturalness?"*
> 切入点：MOS（Mean Opinion Score）5 分制人工评分；CMOS 对比评分；MUSHRA 多刺激参考测试。自动评估可用 SpeakerNet 计算 speaker similarity。Edge-TTS 的 MOS 约 3.5-4.0。

---

## 5. Docker 容器化部署

### 技术难点

**镜像加速器配置**
- 中国大陆直连 Docker Hub 超时（registry-1.docker.io 被 IPv6 阻断）
- 解决：在 daemon.json 配置 registry-mirrors
```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.m.daocloud.io"
  ]
}
```
- 不同镜像站对不同镜像的可用性不同（hello-world 通过 1ms.run，NapCat 通过 daocloud）

**Docker 网络模型：127.0.0.1 陷阱**
- NapCat 的 WebSocket 服务绑定 127.0.0.1（容器内 localhost）
- Docker 端口映射 -p 3001:3001 通过容器的 eth0 接口转发
- 容器内 127.0.0.1 只监听 lo 接口，eth0 流量进不来
- 解决：配置 host 为 0.0.0.0（监听所有接口），或使用 --network host 模式

**NapCat 替代 Lagrange 的技术原因**
- Lagrange.OneBot V1 已被官方 sunset（废弃）
- V2 签名 API 是白名单制（需 GPG + QQ 群注册），无法自建
- NapCat 基于 NTQQ 官方客户端，不需要协议签名服务器
- NapCat 提供 OneBot v11 兼容接口，适配器代码零改动

### 工程规范

```dockerfile
# 容器端口映射原则
docker run -d -p 3000:3000 -p 3001:3001 -p 6099:6099 --name napcat --restart=always mlikiowa/napcat-docker
```
- 端口映射只暴露必要端口（3000 HTTP / 3001 WS / 6099 WebUI）
- --restart=always 确保容器异常退出后自动重启
- 数据持久化路径：/app/.config/QQ（QQ 登录态）、/app/napcat/config（适配器配置）

### 大厂面试题

> **Google SRE** *"A microservice inside a Docker container can't be reached from the host. Walk through your debugging process."*
> 切入点：分层排查——TCP 层（Test-NetConnection 端口是否通）→ HTTP 层（curl 是否返回）→ 应用层（日志是否正常）。本项目的 127.0.0.1 绑定问题是经典 Docker 网络陷阱。

> **阿里巴巴** *"Docker 镜像加速方案对比：自建 Harbor vs 公共镜像 vs CDN 加速？大规模集群如何管理镜像分发？"*
> 切入点：开发阶段用公共镜像加速（daocloud），生产用私有 Harbor + 镜像预热（预拉到所有节点）。大规模集群可用 P2P 分发（Dragonfly/kraken）。

> **腾讯云** *"容器化部署中如何保证数据持久化？Volume 和 Bind Mount 的区别和选型？"*
> 切入点：Volume 由 Docker 管理、跨平台一致、易备份；Bind Mount 直接映射主机路径、简单但耦合路径。本项目 NapCat 用了端口映射，生产应加 -v 挂载配置和登录态目录。

> **字节跳动** *"服务网格（Service Mesh）和传统 Docker 网络有什么区别？Istio 解决了什么问题？"*
> 切入点：Docker 网络是单机/集群层面的连通，Service Mesh 在应用层注入 sidecar 处理流量管理、可观测性、安全策略。从 NapCat 的单容器部署扩展到微服务网格是大规模化的方向。

---

## 6. 配置系统演进：from_yaml 的字段映射

### 技术难点

**平坦化配置的映射问题**
```yaml
# config.yml
adapter:
  adapter: "qq"
  qq_ws_url: "ws://localhost:3001"
  qq_token: "chatbot123"
```
```python
# 错误的 from_yaml：所有 adapter 段字段加 adapter_ 前缀
flat[f"{section}_{key}"] = value  # 生成 adapter_qq_ws_url

# BotConfig 的顶层字段是 qq_ws_url（不带 adapter_ 前缀）
# pydantic 报错：Extra inputs are not permitted
```
- 问题根源：pydantic-settings 的 model_config 禁止额外字段（extra_forbidden）
- 修复：qq_ws_url 和 qq_token 是 BotConfig 的顶层字段，from_yaml 需要特殊处理

```python
# 修复后的 from_yaml
for key, value in section_data.items():
    if key in ("qq_ws_url", "qq_token"):
        flat[key] = value           # 顶层字段，不加前缀
    else:
        flat[f"{section}_{key}"] = value  # 正常加段名前缀
```

### 工程规范

- YAML 配置的嵌套段落（adapter:）和 Python 类的平坦字段（qq_ws_url）之间存在映射层
- from_yaml 是唯一的映射转换点，集中处理避免散落的特殊逻辑
- pydantic 的 extra_forbidden 策略是好习惯——未知字段直接报错，防止配置拼写错误静默失效

### 大厂面试题

> **腾讯** *"微服务有 200 个配置项，分布在不同模块。配置中心如何做到模块化又不失统一管理？"*
> 切入点：YAML 分段（llm/personality/memory/adapter）是模块化的体现，from_yaml 做统一解析。扩展到分布式配置中心可按 namespace/namespace+group 组织，客户端按需订阅自己模块的配置。

> **Google** *"How do you handle configuration drift in a fleet of 10000 servers? Immutable infrastructure vs config management."*
> 切入点：配置漂移（手动改了某台机器的配置导致不一致）。不可变基础设施（容器镜像包含配置）从根源消除漂移；Ansible/Puppet 做期望状态收敛是传统方案。

---

## 7. 异步测试策略

### 技术难点

**异步记忆系统的测试**
```python
@pytest.mark.asyncio
async def test_memory_manager_store_and_context(memory_manager):
    await memory_manager.store_interaction("s1", "你好", "你好呀", "u1")
    context, memories = await memory_manager.get_context("s1", "你好")
    assert len(context) == 2       # 短期：user + assistant
    assert len(memories) >= 1      # 长期：至少 1 条匹配
```
- MemoryManager 的 get_context 返回 tuple（短期 messages + 长期 memories）
- 测试同时验证短期写入和长期向量检索
- Mock 策略：用临时 ChromaDB 路径（tmp_path），避免污染开发数据库

**Test Fixture 的隔离**
```python
@pytest.fixture
def memory_manager(tmp_path):
    return MemoryManager(short_term_size=10, chroma_db_path=str(tmp_path / "test_chroma"))
```
- pytest 的 tmp_path 自动创建临时目录，测试结束自动清理
- 每个测试用例独立的 ChromaDB 实例，互不干扰

### 大厂面试题

> **Google SET** *"How do you test a system that depends on an external vector database? Integration vs unit testing boundaries."*
> 切入点：单元测试 Mock 向量检索返回预设结果，测试 MemoryManager 的拼接逻辑；集成测试用临时 ChromaDB 实例测试真实向量化+检索；E2E 测试完整 Pipeline+真实 LLM。

> **字节跳动** *" pytest fixture 和 unittest setUp/tearDown 的区别？conftest.py 的作用域如何设计？"*
> 切入点：fixture 依赖注入（按参数名注入）比 setUp 的继承更灵活；conftest.py 的 scope（function/module/session）控制 fixture 生命周期，session 级 fixture 避免重复初始化开销大的资源。

---

## 附录

### Q：为什么不用 LangChain 的 Memory 模块？

LangChain 的 ConversationBufferMemory 功能类似，但引入 LangChain 全家桶会带来大量依赖和抽象层。我们的 MemoryManager 直接对接 ChromaDB API，更轻量、更可控，也更容易定制检索策略。

### Q：NapCat 和 Lagrange 的本质区别是什么？

Lagrange 是协议逆向实现（自己实现 NTQQ 协议栈），需要签名服务器对协议包签名。NapCat 是官方客户端注入（在真实 QQ NT 客户端进程内 Hook），不需要签名——因为它本身就是"官方客户端"。

### Q：OneBot v11 的正向和反向 WebSocket 有什么区别？

- 正向 WebSocket（Forward WS）：OneBot 实现作为 WS 服务端，ChatBot 作为客户端连接（本项目采用的方案）
- 反向 WebSocket（Reverse WS）：OneBot 实现作为客户端连接到 ChatBot 的 WS 服务端（Lagrange 默认方案）
- 正向 WS 更简单（Bot 主动连接），反向 WS 适合 Bot 在 NAT 后面无公网 IP 的场景

### Q：向量检索的 distance 值怎么解读？

ChromaDB 默认用余弦距离（distance = 1 - cosine_similarity），值域 [0, 2]：
- 0 = 完全相同（cosine_similarity = 1）
- 1 = 正交（无相关性）
- 2 = 完全相反
- 实际使用中 distance < 0.5 通常表示语义高度相关