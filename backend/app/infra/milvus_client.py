"""Milvus 2.x 向量库封装。

集合结构：id(主键=chunk_id) / doc_id / idx / content / vector(FLOAT_VECTOR, COSINE)
上层用 asyncio.to_thread 调用这些同步方法，避免阻塞事件循环。
Milvus 不可用时不抛异常，返回空结果，由检索层降级为纯 BM25。
"""
import logging

from app.config import settings

logger = logging.getLogger("youyu.milvus")


class MilvusStore:
    def __init__(self):
        self._client = None
        self._warned = False

    @property
    def enabled(self) -> bool:
        return settings.VECTOR_BACKEND.lower() == "milvus"

    def _connect(self):
        if self._client is not None:
            return self._client
        from pymilvus import MilvusClient  # 惰性导入，未装依赖也能启动
        self._client = MilvusClient(uri=settings.milvus_uri, timeout=6)
        return self._client

    def _warn(self, action: str, exc: Exception):
        if not self._warned:
            logger.warning("Milvus 不可用（%s 将降级为纯关键词检索）：%s", action, exc)
            self._warned = True

    def ensure_collection(self) -> bool:
        if not self.enabled:
            return False
        try:
            client = self._connect()
            name = settings.MILVUS_COLLECTION
            # 2.3.x 没有 has_collection，list_collections() 两个版本都可用
            if name in client.list_collections():
                return True
            from pymilvus import CollectionSchema, DataType, FieldSchema
            schema = CollectionSchema(
                fields=[
                    FieldSchema("id", DataType.INT64, is_primary=True, auto_id=False),
                    FieldSchema("doc_id", DataType.INT64),
                    FieldSchema("idx", DataType.INT64),
                    FieldSchema("content", DataType.VARCHAR, max_length=4096),
                    FieldSchema("vector", DataType.FLOAT_VECTOR, dim=settings.EMBED_DIM),
                ],
                enable_dynamic_field=False,
            )
            index_params = {"field_name": "vector", "index_type": "HNSW",
                            "metric_type": "COSINE", "params": {"M": 8, "efConstruction": 64}}
            if hasattr(client, "has_collection"):
                # pymilvus >= 2.4：prepare_index_params() 返回 IndexParams 对象
                index = client.prepare_index_params()
                index.add_index(**index_params)
                client.create_collection(collection_name=name, schema=schema,
                                         index_params=index, consistency_level="Strong")
            else:
                # pymilvus 2.3.x：index_params 是 dict，走 create_collection_with_schema
                client.create_collection_with_schema(
                    collection_name=name, schema=schema, index_params=dict(index_params),
                    consistency_level="Strong")
            logger.info("Milvus collection ready: %s (dim=%s, HNSW/COSINE)", name, settings.EMBED_DIM)
            return True
        except Exception as exc:
            self._warn("建集合", exc)
            self._client = None
            return False

    def upsert_doc(self, doc_id: int, rows: list[dict]) -> int:
        """rows: [{id, vector, idx, content}]；先删该文档旧向量再批量写入。"""
        if not self.enabled or not rows:
            return 0
        try:
            client = self._connect()
            name = settings.MILVUS_COLLECTION
            if not self.ensure_collection():
                return 0
            client.delete(collection_name=name, filter=f"doc_id == {int(doc_id)}")
            data = [{"id": int(r["id"]), "doc_id": int(doc_id),
                     "idx": int(r["idx"]), "content": str(r["content"])[:2000],
                     "vector": r["vector"]} for r in rows]
            client.insert(collection_name=name, data=data)
            client.flush(collection_name=name)
            return len(data)
        except Exception as exc:
            self._warn("写向量", exc)
            return 0

    def delete_doc(self, doc_id: int) -> None:
        if not self.enabled:
            return
        try:
            self._connect().delete(collection_name=settings.MILVUS_COLLECTION,
                                   filter=f"doc_id == {int(doc_id)}")
        except Exception as exc:
            self._warn("删向量", exc)

    def has_doc(self, doc_id: int) -> bool:
        """该文档的切片是否已有向量，供后台切片预览展示。"""
        if not self.enabled:
            return False
        try:
            res = self._connect().query(
                collection_name=settings.MILVUS_COLLECTION,
                filter=f"doc_id == {int(doc_id)}",
                output_fields=["id"],
            )
            return bool(res)
        except Exception as exc:
            self._warn("查向量", exc)
            return False

    def search(self, vector: list[float], top_k: int) -> list[dict]:
        """返回 [{id, score, content, doc_id, idx}]，失败返回空列表。"""
        if not self.enabled or not vector:
            return []
        try:
            client = self._connect()
            res = client.search(
                collection_name=settings.MILVUS_COLLECTION,
                data=[vector], limit=top_k,
                output_fields=["doc_id", "idx", "content"],
                search_params={"metric_type": "COSINE", "params": {"ef": 64}},
            )
            hits = []
            for item in (res[0] if res else []):
                # 2.4 返回 entity 子字典；部分版本直接把输出字段摊平在 hit 上
                entity = item.get("entity") or item
                hits.append({
                    "id": int(item.get("id", entity.get("id", 0))),
                    "score": float(item.get("distance", 0.0)),
                    "doc_id": entity.get("doc_id"),
                    "idx": entity.get("idx"),
                    "content": entity.get("content", ""),
                })
            return hits
        except Exception as exc:
            self._warn("向量检索", exc)
            return []


milvus_store = MilvusStore()
