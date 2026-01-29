"""
Script khởi tạo Vector Database từ markdown files
Chạy script này để tạo ChromaDB và chunks file cho RAG system
"""

import os
import sys
from pathlib import Path
from src.chunking.text_chunker import HybridSectionChunker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Kiểm tra môi trường trước khi chạy"""
    print("\n🔍 KIỂM TRA MÔI TRƯỜNG")
    print("="*70)
    
    # Check GEMINI_API_KEY
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        print("❌ GEMINI_API_KEY chưa được cấu hình!")
        print("   Vui lòng set GEMINI_API_KEY trong file .env hoặc environment variables")
        return False
    print(f"✅ GEMINI_API_KEY: {gemini_key[:10]}...")
    
    # Check EMBEDDING_MODEL_NAME
    embedding_model = os.getenv("EMBEDDING_MODEL_NAME", "models/text-embedding-004")
    print(f"✅ EMBEDDING_MODEL_NAME: {embedding_model}")
    
    # Check processed data directory
    processed_data_dir = Path("data/processed_data")
    if not processed_data_dir.exists():
        print(f"❌ Thư mục {processed_data_dir} không tồn tại!")
        return False
    
    # Check markdown files
    md_files = list(processed_data_dir.glob("*.md"))
    if not md_files:
        print(f"❌ Không tìm thấy file .md trong {processed_data_dir}!")
        return False
    
    print(f"✅ Tìm thấy {len(md_files)} file markdown:")
    for md_file in md_files:
        print(f"   - {md_file.name}")
    
    return True

def initialize_database(
    collection_name="knowledge_base",
    persist_directory="data/chroma_db",
    chunk_size=800,
    chunk_overlap=150,
    reset=False
):
    """
    Khởi tạo vector database từ markdown files
    
    Args:
        collection_name: Tên collection trong ChromaDB
        persist_directory: Thư mục lưu ChromaDB
        chunk_size: Kích thước mỗi chunk
        chunk_overlap: Độ overlap giữa các chunks
        reset: Xóa database cũ nếu có
    """
    
    print("\n" + "="*70)
    print("🚀 KHỞI TẠO VECTOR DATABASE")
    print("="*70)
    
    # Check environment
    if not check_environment():
        print("\n❌ Kiểm tra môi trường thất bại!")
        print("   Vui lòng sửa các lỗi trên trước khi tiếp tục.")
        sys.exit(1)
    
    # Initialize chunker
    print(f"\n📦 Khởi tạo HybridSectionChunker...")
    print(f"   - Chunk size: {chunk_size}")
    print(f"   - Chunk overlap: {chunk_overlap}")
    
    chunker = HybridSectionChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    # Get all markdown files
    processed_data_dir = Path("data/processed_data")
    md_files = sorted(processed_data_dir.glob("*.md"))
    
    print(f"\n📚 Xử lý {len(md_files)} file markdown...")
    
    # Process each file
    for idx, md_file in enumerate(md_files, 1):
        print(f"\n{'='*70}")
        print(f"📄 [{idx}/{len(md_files)}] Xử lý: {md_file.name}")
        print(f"{'='*70}")
        
        try:
            chunker.chunk_and_save_to_db(
                md_file_path=str(md_file),
                collection_name=collection_name,
                persist_directory=persist_directory,
                reset=(reset and idx == 1)  # Only reset on first file
            )
            print(f"✅ Hoàn thành: {md_file.name}")
        except Exception as e:
            print(f"❌ Lỗi khi xử lý {md_file.name}: {e}")
            raise
    
    # Verify database
    print(f"\n{'='*70}")
    print("🔍 KIỂM TRA DATABASE")
    print(f"{'='*70}")
    
    db_path = Path(persist_directory)
    chroma_db = db_path / "chroma.sqlite3"
    chunks_file = db_path / f"{collection_name}_chunks.pkl"
    
    if chroma_db.exists():
        size_mb = chroma_db.stat().st_size / (1024 * 1024)
        print(f"✅ ChromaDB: {chroma_db} ({size_mb:.2f} MB)")
    else:
        print(f"❌ ChromaDB không tồn tại: {chroma_db}")
    
    if chunks_file.exists():
        size_mb = chunks_file.stat().st_size / (1024 * 1024)
        print(f"✅ Chunks file: {chunks_file} ({size_mb:.2f} MB)")
    else:
        print(f"❌ Chunks file không tồn tại: {chunks_file}")
    
    print(f"\n{'='*70}")
    print("🎉 HOÀN TẤT KHỞI TẠO DATABASE!")
    print(f"{'='*70}")
    print(f"📊 Tổng kết:")
    print(f"   - Số file đã xử lý: {len(md_files)}")
    print(f"   - Collection: {collection_name}")
    print(f"   - Persist directory: {persist_directory}")
    print(f"\n✅ Bạn có thể chạy API server bằng lệnh:")
    print(f"   uvicorn main:app --host 0.0.0.0 --port 8000")
    print(f"\n✅ Hoặc test chatbot bằng lệnh:")
    print(f"   python cli.py")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Khởi tạo Vector Database cho RAG system")
    parser.add_argument(
        "--collection-name",
        type=str,
        default="knowledge_base",
        help="Tên collection trong ChromaDB (default: knowledge_base)"
    )
    parser.add_argument(
        "--persist-directory",
        type=str,
        default="data/chroma_db",
        help="Thư mục lưu ChromaDB (default: data/chroma_db)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="Kích thước mỗi chunk (default: 800)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=150,
        help="Độ overlap giữa các chunks (default: 150)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Xóa database cũ nếu có"
    )
    
    args = parser.parse_args()
    
    try:
        initialize_database(
            collection_name=args.collection_name,
            persist_directory=args.persist_directory,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            reset=args.reset
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã hủy bởi người dùng")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
