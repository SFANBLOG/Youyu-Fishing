from unittest.mock import MagicMock

from app.config import settings
from app.infra.milvus_client import MilvusStore
from app.infra.minio_client import MinioStore


def test_milvus_disabled_degrades_to_bm25(monkeypatch):
    monkeypatch.setattr(settings, "VECTOR_BACKEND", "off")
    store = MilvusStore()
    assert store.enabled is False
    assert store.ensure_collection() is False
    assert store.search([0.1, 0.2], 5) == []
    assert store.has_doc(1) is False
    rows = [{"id": 1, "idx": 0, "content": "x", "vector": [0.1, 0.2]}]
    assert store.upsert_doc(1, rows) == 0


def test_minio_disable_falls_back_to_local(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "minio")
    store = MinioStore()
    assert store.enabled is True
    store.disable()
    assert store.enabled is False
    assert store.ensure_bucket() is False


def test_milvus_collection_pymilvus_23(monkeypatch):
    monkeypatch.setattr(settings, "VECTOR_BACKEND", "milvus")
    store = MilvusStore()
    fake = MagicMock(spec=["list_collections", "create_collection_with_schema",
                           "create_collection", "prepare_index_params"])
    fake.list_collections.return_value = []
    monkeypatch.setattr(store, "_connect", lambda: fake)
    assert store.ensure_collection() is True
    kwargs = fake.create_collection_with_schema.call_args.kwargs
    assert kwargs["index_params"]["index_type"] == "HNSW"
    assert kwargs["index_params"]["metric_type"] == "COSINE"
    assert [f.name for f in kwargs["schema"].fields] == ["id", "doc_id", "idx", "content", "vector"]
    fake.create_collection.assert_not_called()


def test_milvus_collection_pymilvus_24(monkeypatch):
    monkeypatch.setattr(settings, "VECTOR_BACKEND", "milvus")
    store = MilvusStore()
    fake = MagicMock(spec=["has_collection", "list_collections",
                           "prepare_index_params", "create_collection"])
    fake.list_collections.return_value = []
    index = MagicMock()
    fake.prepare_index_params.return_value = index
    monkeypatch.setattr(store, "_connect", lambda: fake)
    assert store.ensure_collection() is True
    index.add_index.assert_called_once()
    assert fake.create_collection.call_args.kwargs["index_params"] is index


def test_milvus_existing_collection_skips_creation(monkeypatch):
    monkeypatch.setattr(settings, "VECTOR_BACKEND", "milvus")
    store = MilvusStore()
    fake = MagicMock(spec=["list_collections", "create_collection_with_schema"])
    fake.list_collections.return_value = [settings.MILVUS_COLLECTION]
    monkeypatch.setattr(store, "_connect", lambda: fake)
    assert store.ensure_collection() is True
    fake.create_collection_with_schema.assert_not_called()
