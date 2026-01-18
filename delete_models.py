"""Script để xóa tất cả embedding models đã tải"""

from huggingface_hub import scan_cache_dir
import shutil
import os
from pathlib import Path

def delete_all_embedding_models():
    print("🔍 Đang quét cache...")
    
    # Tìm cache directory
    cache_home = os.environ.get("HF_HOME") or os.path.join(Path.home(), ".cache", "huggingface")
    hub_cache = os.path.join(cache_home, "hub")
    
    if not os.path.exists(hub_cache):
        print("✅ Không có model nào trong cache")
        return
    
    try:
        cache_info = scan_cache_dir()
        
        print("\n📦 Models trong cache:")
        print("="*60)
        
        total_size = 0
        for repo in cache_info.repos:
            print(f"  - {repo.repo_id}")
            print(f"    Size: {repo.size_on_disk_str}")
            total_size += repo.size_on_disk
        
        print("="*60)
        print(f"Tổng dung lượng: {total_size / (1024**3):.2f} GB")
        print(f"📁 Cache location: {hub_cache}")
        
        # Confirm trước khi xóa
        confirm = input("\n⚠️  Bạn có chắc muốn XÓA TẤT CẢ? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ Hủy bỏ")
            return
        
        print("\n🗑️  Đang xóa toàn bộ cache folder...")
        
        # Xóa trực tiếp folder (cách hiệu quả nhất)
        shutil.rmtree(hub_cache, ignore_errors=True)
        
        print(f"✅ Đã xóa toàn bộ cache!")
        print(f"✅ Giải phóng {total_size / (1024**3):.2f} GB")
        
        # Verify
        if not os.path.exists(hub_cache):
            print("✅ Xác nhận: Cache folder đã bị xóa hoàn toàn")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        print(f"\n💡 Thử xóa thủ công:")
        print(f"Windows PowerShell: Remove-Item -Recurse -Force '{hub_cache}'")
        print(f"Git Bash: rm -rf '{hub_cache}'")

if __name__ == "__main__":
    delete_all_embedding_models()
