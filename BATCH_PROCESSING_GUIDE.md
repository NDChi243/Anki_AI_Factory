# 🚀 Hướng Dẫn Xử Lý Danh Sách Từ Vựng Lớn Với AI

## 📋 Tổng Quan

Module **Batch Processor** cho phép bạn paste danh sách **hàng trăm đến hàng nghìn từ vựng** và để AI xử lý tuần tự, thông minh. AI sẽ:

1. **Làm giàu từng từ**: Điền đầy đủ nghĩa, phát âm (furigana/pinyin), cấp độ (JLPT/HSK), chủ đề (topic), và 2 ví dụ có hồn
2. **Tự động tổ chức deck**: Đề xuất và tạo Parent Deck + Sub Decks theo chủ đề, cấp độ
3. **Chống trùng lặp**: Tự động lọc bỏ từ đã có trong deck hiện tại

---

## 🧠 Chiến Lược Xử Lý

### Kiến Trúc 2 Tầng (Two-Pass AI)

```
┌─────────────────────────────────────────────────┐
│           PASS 1: BATCH PROCESSING               │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │Batch1│→│Batch2│→│Batch3│→│BatchN│        │
│  │40 từ │  │40 từ │  │40 từ │  │...   │        │
│  └──────┘  └──────┘  └──────┘  └──────┘        │
│     ↓         ↓         ↓         ↓              │
│  Cache    Rate Limit  Retry    Dedup            │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│           PASS 2: DECK ORGANIZER                 │
│  AI phân tích toàn bộ từ → Đề xuất:             │
│  📁 Tiếng Nhật Giao Tiếp                       │
│    ├── Chào Hỏi & Gặp Gỡ (25 từ)               │
│    ├── Ẩm Thực & Nhà Hàng (30 từ)              │
│    ├── Công Việc & Văn Phòng (35 từ)           │
│    └── Du Lịch & Di Chuyển (28 từ)             │
│  📁 Tiếng Nhật Học Thuật                       │
│    ├── N5 - Cơ Bản (40 từ)                     │
│    └── N4 - Sơ Cấp (35 từ)                     │
└─────────────────────────────────────────────────┘
```

### Smart Chunking

Thay vì cắt theo ký tự, module nhóm từ **theo ngữ nghĩa**:
- Nhóm theo cấp độ (N5→N1, HSK1→HSK6)
- Trong cùng cấp độ: nhóm theo độ dài từ
- Đảm bảo mỗi batch có độ đa dạng topic

### Token Optimization

| Cơ chế | Mô tả |
|---------|-------|
| **Batch size limit** | 30-50 từ/batch (có thể tùy chỉnh) |
| **Existing words** | Gửi danh sách từ đã có (giới hạn 1500) để AI tránh trùng |
| **Cache 14 ngày** | Mỗi batch được cache riêng, không gọi lại nếu không đổi |
| **Rate limiting** | Delay 1.5s giữa các batch |
| **Retry + backoff** | Tối đa 3 lần retry với exponential backoff |

### Chất Lượng Được Đảm Bảo

- **System prompt chất lượng cao**: AI được hướng dẫn tạo ví dụ "có hồn" — khẩu ngữ tự nhiên + formal
- **Context-aware**: Mỗi batch có context về các batch khác
- **Post-processing**: Lọc trùng, validate fields sau khi AI trả về
- **Fallback parser**: Nếu JSON không chuẩn, dùng `safe_parse_json` để cứu dữ liệu

---

## 💰 Ước Tính Chi Phí

Với **DeepSeek Chat** (rẻ nhất, chất lượng cao):

| Số từ | Số batch | Input Tokens | Output Tokens | Chi phí (USD) | Thời gian |
|-------|----------|-------------|---------------|---------------|-----------|
| 100 | 3 | ~15,000 | ~20,000 | ~$0.008 | ~30s |
| 500 | 13 | ~75,000 | ~100,000 | ~$0.039 | ~2ph |
| 1,000 | 25 | ~150,000 | ~200,000 | ~$0.077 | ~4ph |
| 5,000 | 125 | ~750,000 | ~1,000,000 | ~$0.385 | ~20ph |
| 10,000 | 250 | ~1,500,000 | ~2,000,000 | ~$0.770 | ~40ph |

> 💡 **Tip**: Với 10,000 từ, chi phí chỉ ~$0.77 (khoảng 19,000 VNĐ). Rẻ hơn 1 ly cà phê!

---

## 🎯 Cách Sử Dụng

### Bước 1: Mở Batch Dialog

Trong giao diện chính của AnkiTool, bấm nút **"📋 Batch Từ Vựng"** (màu xanh lá) trong phần AI.

### Bước 2: Paste Danh Sách Từ

Paste danh sách từ vào text area. Hỗ trợ nhiều format:

```
# Format 1: Mỗi dòng 1 từ
食べる
飲む
勉強する

# Format 2: Từ + nghĩa
食べる : ăn
飲む : uống
勉強する : học

# Format 3: Từ + nghĩa + cấp độ
食べる : ăn : N5
飲む : uống : N5
勉強する : học : N4

# Format 4: CSV
食べる, たべる, ăn, N5
飲む, のむ, uống, N5

# Format 5: JSON array
[{"front":"食べる","meaning":"ăn"},{"front":"飲む","meaning":"uống"}]
```

### Bước 3: Cấu Hình

- **Số từ/batch**: 30-50 (mặc định 40). Nhỏ hơn = chất lượng cao hơn nhưng chậm hơn.
- **Yêu cầu thêm**: Hướng dẫn bổ sung cho AI (VD: "Chỉ lấy từ N3+, chủ đề kinh doanh")
- **AI tự đề xuất deck**: Bật để AI phân tích và đề xuất cấu trúc Parent/Sub Deck
- **Tự động tạo deck**: Bật để tự động tạo deck trong Anki

### Bước 4: Xử Lý

Bấm **"🚀 Xử Lý Với AI"**. Hệ thống sẽ:
1. Parse danh sách từ
2. Lọc bỏ từ trùng với deck hiện có
3. Chia thành các batch thông minh
4. Gọi AI tuần tự cho từng batch
5. (Tùy chọn) AI phân tích và tổ chức deck
6. (Tùy chọn) Tự động tạo deck trong Anki

### Bước 5: Import

Sau khi xử lý xong, danh sách từ vựng đã được làm giàu sẽ tự động đổ vào "xưởng". Bạn có thể:
- Xem preview từng từ
- Chỉnh sửa trước khi import
- Bấm "Kiểm Định" rồi "Import" như bình thường

---

## 🔧 Cấu Trúc File Mới

```
utils/
├── batch_processor.py    ← Module xử lý batch chính
│   ├── parse_word_list()           Parse danh sách từ
│   ├── smart_group_words()         Nhóm từ thông minh
│   ├── process_large_word_list()   Xử lý batch chính
│   ├── organize_decks_with_ai()    AI tổ chức deck
│   ├── create_decks_from_organization()  Tạo deck trong Anki
│   └── estimate_batch_cost()       Ước tính chi phí

workers/
├── batch_workers.py       ← Background threads
│   ├── BatchProcessThread         Thread xử lý batch
│   └── DeckOrganizerThread        Thread tổ chức deck

ui/
├── batch_dialog.py        ← UI Dialog
│   └── BatchWordListDialog        Dialog paste & xử lý
```

---

## 🛡️ Xử Lý Lỗi & Resilience

| Tình huống | Cách xử lý |
|-----------|-----------|
| **API timeout** | Retry 3 lần với exponential backoff (2s → 4s → 8s) |
| **JSON parse fail** | Fallback parser `safe_parse_json` |
| **Batch lỗi** | Skip batch đó, tiếp tục batch sau |
| **Quá 3 batch lỗi** | Dừng toàn bộ, báo lỗi |
| **User bấm hủy** | Dừng ngay, giữ lại kết quả đã xử lý |
| **Cache hit** | Dùng cache, không gọi API |
| **Deck organizer lỗi** | Fallback: tự nhóm theo topic/level |

---

## 📊 So Sánh: Cũ vs Mới

| Tiêu chí | Cũ (AI Trích Xuất) | Mới (Batch Từ Vựng) |
|----------|-------------------|---------------------|
| Input | Văn bản/đoạn văn | Danh sách từ vựng |
| Số lượng | ~12,000 ký tự | Không giới hạn (hàng nghìn từ) |
| Chunking | Cắt theo ký tự | Nhóm theo ngữ nghĩa |
| Cache | 7 ngày, theo text | 14 ngày, theo batch |
| Deck tổ chức | Không có | AI đề xuất + tự tạo |
| Progress | Cơ bản | Chi tiết từng batch |
| Retry | 2 lần | 3 lần + exponential backoff |

---

## 💡 Tips & Best Practices

1. **Batch size 30-40 từ**: Đây là "sweet spot" — đủ context cho AI nhưng không quá nhiều để giảm chất lượng
2. **Dùng model rẻ cho batch lớn**: `deepseek-chat` hoặc `gpt-4o-mini` cho Pass 1, model mạnh hơn cho Pass 2 nếu cần
3. **Thêm custom instruction**: Hướng dẫn AI về phong cách ví dụ, chủ đề ưu tiên, cấp độ mong muốn
4. **Kiểm tra kết quả trước khi import**: Sau khi xử lý, duyệt qua bảng preview để đảm bảo chất lượng
5. **Cache rất quan trọng**: Nếu cần xử lý lại, cache sẽ giúp tiết kiệm 100% chi phí cho các batch không đổi
