import os

# 在测试环境中重定向 ChromaDB 和 HuggingFace 缓存到项目 data 目录
# 避免沙箱阻止写入 C:\Users\Lai\.cache
os.environ.setdefault("CHROMA_CACHE_DIR", "data/chroma_cache")
os.environ.setdefault("HF_HOME", "data/hf_cache")
os.makedirs("data/chroma_cache", exist_ok=True)
os.makedirs("data/hf_cache", exist_ok=True)

