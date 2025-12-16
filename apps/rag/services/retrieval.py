from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from .ingestion import get_vector_store


class HybridRetriever:
    def __init__(self, k: int = 10):
        self.k = k
        self.vector_store = get_vector_store()
        self._bm25_retriever = None
        self._documents = None
    
    def _load_documents_for_bm25(self):
        if self._documents is None:
            results = self.vector_store.similarity_search("", k=1000)
            self._documents = results
            self._bm25_retriever = BM25Retriever.from_documents(
                self._documents,
                k=self.k
            )
    
    def get_ensemble_retriever(self) -> EnsembleRetriever:
        self._load_documents_for_bm25()
        
        vector_retriever = self.vector_store.as_retriever(
            search_kwargs={"k": self.k}
        )
        
        return EnsembleRetriever(
            retrievers=[vector_retriever, self._bm25_retriever],
            weights=[0.5, 0.5]
        )
    
    def retrieve(self, query: str) -> dict:
        vector_retriever = self.vector_store.as_retriever(
            search_kwargs={"k": self.k}
        )
        vector_results = vector_retriever.invoke(query)
        
        self._load_documents_for_bm25()
        bm25_results = self._bm25_retriever.invoke(query)
        
        ensemble = self.get_ensemble_retriever()
        fused_results = ensemble.invoke(query)
        
        return {
            "vector_results": vector_results[:5],
            "bm25_results": bm25_results[:5],
            "fused_results": fused_results[:self.k]
        }