import os
os.environ.setdefault("CHROMA_CACHE_DIR", "data/chroma_cache")
os.environ.setdefault("HF_HOME", "data/hf_cache")
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", "data/st_cache")
os.environ.setdefault("TRANSFORMERS_CACHE", "data/transformers_cache")
os.environ.setdefault("XDG_CACHE_HOME", "data/xdg_cache")
for d in [os.environ[v] for v in
          ["CHROMA_CACHE_DIR", "HF_HOME", "SENTENCE_TRANSFORMERS_HOME", "TRANSFORMERS_CACHE"]]:
    os.makedirs(d, exist_ok=True)
