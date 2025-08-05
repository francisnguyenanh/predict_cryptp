# 🚀 CRYPTO PREDICTION APP - HƯỚNG DẪN SỬ DỤNG

## 📋 Tính năng chính

### 1. 📈 DỰ ĐOÁN MUA
- Phân tích đa khung thời gian (60m, 4h, 1d)
- Tìm coin tốt nhất để mua vào
- Đưa ra mức giá Entry, TP1, TP2, SL
- Tỷ lệ chính xác dự đoán

### 2. 📉 DỰ ĐOÁN BÁN/HOLD
- Phân tích xu hướng coin đang nắm giữ
- Khuyến nghị HOLD hay BÁN
- Mức giá mục tiêu nếu tiếp tục tăng
- Phân tích trên 3 khung thời gian (60m, 1h, 4h)

## 🖱️ Cách sử dụng (Chạy thủ công)

### Cách 1: Menu tương tác
```bash
python3 auto_runner.py
```
- Chọn 1: Dự đoán MUA
- Chọn 2: Dự đoán BÁN/HOLD
- Chọn 3: Thoát

### Cách 2: Command line
```bash
# Phân tích mua tất cả khung thời gian
python3 auto_runner.py --multi

# Phân tích mua khung cụ thể
python3 auto_runner.py --60m
python3 auto_runner.py --4h  
python3 auto_runner.py --1d

# Chạy một lần (legacy)
python3 auto_runner.py --once
```

### Cách 3: File batch (macOS)
- **`run_analysis.command`**: Menu tương tác đầy đủ
- **`analyze_sell.command`**: Phân tích bán/hold nhanh

## 🎯 Cách đọc kết quả

### Dự đoán MUA:
```
📈 60M (60 minutes)
Coin: XRPJPY
Giá vào lệnh: 454.500000
SL: 451.868522      (Stop Loss - mức cắt lỗ)
TP1: 459.412092     (Take Profit 1 - chốt lời lần 1)
TP2: 462.394434     (Take Profit 2 - chốt lời lần 2)
Tỷ lệ chính xác: 33.3%
```

### Dự đoán BÁN/HOLD:
```
Khung    Xu hướng        Khuyến nghị          Mục tiêu     Tỷ lệ    Độ chính xác
60m      📈 TĂNG MẠNH     🔒 HOLD - Tiếp tục   462.058     +1.76%   33.3%
1h       📈 TĂNG MẠNH     🔒 HOLD - Tiếp tục   480.297     +5.77%   33.3%
4h       📈 TĂNG MẠNH     🔒 HOLD - Tiếp tục   480.297     +5.77%   33.3%
```

## 📊 Các coin được hỗ trợ
- XRPJPY
- XLMJPY  
- ADAJPY
- SUIJPY
- LINKJPY
- SOLJPY
- ETHJPY

## ⚠️ Lưu ý quan trọng
- **Chạy thủ công:** App không có timer tự động, bạn cần chạy thủ công mỗi lần
- Đây chỉ là công cụ hỗ trợ phân tích, không phải lời khuyên đầu tư
- Luôn cân nhắc rủi ro trước khi đầu tư
- Sử dụng Stop Loss để bảo vệ vốn
- Tỷ lệ chính xác dựa trên dữ liệu lịch sử, không đảm bảo kết quả tương lai

## 🔧 Yêu cầu hệ thống
- Python 3.8+
- Internet connection (để lấy dữ liệu từ Binance API)
- Các package: pandas, numpy, requests, talib, colorama

## 📈 Cập nhật mới nhất
- ✅ Loại bỏ timer/schedule - chỉ chạy thủ công
- ✅ Điều chỉnh tỷ lệ TP/SL phù hợp với từng trend
- ✅ STRONG_UP: TP cao hơn để tận dụng momentum
- ✅ Trend yếu: TP thấp hơn, thận trọng
- ✅ Menu tương tác thân thiện
- ✅ Phân tích hold/bán cho coin đang nắm giữ
