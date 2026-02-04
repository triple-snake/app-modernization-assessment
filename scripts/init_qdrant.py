#!/usr/bin/env python3
"""
Qdrant 컬렉션 초기화 스크립트
2개 컬렉션 생성: Modernization_RAG, System_Metrics_Grade
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import sys

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

def init_qdrant():
    """Qdrant 컬렉션 초기화"""
    
    print(f"🔌 Qdrant 연결 중: {QDRANT_HOST}:{QDRANT_PORT}")
    
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        print("✅ Qdrant 연결 성공")
    except Exception as e:
        print(f"❌ Qdrant 연결 실패: {e}")
        print("💡 Hint: docker-compose -f docker-compose.db.yml up -d 실행했나요?")
        sys.exit(1)
    
    # 기존 컬렉션 삭제 (재실행 시)
    existing_collections = [c.name for c in client.get_collections().collections]
    
    if "Modernization_RAG" in existing_collections:
        client.delete_collection("Modernization_RAG")
        print("🗑️  기존 Modernization_RAG 컬렉션 삭제")
    
    if "System_Metrics_Grade" in existing_collections:
        client.delete_collection("System_Metrics_Grade")
        print("🗑️  기존 System_Metrics_Grade 컬렉션 삭제")
    
    # Collection 1: Modernization_RAG (1536차원 - OpenAI embeddings)
    print("\n📦 Collection 1: Modernization_RAG 생성 중...")
    client.create_collection(
        collection_name="Modernization_RAG",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
    print("✅ Modernization_RAG 컬렉션 생성 완료 (1536차원, Cosine)")
    
    # Collection 2: System_Metrics_Grade (22차원 - 22개 지표 Grade)
    print("\n📦 Collection 2: System_Metrics_Grade 생성 중...")
    client.create_collection(
        collection_name="System_Metrics_Grade",
        vectors_config=VectorParams(size=22, distance=Distance.COSINE),
    )
    print("✅ System_Metrics_Grade 컬렉션 생성 완료 (22차원, Cosine)")
    
    # 검증
    print("\n🔍 컬렉션 확인...")
    collections = client.get_collections()
    print(f"📋 총 {len(collections.collections)}개 컬렉션:")
    for col in collections.collections:
        info = client.get_collection(col.name)
        print(f"  - {col.name}: {info.config.params.vectors.size}차원, {info.config.params.vectors.distance}")
    
    print("\n✅ 모든 작업 완료!")

if __name__ == '__main__':
    print("=" * 60)
    print("Qdrant 컬렉션 초기화 스크립트")
    print("=" * 60)
    init_qdrant()
