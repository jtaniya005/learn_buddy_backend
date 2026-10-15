import os
# Workarounds for PyTorch DLL conflict and CPU only usage
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from app.core.config import settings

class RAGService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RAGService, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.api_key = settings.PINECONE_API_KEY or "pcsk_qzvqg_45k7FnGvmyPFV7NkHpXCHCFnuRixV1Vddtt7zFSNszwpMDQK7UB2n61LfYaD5LQ"
        self.index_name = settings.PINECONE_INDEX_NAME or "learn-buddy"
        
        print("RAGService: Connecting to Pinecone...")
        self.pc = Pinecone(api_key=self.api_key)
        self.index = self.pc.Index(self.index_name)
        
        print("RAGService: Loading local SentenceTransformer model (all-mpnet-base-v2)...")
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self._initialized = True
        print("RAGService: Initialized successfully!")

    def query_namespace(self, query: str, namespace: str, top_k: int = 3) -> list[dict]:
        """
        Embeds the query and searches inside the specified Pinecone namespace.
        Available namespaces: 'careers', 'colleges', 'syllabus', 'faqs', 'conversations'
        """
        try:
            # Generate embedding
            query_vector = self.model.encode(query).tolist()
            
            # Query Pinecone index
            results = self.index.query(
                namespace=namespace,
                vector=query_vector,
                top_k=top_k,
                include_metadata=True
            )
            
            # Format output matches
            matches = []
            for match in results.matches:
                matches.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            return matches
        except Exception as e:
            print(f"RAGService Error querying namespace '{namespace}': {e}")
            return []

# Create a singleton instance for global use
rag_service = RAGService()
