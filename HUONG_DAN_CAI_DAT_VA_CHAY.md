# Hướng dẫn cài đặt và chạy

Tài liệu này hướng dẫn cài đặt môi trường và chạy project `Lab 3: Chatbot vs ReAct Agent`.

## 1. Yêu cầu

- Python 3.10 trở lên.
- `pip` và `venv`.
- API key OpenAI hoặc Gemini nếu chạy provider cloud.
- Nếu chạy local model, cần file model `.gguf` và máy có đủ RAM/CPU.

## 2. Tạo môi trường ảo

Chạy các lệnh sau tại thư mục gốc của project:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Trên Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 3. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

Lưu ý: `llama-cpp-python` dùng cho local model có thể cần compiler. Trên macOS, nếu cài đặt lỗi do thiếu công cụ build, cài Xcode Command Line Tools:

```bash
xcode-select --install
```

## 4. Cấu hình biến môi trường

Tạo file `.env` từ file mẫu:

```bash
cp .env.example .env
```

Mở `.env` và điền provider muốn dùng.

### Chạy bằng OpenAI

```env
OPENAI_API_KEY=sk-...
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
```

### Chạy bằng Gemini

```env
GEMINI_API_KEY=...
DEFAULT_PROVIDER=google
DEFAULT_MODEL=gemini-1.5-flash
```

### Chạy bằng local model

Tải model `Phi-3-mini-4k-instruct-q4.gguf` từ Hugging Face:

```text
https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
```

Đặt file model vào thư mục `models/`, ví dụ:

```text
models/Phi-3-mini-4k-instruct-q4.gguf
```

Cập nhật `.env`:

```env
DEFAULT_PROVIDER=local
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

## 5. Chạy bằng command line

Chạy ReAct Agent với câu hỏi mặc định:

```bash
python main.py --mode agent
```

Chạy Chatbot baseline:

```bash
python main.py --mode chatbot
```

Truyền câu hỏi riêng:

```bash
python main.py --mode agent -q "Toi bi dau nguc, kho tho. Tim bac si phu hop."
```

Chọn provider trực tiếp từ command line:

```bash
python main.py --mode agent --provider openai
python main.py --mode agent --provider google
python main.py --mode agent --provider local
```

Chạy chế độ hội thoại nhiều lượt:

```bash
python main.py --chat
```

Trong chế độ hội thoại, gõ `exit`, `quit`, `thoat`, `thoát` hoặc `q` để thoát.

## 6. Chạy giao diện Streamlit

```bash
streamlit run app.py
```

Sau khi chạy, Streamlit sẽ in ra URL local, thường là:

```text
http://localhost:8501
```

Trong giao diện, có thể chọn:

- `agent`: dùng ReAct Agent có tool và trace.
- `chatbot`: dùng chatbot baseline.
- Provider: theo `.env`, OpenAI, Gemini hoặc local.

## 7. Chạy experiment và test

Chạy bộ so sánh Chatbot vs ReAct Agent:

```bash
python scripts/run_experiments.py
```

Chạy experiment với provider cụ thể:

```bash
python scripts/run_experiments.py --provider google
```

Chạy test:

```bash
pytest
```

Nếu `pytest` không được tìm thấy, chạy:

```bash
python -m pytest
```

## 8. Log và telemetry

Project ghi log/telemetry vào thư mục `logs/`. Có thể phân tích log bằng:

```bash
python scripts/parse_logs.py
```

Trong CLI và Streamlit, cuối mỗi phiên sẽ có thông tin:

- Số request.
- Tổng token.
- Tổng latency.
- Chi phí ước tính.

## 9. Lỗi thường gặp

### Thiếu API key

Nếu gặp lỗi dạng:

```text
OPENAI_API_KEY chưa được cấu hình trong .env
GEMINI_API_KEY chưa được cấu hình trong .env
```

Hãy kiểm tra lại file `.env` và đảm bảo `DEFAULT_PROVIDER` khớp với API key đã điền.

### Không tìm thấy local model

Nếu gặp lỗi dạng:

```text
Model file not found
```

Hãy kiểm tra `LOCAL_MODEL_PATH` trong `.env` và đảm bảo file `.gguf` tồn tại đúng đường dẫn.

### Lệnh import module bị lỗi

Đảm bảo đang chạy lệnh từ thư mục gốc của project, nơi có file `main.py`, `app.py` và `requirements.txt`.

### Muốn chạy lại từ môi trường sạch

Lệnh dưới đây xoá môi trường ảo `.venv` hiện tại rồi tạo lại từ đầu:

```bash
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
