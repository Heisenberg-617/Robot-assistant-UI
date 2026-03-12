import json
import os
from typing import List
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


class RAGService:
    def __init__(self, db_path: str = "./vector_db", model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.db_path = db_path
        # Using HuggingFace embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        self.vector_db = None
        if os.path.exists(db_path):
            self.vector_db = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embeddings
            )

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize text to proper UTF-8 and fix common encoding issues."""
        if not text:
            return ""
        
        # Normalize common Windows-1252 to UTF-8 characters
        replacements = {
            "Ã©": "é",
            "Ã¨": "è",
            "Ã": "à",
            "â€™": "'",
            "â€“": "-",
            "â€˜": "'",
            "â€œ": '"',
            "â€": '"',
            "â€¯": " ",  # thin space
            "Â": "",      # stray character often appearing
        }

        # Decode & replace
        text = text.encode("utf-8", "ignore").decode("utf-8")
        for wrong, right in replacements.items():
            text = text.replace(wrong, right)
        
        # Replace other common unicode spaces and dashes
        text = text.replace('\u2009', ' ')  # thin space
        text = text.replace('\u202f', ' ')  # narrow no-break space
        text = text.replace('\u2013', '-')  # en dash
        text = text.replace('\u2019', "'")  # right single quote
        text = text.replace('\u201c', '"')  # left double quote
        text = text.replace('\u201d', '"')  # right double quote
        
        # Strip extra spaces
        text = " ".join(text.split())
        
        return text

    def ingest_files(self, file_paths: List[str]):
        """Takes a list of .txt, .pdf, and .json paths, chunks them, and stores them in the vector DB."""
        all_docs = []

        for file_path in file_paths:
            docs = []

            if file_path.endswith(".pdf"):
                loader = PyMuPDFLoader(file_path)
                docs = loader.load()
            elif file_path.endswith(".txt"):
                loader = TextLoader(file_path, encoding="utf-8")
                docs = loader.load()
            elif file_path.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data_list = json.load(f)
                for data in data_list:
                    docs.append(
                        Document(
                            page_content=data.get("content", ""),
                            metadata={
                                "source": file_path,
                                "url": data.get("url", "")
                            }
                        )
                    )
            else:
                continue

            # Clean text
            for doc in docs:
                doc.page_content = doc.page_content.strip()
                doc.page_content = RAGService.clean_text(doc.page_content)

            all_docs.extend(docs)

        # Chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        chunks = text_splitter.split_documents(all_docs)

        # Embedding + storage
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