import os
from typing import List
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

class RAGService:
    
    def __init__(self, db_path: str = "./vector_db", model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.db_path = db_path
        # Using OpenAI embeddings by default; can be swapped for HuggingFace
        self.embeddings = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
        
        self.vector_db = None
        if os.path.exists(db_path):
            self.vector_db = Chroma(
                persist_directory=self.db_path, 
                embedding_function=self.embeddings
            )

    def ingest_files(self, file_paths: List[str]):
        """Takes a list of .txt and .pdf paths, chunks them, and stores in DB."""
        all_docs = []
        
        for file_path in file_paths:
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith('.txt'):
                loader = TextLoader(file_path)
            else:
                continue
            all_docs.extend(loader.load())

        # 1. Chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(all_docs)

        # 2. Embedding & Storage
        self.vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.db_path
        )
        print(f"Successfully indexed {len(chunks)} chunks.")

    def search(self, query: str, k: int = 3) -> List[Document]:
            """Embeds the query and returns the top k relevant chunks."""
            if not self.vector_db:
                raise ValueError("Vector database not initialized.")
            
            return self.vector_db.similarity_search(query, k=k)