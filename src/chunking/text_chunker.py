from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
import os
import shutil
import pickle

import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")


class HybridSectionChunker:
    
    def __init__(self, chunk_size=1000, chunk_overlap=100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 1. Section splitter - tách theo markdown headers
        self.headers_to_split_on = [
            ("#", "h1"),
            ("##", "h2"),
            # ("###", "h3"),
            # ("####", "h4")
        ]
        self.section_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=True
        )
        
        # 2. Recursive splitter - tách sections lớn
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL_NAME,
            api_key=GEMINI_API_KEY
        )
    
    def chunk_and_save_to_db(self, md_file_path, collection_name="knowledge_base", 
                             persist_directory="data/chroma_db", reset=False):
        
        print(f"\n🔪 HYBRID SECTION CHUNKING")
        print(f"="*70)
        print(f"📄 File: {md_file_path}")
        print(f"📏 Chunk size: {self.chunk_size}")
        print(f"🔗 Chunk overlap: {self.chunk_overlap}")
        
        if reset and os.path.exists(persist_directory):
            print(f"🗑️  Xóa DB cũ...")
            shutil.rmtree(persist_directory)
        
        os.makedirs(persist_directory, exist_ok=True)
        
        # Load document
        with open(md_file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Step 1: Tách theo headers
        print(f"\n📑 Bước 1: Tách theo markdown headers...")
        section_docs = self.section_splitter.split_text(text)
        print(f"→ {len(section_docs)} sections")
        
        # Step 2: Recursive split cho sections lớn
        print(f"🔨 Bước 2: Recursive split cho sections lớn...")
        final_chunks = []
        
        for idx, section_doc in enumerate(section_docs):
            section_doc.metadata.update({
                "source": md_file_path,
                "section_id": idx,
                "document": os.path.basename(md_file_path).replace('.md', '')
            })
            
            # Nếu section quá lớn, tách tiếp
            if len(section_doc.page_content) > self.chunk_size:
                sub_chunks = self.recursive_splitter.split_documents([section_doc])
                
                # Thêm sub_chunk_id
                for sub_idx, sub_chunk in enumerate(sub_chunks):
                    sub_chunk.metadata.update({
                        "sub_chunk_id": sub_idx,
                        "total_sub_chunks": len(sub_chunks)
                    })
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(section_doc)
        
        print(f"   → {len(final_chunks)} chunks cuối cùng")
        
        # Step 3: Lưu vào Chroma (cho semantic search)
        print(f"\n💾 Bước 3: Lưu vào Chroma DB...")
        Chroma.from_documents(
            documents=final_chunks,
            embedding=self.embeddings,
            collection_name=collection_name,
            persist_directory=persist_directory
        )
        
        # Step 4: Lưu chunks vào pickle (cho BM25)
        chunks_file = os.path.join(persist_directory, f"{collection_name}_chunks.pkl")
        with open(chunks_file, 'wb') as f:
            pickle.dump(final_chunks, f)
        print(f"💾 Đã lưu chunks vào {chunks_file}")
        
        print(f"\n✅ HOÀN TẤT!")
        print(f"📊 {len(section_docs)} sections → {len(final_chunks)} chunks")
        print(f"💾 Lưu tại: {persist_directory}")
    
    def query_with_hybrid_search(self, query, collection_name="knowledge_base", 
                                  persist_directory="data/chroma_db", k=5,
                                  bm25_weight=0.5, semantic_weight=0.5):
        
        print(f"\n🔍 HYBRID SEARCH QUERY")
        print(f"="*70)
        print(f"❓ Query: {query}")
        print(f"🎯 Top K: {k}")
        print(f"⚖️ Weights: BM25={bm25_weight}, Semantic={semantic_weight}")
        
        # Load vectorstore
        print(f"\n📂 Đang load vectorstore...")
        vectorstore = Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        
        # Load chunks cho BM25
        chunks_file = os.path.join(persist_directory, f"{collection_name}_chunks.pkl")
        with open(chunks_file, 'rb') as f:
            chunks = pickle.load(f)
        print(f"📂 Đã load {len(chunks)} chunks")
        
        # Tạo BM25 retriever
        print(f"🔤 Khởi tạo BM25 retriever...")
        bm25_retriever = BM25Retriever.from_documents(chunks)
        bm25_retriever.k = k
        
        # Tạo Semantic retriever
        print(f"🧠 Khởi tạo Semantic retriever...")
        semantic_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        
        # Ensemble retriever
        print(f"🔀 Tạo Ensemble retriever...")
        hybrid_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, semantic_retriever],
            weights=[bm25_weight, semantic_weight]
        )
        
        # Query
        print(f"\n🔎 Đang search...")
        results = hybrid_retriever.invoke(query)
        
        print(f"✅ Tìm thấy {len(results)} kết quả!")
        
        return results[:k]

