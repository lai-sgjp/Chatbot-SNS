import uuid
import logging
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LongTermMemory:
    def __init__(self, persist_directory: str = "data/chroma_db"):
        self._persist_directory = persist_directory
        self._collection = None
        self._disabled = False

    async def _ensure_collection(self):
        if self._collection is not None or self._disabled:
            return

        # 将所有缓存都重定向到项目 data/ 目录，不写入 C 盘
        project_data = os.path.abspath("data")
        os.environ.setdefault("CHROMA_CACHE_DIR", os.path.join(project_data, "chroma_cache"))
        os.environ.setdefault("HF_HOME", os.path.join(project_data, "hf_cache"))
        os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", os.path.join(project_data, "st_cache"))
        os.environ.setdefault("TRANSFORMERS_CACHE", os.path.join(project_data, "transformers_cache"))
        os.environ.setdefault("XDG_CACHE_HOME", os.path.join(project_data, "xdg_cache"))
        for d in [os.environ[v] for v in
                  ["CHROMA_CACHE_DIR", "HF_HOME", "SENTENCE_TRANSFORMERS_HOME", "TRANSFORMERS_CACHE"]]:
            os.makedirs(d, exist_ok=True)

        # Monkey-patch ChromaDB 的 ONNX 模型下载路径，避免写入 C:\Users\Lai\.cache
        try:
            import chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 as onnx_ef
            onnx_dest = os.path.join(project_data, "chroma_cache", "onnx_models", "all-MiniLM-L6-V2")
            onnx_ef.ONNXMiniLM_L6_V2.DOWNLOAD_PATH = onnx_dest
            os.makedirs(onnx_dest, exist_ok=True)
        except Exception:
            pass

        try:
            import chromadb
            client = chromadb.PersistentClient(path=self._persist_directory)
            try:
                from chromadb.utils.embedding_functions import FastEmbedEmbeddingFunction
                fn = FastEmbedEmbeddingFunction(model_name="BAAI/bge-small-zh-v1.5")
                self._collection = client.get_or_create_collection(
                    name="chat_memories", embedding_function=fn
                )
            except (ImportError, ValueError, Exception):
                self._collection = client.get_or_create_collection(
                    name="chat_memories"
                )
            logger.info("ChromaDB ready: %s", self._persist_directory)
        except Exception as e:
            logger.warning("ChromaDB ???: %s. ????????", e)
            self._disabled = True

    async def _safe_op(self, fn, *args, **kwargs):
        if self._disabled:
            return None
        try:
            return fn(*args, **kwargs)
        except PermissionError as e:
            logger.warning("ChromaDB ????: %s. ????????", e)
            self._disabled = True
            return None
        except Exception as e:
            logger.warning("ChromaDB ????: %s", e)
            return None

    async def add_memory(self, session_id: str, user_id: str, content: str,
                         memory_type: str = "conversation") -> None:
        await self._ensure_collection()
        if self._collection is None:
            return
        doc_id = str(uuid.uuid4())
        ts = datetime.now().isoformat()
        await self._safe_op(
            self._collection.add,
            documents=[content],
            metadatas=[{
                "session_id": session_id, "user_id": user_id,
                "timestamp": ts, "type": memory_type,
            }],
            ids=[doc_id],
        )

    async def query_memories(self, query: str, n_results: int = 5,
                             session_id: Optional[str] = None) -> list[dict]:
        await self._ensure_collection()
        if self._collection is None:
            return []
        where = {"session_id": session_id} if session_id else None
        results = await self._safe_op(
            self._collection.query,
            query_texts=[query], n_results=n_results, where=where,
        )
        if results is None:
            return []
        memories = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for i, doc in enumerate(docs):
            memories.append({
                "content": doc,
                "metadata": metas[i] if i < len(metas) else {},
                "distance": dists[i] if i < len(dists) else 0,
            })
        return memories

    async def clear_session(self, session_id: str) -> None:
        await self._ensure_collection()
        if self._collection is None:
            return
        r = self._collection.get(where={"session_id": session_id})
        if r.get("ids"):
            await self._safe_op(self._collection.delete, ids=r["ids"])

