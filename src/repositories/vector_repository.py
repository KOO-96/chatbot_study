"""
Qdrant 벡터 데이터베이스 리포지토리

벡터 저장 및 검색을 담당하는 데이터 접근 계층입니다.
임베딩 생성은 EmbeddingGenerator를 사용합니다.
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, QueryResponse
from qdrant_client.http import models
from typing import List, Optional
import uuid
import logging
from pathlib import Path

from src.models.chunk import Chunk, ChunkMetadata
from src.models.search_result import SearchResult
from src.models.document import Document, DocumentMetadata
from src.utils.embedding_generator import EmbeddingGenerator

logger = logging.getLogger(__name__)


class VectorRepository:
    """Qdrant 벡터 데이터베이스 리포지토리 (데이터 접근 계층)"""
    
    def __init__(
        self,
        collection_name: str,
        qdrant_path: str,
        embedding_generator: EmbeddingGenerator
    ):
        """
        Args:
            collection_name: Qdrant 컬렉션 이름
            qdrant_path: Qdrant 로컬 저장 경로
            embedding_generator: 임베딩 생성기 인스턴스
        """
        self.collection_name = collection_name
        self.qdrant_path = Path(qdrant_path)
        self.embedding_generator = embedding_generator
        self.client: Optional[QdrantClient] = None
    
    def initialize(self):
        """Qdrant 클라이언트 초기화"""
        try:
            # Qdrant 클라이언트 초기화 (로컬 경로)
            self.qdrant_path.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(self.qdrant_path))
            qdrant_path_str = str(self.qdrant_path)
            logger.info("Qdrant client initialized: " + qdrant_path_str)
            
            # 컬렉션 생성 (존재하지 않는 경우)
            self._create_collection_if_not_exists()
            
        except Exception as e:
            logger.error("Vector repository initialization failed: " + str(e))
            raise
    
    def _create_collection_if_not_exists(self):
        """컬렉션이 없으면 생성"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                # 임베딩 차원 가져오기
                embedding_dim = self.embedding_generator.get_embedding_dimension()
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info("Collection created: " + self.collection_name)
            else:
                logger.info("Collection already exists: " + self.collection_name)
        except Exception as e:
            logger.error("Collection creation/verification failed: " + str(e))
            raise
    
    async def save_chunks(
        self,
        chunks: List[Chunk]
    ) -> str:
        """
        청크를 벡터화하여 Qdrant에 저장
        
        Args:
            chunks: 저장할 청크 리스트
            
        Returns:
            문서 ID
            
        Raises:
            ValueError: chunks가 비어있는 경우
        """
        if not self.client:
            raise RuntimeError("Vector repository is not initialized")
        
        if not chunks:
            raise ValueError("Cannot save empty chunks list")
        
        try:
            # 텍스트 추출 및 빈 텍스트 필터링
            valid_chunks = []
            valid_texts = []
            for chunk in chunks:
                if chunk.text and chunk.text.strip():
                    valid_chunks.append(chunk)
                    valid_texts.append(chunk.text)
            
            if not valid_texts:
                raise ValueError("Cannot save chunks: all chunks have empty text content")
            
            # 임베딩 생성 (EmbeddingGenerator 사용, E5 모델은 "passage:" prefix 필요)
            embeddings = self.embedding_generator.generate_embeddings(valid_texts, show_progress=False, instruction_type="passage")
            
            # 문서 ID 생성 (첫 번째 청크의 메타데이터에서 가져오기)
            document_id = valid_chunks[0].metadata.document_id
            
            # 포인트 생성
            points = []
            for i, (chunk, embedding) in enumerate(zip(valid_chunks, embeddings)):
                point_id = str(uuid.uuid4())
                point = PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        "document_id": chunk.metadata.document_id,
                        "chunk_index": chunk.metadata.chunk_index,
                        "text": chunk.text,
                        "filename": chunk.metadata.filename,
                        "file_type": chunk.metadata.file_type
                    }
                )
                points.append(point)
            
            # Qdrant에 저장
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            chunks_count = len(chunks)
            logger.info("Chunks saved successfully - document ID: " + document_id + ", chunks count: " + str(chunks_count))
            return document_id
        
        except Exception as e:
            logger.error("Chunk saving failed: " + str(e))
            raise
    
    async def search_similar(
        self,
        query: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        쿼리와 유사한 청크 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 개수
            
        Returns:
            검색 결과 리스트
        """
        if not self.client:
            raise RuntimeError("Vector repository is not initialized")
        
        try:
            # 쿼리 임베딩 생성 (EmbeddingGenerator 사용, E5 모델은 "query:" prefix 필요)
            query_embedding = self.embedding_generator.generate_embedding(query, instruction_type="query")
            
            # 벡터 검색 (qdrant-client 최신 API 사용: query_points)
            # query_points는 리스트를 직접 받을 수 있음
            query_response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding.tolist(),
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )
            
            # 결과를 모델로 변환
            results = []
            for point in query_response.points:
                payload = point.payload or {}
                text = payload.get("text", "")
                
                # 빈 텍스트는 건너뛰기
                if not text or not text.strip():
                    continue
                
                document_id = payload.get("document_id", "")
                if not document_id:
                    continue
                
                # 점수 추출 (query_points는 score를 직접 제공하지 않으므로 거리 기반 계산)
                # 또는 similarity score를 사용 (1.0 - distance for cosine similarity)
                score = getattr(point, 'score', None)
                if score is None:
                    # score가 없으면 기본값 사용 (실제로는 거리 기반 계산 필요)
                    score = 1.0
                
                search_result = SearchResult(
                    text=text,
                    score=float(score) if score is not None else 1.0,
                    metadata=ChunkMetadata(
                        document_id=document_id,
                        chunk_index=payload.get("chunk_index", 0),
                        filename=payload.get("filename"),
                        file_type=payload.get("file_type")
                    )
                )
                results.append(search_result)
            
            return results
        
        except Exception as e:
            logger.error("Search failed: " + str(e))
            raise
    
    async def find_all_documents(self) -> List[Document]:
        """저장된 모든 문서 조회"""
        if not self.client:
            raise RuntimeError("Vector repository is not initialized")
        
        try:
            # 모든 포인트 조회 (스크롤)
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            
            # 문서 ID별로 그룹화
            documents_dict = {}
            for point in scroll_result[0]:
                payload = point.payload
                doc_id = payload.get("document_id")
                
                if doc_id and doc_id not in documents_dict:
                    documents_dict[doc_id] = Document(
                        document_id=doc_id,
                        metadata=DocumentMetadata(
                            filename=payload.get("filename", "Unknown"),
                            file_type=payload.get("file_type", "Unknown")
                        ),
                        chunks_count=0
                    )
                
                if doc_id:
                    documents_dict[doc_id].chunks_count += 1
            
            return list(documents_dict.values())
        
        except Exception as e:
            logger.error("Document list retrieval failed: " + str(e))
            raise
    
    async def delete_by_document_id(self, document_id: str) -> bool:
        """
        특정 문서의 모든 청크 삭제
        
        Args:
            document_id: 삭제할 문서 ID
            
        Returns:
            삭제 성공 여부
        """
        if not self.client:
            raise RuntimeError("Vector repository is not initialized")
        
        try:
            # 해당 문서의 모든 포인트 찾기
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=10000,
                with_payload=False,
                with_vectors=False
            )
            
            if not scroll_result[0]:
                return False
            
            # 포인트 ID 추출
            point_ids = [point.id for point in scroll_result[0]]
            
            # 삭제
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=point_ids
                )
            )
            
            points_count = len(point_ids)
            logger.info("Document deleted successfully - document ID: " + document_id + ", points count: " + str(points_count))
            return True
        
        except Exception as e:
            logger.error("Document deletion failed: " + str(e))
            raise
    
    def cleanup(self):
        """Qdrant 클라이언트 및 리소스 정리"""
        if self.client is not None:
            try:
                # Qdrant 클라이언트는 자동으로 정리되지만 명시적으로 None으로 설정
                self.client = None
                logger.info("Vector repository cleaned up")
            except Exception as e:
                logger.warning("Failed to cleanup vector repository: " + str(e))
