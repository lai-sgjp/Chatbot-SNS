# ChatBot SNS - Agent Context

## Project Overview
Cross-platform chatbot supporting QQ, WeChat. Features: customizable personality, LLM (API/local), long-term memory, voice interaction, plugins.

Python >= 3.11, asyncio, OpenAI-compatible API, ChromaDB (Phase 2), GPT-SoVITS (Phase 3).

## Project Docs
- [todo_plan.md](/E:/work/ChatBot_SNS/todo_plan.md) - 项目进度
- [work_log.md](/E:/work/ChatBot_SNS/work_log.md) - 工作日志
- [docs/phase-1-interview-prep.md](/E:/work/ChatBot_SNS/docs/phase-1-interview-prep.md) - Phase 1 面试准备

## Phase 1 Summary (Completed)
Built core skeleton: event-driven async architecture, LLM abstraction layer, personality engine with character cards, YAML/env config system, terminal adapter, complete unit test suite.

## Phase 2 Summary (Completed)
Memory & platform integration: ChromaDB long-term memory with FastEmbed vector search, MemoryManager unifying short/long-term memory, QQ OneBot v11 adapter (WebSocket + aiohttp), Edge-TTS voice synthesis. Deployed with NapCat Docker (replaced deprecated Lagrange.OneBot V1). 18 unit tests passing. QQ adapter verified with real message send/receive.

## Run
```
pip install -r requirements.txt
python -m bot.main
```

## Env overrides
All config via BOT_ prefix: BOT_LLM_API_KEY, BOT_LLM_BASE_URL, BOT_LLM_MODEL, BOT_QQ_WS_URL, BOT_QQ_TOKEN, BOT_DEBUG

## QQ Adapter Setup (NapCat Docker)
```
docker run -d -p 3000:3000 -p 3001:3001 -p 6099:6099 --name napcat --restart=always mlikiowa/napcat-docker
# Scan QR code: docker cp napcat:/app/napcat/cache/qrcode.png ./qrcode.png
# WebUI: http://127.0.0.1:6099/webui
# Configure OneBot v11 Forward WebSocket on port 3001
```
Note: WebSocket server must bind to 0.0.0.0 (not 127.0.0.1) inside Docker container.

## Encoding Note - 中文字符处理
PowerShell 的 `@''@` here-string 通过管道输入到 Python（`| python`）时，中文字符会丢失变成 `?`。
解决方案：始终使用 `Set-Content -Encoding UTF8` 或 `Add-Content -Encoding UTF8` 直接写入文件，避免通过 Python 管道中转。
`apply_patch` 工具可以正确处理中文字符，可以直接用于含中文的文件创建和编辑。
