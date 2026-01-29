# 🚀 HƯỚNG DẪN CHẠY ỨNG DỤNG TRÊN LOCALHOST:8000

## 📋 YÊU CẦU HỆ THỐNG

- **Docker Desktop** đã cài đặt và đang chạy
- **Git** (để clone project)
- **Gemini API Key** (lấy miễn phí tại: https://aistudio.google.com/app/apikey)

---

## ⚡ CÁCH 1: CHẠY VỚI DOCKER (KHUYẾN NGHỊ - ĐƠN GIẢN NHẤT)

### Bước 1: Tạo file `.env`

Tạo file `.env` trong thư mục gốc của project với nội dung sau:

```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# Embedding Model Configuration
EMBEDDING_MODEL_NAME=models/text-embedding-004
DIMENSION_OF_MODEL=768

# Database (Không cần thay đổi - Docker tự động setup)
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=rag_password
POSTGRES_DB=rag_db
DATABASE_URL=postgresql://rag_user:rag_password@postgres:5432/rag_db

# Redis (Không cần thay đổi)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://redis:6379/0
```

**⚠️ QUAN TRỌNG**: Thay `your_gemini_api_key_here` bằng API key thật của bạn!

### Bước 2: Khởi động ứng dụng

Mở **Command Prompt** hoặc **PowerShell** tại thư mục project và chạy:

```bash
docker-compose up -d --build
```

**Giải thích lệnh**:
- `docker-compose up`: Khởi động các services
- `-d`: Chạy ở chế độ background (detached)
- `--build`: Build lại Docker images

### Bước 3: Kiểm tra services đã chạy

```bash
docker-compose ps
```

Bạn sẽ thấy 4 services đang chạy:
- ✅ `rag_postgres` - Database (port 5433)
- ✅ `rag_redis` - Queue system (port 6379)
- ✅ `rag_api` - FastAPI server (port 8000)
- ✅ `rag_worker_process` - Background worker

### Bước 4: Truy cập ứng dụng

Mở trình duyệt và truy cập:

- **🌐 API Documentation (Swagger UI)**: http://localhost:8000/docs
- **🎨 Web UI**: http://localhost:8000/ui
- **📊 API Info**: http://localhost:8000/
- **💚 Health Check**: http://localhost:8000/health

### Bước 5: Test API

Thử upload file HTML để test:

```bash
curl -X POST "http://localhost:8000/api/v1/process" ^
  -H "Content-Type: multipart/form-data" ^
  -F "files=@test.txt" ^
  -F "chunk_size=800" ^
  -F "chunk_overlap=150"
```

**Hoặc** sử dụng Swagger UI tại http://localhost:8000/docs để test trực tiếp!

---

## 🛠️ CÁCH 2: CHẠY LOCAL (KHÔNG DÙNG DOCKER)

### Bước 1: Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

### Bước 2: Khởi động PostgreSQL và Redis bằng Docker

```bash
docker-compose up -d postgres redis
```

### Bước 3: Tạo file `.env` (giống Cách 1)

Nhưng thay đổi `DATABASE_URL`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
EMBEDDING_MODEL_NAME=models/text-embedding-004
DIMENSION_OF_MODEL=768

# Database - Chú ý port 5433 (không phải 5432)
DATABASE_URL=postgresql://rag_user:rag_password@localhost:5433/rag_db

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Bước 4: Chạy API server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

### Bước 5: Chạy Worker (Terminal mới)

Mở terminal mới và chạy:

```bash
rq worker process --url redis://localhost:6379/0
```

### Bước 6: Truy cập ứng dụng

Giống như Cách 1, truy cập: http://localhost:8000/docs

---

## 🔧 CÁC LỆNH HỮU ÍCH

### Xem logs của tất cả services

```bash
docker-compose logs -f
```

### Xem logs của service cụ thể

```bash
# API logs
docker-compose logs -f api

# Worker logs
docker-compose logs -f worker_process

# Database logs
docker-compose logs -f postgres
```

### Dừng ứng dụng

```bash
docker-compose down
```

### Dừng và xóa toàn bộ data

```bash
docker-compose down -v
```

### Khởi động lại services

```bash
docker-compose restart
```

### Khởi động lại service cụ thể

```bash
docker-compose restart api
docker-compose restart worker_process
```

---

## 🐛 XỬ LÝ LỖI THƯỜNG GẶP

### ❌ Lỗi: "Port 8000 already in use"

**Nguyên nhân**: Port 8000 đang được sử dụng bởi ứng dụng khác

**Giải pháp**:

1. Tìm và tắt ứng dụng đang dùng port 8000
2. Hoặc đổi port trong `docker-compose.yml`:

```yaml
api:
  ports:
    - "8001:8000"  # Đổi từ 8000 sang 8001
```

Sau đó truy cập: http://localhost:8001

### ❌ Lỗi: "GEMINI_API_KEY not found"

**Nguyên nhân**: Chưa tạo file `.env` hoặc chưa điền API key

**Giải pháp**:
1. Tạo file `.env` theo hướng dẫn ở Bước 1
2. Lấy API key tại: https://aistudio.google.com/app/apikey
3. Restart services: `docker-compose restart`

### ❌ Lỗi: "Connection refused" khi kết nối database

**Nguyên nhân**: PostgreSQL chưa sẵn sàng

**Giải pháp**:
```bash
# Kiểm tra PostgreSQL đã chạy chưa
docker-compose ps postgres

# Xem logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### ❌ Lỗi: "Worker not processing jobs"

**Nguyên nhân**: Worker chưa chạy hoặc bị lỗi

**Giải pháp**:
```bash
# Xem worker logs
docker-compose logs -f worker_process

# Restart worker
docker-compose restart worker_process
```

### ❌ Lỗi: "Docker daemon not running"

**Nguyên nhân**: Docker Desktop chưa khởi động

**Giải pháp**:
1. Mở **Docker Desktop**
2. Đợi Docker khởi động hoàn tất
3. Chạy lại lệnh `docker-compose up -d --build`

---

## 📊 KIỂM TRA HỆ THỐNG

### 1. Kiểm tra API hoạt động

```bash
curl http://localhost:8000/health
```

Kết quả mong đợi:
```json
{
  "status": "healthy",
  "service": "RAG Service"
}
```

### 2. Kiểm tra Database

```bash
docker exec rag_postgres psql -U rag_user -d rag_db -c "SELECT COUNT(*) FROM documents;"
```

### 3. Kiểm tra Redis Queue

```bash
docker exec rag_redis redis-cli LLEN rq:queue:process
```

### 4. Kiểm tra tất cả containers

```bash
docker-compose ps
```

Tất cả services phải có trạng thái **Up** hoặc **Up (healthy)**

---

## 🎯 SỬ DỤNG API

### 1. Upload và xử lý file

Truy cập: http://localhost:8000/docs

Tìm endpoint **POST /api/v1/process** và:
1. Click **"Try it out"**
2. Upload file HTML
3. Điều chỉnh `chunk_size` và `chunk_overlap` (tùy chọn)
4. Click **"Execute"**

### 2. Tìm kiếm tài liệu

Endpoint: **POST /api/v1/search**

```json
{
  "query": "Hồ Chí Minh sinh năm nào",
  "top_k": 5
}
```

### 3. Chat với RAG

Endpoint: **POST /api/v1/chat**

```json
{
  "question": "Hồ Chí Minh sinh năm nào",
  "top_k": 10
}
```

### 4. Kiểm tra trạng thái job

Endpoint: **GET /api/v1/jobs/{job_id}/status**

---

## 📁 CẤU TRÚC THƯ MỤC

```
WikiChatbot-RAG/
├── app/                    # Source code chính
│   ├── api/               # API routes & schemas
│   ├── database/          # Database models & connection
│   ├── services/          # Business logic
│   ├── workers/           # Background workers
│   ├── config.py          # Configuration
│   └── main.py            # FastAPI app entry point
├── data/                  # Data storage
│   └── temp/             # Temporary upload files
├── migrations/            # Database migrations
├── docker-compose.yml     # Docker orchestration
├── Dockerfile            # Docker image definition
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (TỰ TẠO)
└── README.md             # Documentation
```

---

## 🎉 HOÀN TẤT!

Bây giờ bạn đã có:
- ✅ API server chạy tại: http://localhost:8000
- ✅ Swagger UI tại: http://localhost:8000/docs
- ✅ Web UI tại: http://localhost:8000/ui
- ✅ PostgreSQL với pgvector
- ✅ Redis Queue với background worker
- ✅ Hệ thống RAG hoàn chỉnh

## 📞 HỖ TRỢ

Nếu gặp vấn đề:
1. ✅ Kiểm tra logs: `docker-compose logs -f`
2. ✅ Kiểm tra `.env` có đầy đủ thông tin
3. ✅ Đảm bảo Docker Desktop đang chạy
4. ✅ Restart services: `docker-compose restart`
5. ✅ Xem phần "Xử lý lỗi thường gặp" ở trên

---

**Chúc bạn sử dụng thành công! 🚀**
