"""
RAG (Retrieval-Augmented Generation) for Medical Guidelines
"""
import logging
import chromadb
from typing import List, Dict, Any, Optional
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class MedicalGuidelineRAG:
    """RAG system for retrieving medical guidelines"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name="medical_guidelines",
                metadata={"description": "Medical guidelines for patient advisories"}
            )
            logger.info("MedicalGuidelineRAG initialized")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}. Using mock mode.")
            self.client = None
            self.collection = None
    
    async def retrieve_guidelines(
        self,
        query: str,
        filters: Optional[Dict] = None,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Retrieve relevant medical guidelines
        
        Args:
            query: Search query
            filters: Optional filters (approved, language, type)
            top_k: Number of results to return
        
        Returns:
            List of guideline dicts with content, metadata
        """
        if not self.collection:
            # Return mock guidelines if ChromaDB not available
            return self._get_mock_guidelines(query, top_k)
        
        try:
            # Build where clause for filters
            where = {}
            if filters:
                if filters.get("approved"):
                    where["approved"] = filters["approved"]
                if filters.get("language"):
                    where["language"] = filters["language"]
                if filters.get("type"):
                    where["type"] = filters["type"]
            
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where if where else None
            )
            
            guidelines = []
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    guideline = {
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else None
                    }
                    guidelines.append(guideline)
            
            return guidelines
            
        except Exception as e:
            logger.error(f"Failed to retrieve guidelines: {e}")
            return self._get_mock_guidelines(query, top_k)
    
    def _get_mock_guidelines(self, query: str, top_k: int) -> List[Dict]:
        """Return mock guidelines when ChromaDB is unavailable"""
        mock_guidelines = [
            {
                "content": "During high air pollution (AQI >150), patients with respiratory conditions should stay indoors, use air purifiers, and follow prescribed medication schedules. Emergency care should be sought if breathing difficulties worsen.",
                "metadata": {"approved": True, "language": "en", "type": "public_health"},
                "distance": 0.1
            },
            {
                "content": "During disease outbreaks, practice good hygiene: wash hands frequently, avoid crowded places, wear masks in public. Seek medical attention if symptoms develop. Follow public health advisories.",
                "metadata": {"approved": True, "language": "en", "type": "public_health"},
                "distance": 0.2
            },
            {
                "content": "During hospital surge periods, non-urgent cases may experience delays. Emergency care remains available 24/7. Patients with urgent symptoms should come immediately.",
                "metadata": {"approved": True, "language": "en", "type": "public_health"},
                "distance": 0.3
            }
        ]
        
        # Filter by query keywords
        filtered = []
        query_lower = query.lower()
        
        for guideline in mock_guidelines:
            content_lower = guideline["content"].lower()
            if any(keyword in content_lower for keyword in query_lower.split()):
                filtered.append(guideline)
        
        return filtered[:top_k] if filtered else mock_guidelines[:top_k]
    
    def add_guideline(self, content: str, metadata: Dict):
        """Add a new guideline to the collection"""
        if not self.collection:
            logger.warning("Cannot add guideline - ChromaDB not available")
            return
        
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[f"guideline_{len(self.collection.get()['ids'])}"]
            )
            logger.info("Guideline added successfully")
        except Exception as e:
            logger.error(f"Failed to add guideline: {e}")

