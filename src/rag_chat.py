"""
RAG Chat với LLM (Google Gemini)
Sử dụng Hybrid Search (BM25 + Semantic) để retrieve context
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.chunking.text_chunker import HybridSectionChunker
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class RAGChat:
    
    def __init__(self, 
                 collection_name="knowledge_base",
                 persist_directory="data/chroma_db",
                 model_name="gemini-2.5-flash-lite",
                 temperature=0.1,
                 top_k=5,
                 bm25_weight=0.6,
                 semantic_weight=0.4):
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.top_k = top_k
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        
        # Khởi tạo chunker (dùng để retrieve)
        self.chunker = HybridSectionChunker(chunk_size=800, chunk_overlap=150)
        
        # Khởi tạo LLM
        print(f"🤖 Khởi tạo {model_name}...")
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            api_key=GEMINI_API_KEY,
            temperature=temperature,
            convert_system_message_to_human=True
        )
        
        # Tạo prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("human", """Bạn là trợ lý AI thông minh, trả lời câu hỏi dựa trên CONTEXT được cung cấp.

NGUYÊN TẮC:
1. CHỈ trả lời dựa trên thông tin trong CONTEXT
2. Nếu CONTEXT không có thông tin → trả lời "Tôi không tìm thấy thông tin này trong tài liệu"
3. Trả lời NGẮN GỌN, CHÍNH XÁC, bằng tiếng Việt
4. Trích dẫn thông tin từ CONTEXT nếu có thể
5. KHÔNG bịa đặt hoặc suy đoán thông tin không có trong CONTEXT

CONTEXT:
{context}

CÂU HỎI: {question}

TRẢ LỜI:"""),
        ])
        
        # Tạo RAG chain
        self.rag_chain = (
            {
                "context": lambda x: self._format_docs(x["docs"]),
                "question": lambda x: x["question"]
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        print(f"✅ RAG Chat sẵn sàng!")
    
    def _format_docs(self, docs):
        if not docs:
            return "Không tìm thấy thông tin liên quan trong tài liệu."
        
        formatted = []
        for i, doc in enumerate(docs, 1):
            header = doc.metadata.get('h2', doc.metadata.get('h1', ''))
            formatted.append(f"--- Đoạn {i} ({header}) ---\n{doc.page_content}")
        return "\n\n".join(formatted)
    
    def retrieve(self, query):
        print(f"\n🔍 Đang retrieve context cho: '{query}'")
        
        try:
            results = self.chunker.query_with_hybrid_search(
                query=query,
                collection_name=self.collection_name,
                persist_directory=self.persist_directory,
                k=self.top_k,
                bm25_weight=self.bm25_weight,
                semantic_weight=self.semantic_weight
            )
            
            print(f"📦 Đã retrieve {len(results)} chunks")
            return results
        except FileNotFoundError as e:
            print(f"❌ Lỗi: {str(e)}")
            raise FileNotFoundError(
                f"Vector database chưa được khởi tạo. "
                f"Vui lòng chạy script khởi tạo database trước. "
                f"Chi tiết: {str(e)}"
            )
        except Exception as e:
            print(f"❌ Lỗi khi retrieve: {str(e)}")
            raise RuntimeError(f"Lỗi khi retrieve context: {str(e)}")
    
    def chat(self, question, verbose=False):
        
        # Validate question
        if not question or not question.strip():
            return "Vui lòng nhập câu hỏi hợp lệ."
        
        try:
            # Retrieve context
            docs = self.retrieve(question)
            
            # Kiểm tra có docs không
            if not docs:
                return "Xin lỗi, tôi không tìm thấy thông tin liên quan trong tài liệu."
            
            # In context nếu verbose
            if verbose:
                print(f"\n{'='*70}")
                print(f"CONTEXT ĐƯỢC RETRIEVE:")
                print(f"{'='*70}")
                for i, doc in enumerate(docs, 1):
                    print(f"\n📄 Chunk {i}:")
                    print(f"   Headers: {doc.metadata.get('h1', '')} / {doc.metadata.get('h2', '')}")
                    print(f"   Content: {doc.page_content[:200]}...")
                    print(f"   {'-'*70}")
            
            # Format context
            context = self._format_docs(docs)
            
            # Đảm bảo context không rỗng
            if not context or not context.strip():
                return "Xin lỗi, không thể tạo context từ tài liệu."
            
            # Generate answer
            print(f"\n💬 Đang generate câu trả lời...")
            answer = self.rag_chain.invoke({
                "docs": docs,
                "question": question
            })
            
            return answer
            
        except FileNotFoundError as e:
            error_msg = (
                "Vector database chưa được khởi tạo. "
                "Vui lòng chạy script khởi tạo database trước khi sử dụng chatbot."
            )
            print(f"❌ {error_msg}")
            return error_msg
            
        except Exception as e:
            error_msg = f"Đã xảy ra lỗi khi xử lý câu hỏi: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg



# ============================================================================
# INTERACTIVE CHAT
# ============================================================================

def interactive_chat():
    rag = RAGChat(
        collection_name="knowledge_base",
        persist_directory="data/chroma_db",
        model_name="gemini-2.5-flash-lite",
        temperature=0.1,
        top_k=10,
        bm25_weight=0.5,
        semantic_weight=0.5
    )
    
    print(f"\n{'='*70}")
    print(f"🤖 RAG CHAT - Hỏi đáp về Doanh nhân")
    print(f"{'='*70}")
    print(f"Nhập 'quit' hoặc 'exit' để thoát")
    print(f"Nhập 'verbose' để bật/tắt hiển thị context")
    print(f"{'='*70}\n")
    
    verbose = False
    
    while True:
        question = input("❓ Câu hỏi: ").strip()
        
        if question.lower() in ['quit', 'exit', 'thoát']:
            print("👋 Tạm biệt!")
            break
        
        if question.lower() == 'verbose':
            verbose = not verbose
            print(f"✅ Verbose mode: {'ON' if verbose else 'OFF'}")
            continue
        
        if not question:
            continue
        
        try:
            answer = rag.chat(question, verbose=verbose)
            print(f"\n💡 TRẢ LỜI: {answer}\n")
        except Exception as e:
            print(f"❌ Lỗi: {e}\n")


if __name__ == "__main__":
    interactive_chat()
