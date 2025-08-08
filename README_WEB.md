# Crypto Prediction Web App

Ứng dụng web dự đoán cryptocurrency với giao diện Bootstrap đẹp mắt và tính năng phân tích kỹ thuật nâng cao.

## 🚀 Tính năng

### 📈 Dự đoán MUA
- Phân tích đa khung thời gian (60m, 4h, 1d)
- Tìm kiếm coin có tín hiệu mua mạnh
- Tính toán Take Profit (TP1, TP2) và Stop Loss tự động
- Đánh giá xác suất thành công và chất lượng entry

### 📉 Phân tích BÁN
- Phân tích xu hướng coin đang nắm giữ
- Khuyến nghị Hold/Sell/Wait
- Dự báo mức giá tiếp theo
- Quản lý rủi ro tối ưu

### 🎯 Chỉ báo kỹ thuật
- **RSI** (Relative Strength Index)
- **MACD** (Moving Average Convergence Divergence)
- **Ichimoku Cloud** (Tenkan-sen, Kijun-sen, Senkou Span)
- **Fibonacci Retracement**
- **Bollinger Bands**
- **Stochastic Oscillator**
- **ADX** (Average Directional Index)
- **Volume Analysis** with OBV
- **Candlestick Patterns**

## 🛠️ Cài đặt

### Yêu cầu hệ thống
- Python 3.8+
- Kết nối internet (để lấy dữ liệu từ Binance API)

### Cài đặt tự động (Windows)
```bash
run_web.bat
```

### Cài đặt tự động (Linux/Mac)
```bash
chmod +x run_web.sh
./run_web.sh
```

### Cài đặt thủ công
1. Clone repository
```bash
git clone <repository-url>
cd predict_cryptp
```

2. Tạo virtual environment
```bash
python -m venv .venv
```

3. Kích hoạt virtual environment
- Windows: `.venv\Scripts\activate`
- Linux/Mac: `source .venv/bin/activate`

4. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

5. Chạy ứng dụng
```bash
python app.py
```

6. Mở trình duyệt và truy cập: `http://localhost:5000`

## 📱 Giao diện

### Trang chủ
- Giới thiệu tính năng
- Danh sách coin được hỗ trợ
- Thống kê hệ thống

### Dự đoán MUA
- Giao diện phân tích real-time
- Hiển thị kết quả theo từng khung thời gian
- Thông tin chi tiết về entry, TP, SL

### Phân tích BÁN
- Chọn coin để phân tích
- Bảng so sánh xu hướng
- Khuyến nghị tổng hợp

## 🔧 Cấu hình

### Danh sách coin hỗ trợ
Được định nghĩa trong `enhanced_app_v2.py`:
```python
self.pairs = ['XRPJPY', 'XLMJPY', 'ADAJPY', 'SUIJPY', 'LINKJPY', 'SOLJPY', 'ETHJPY']
```

### Khung thời gian đầu tư
```python
self.investment_types = {
    '60m': {'timeframe': '15m', 'analysis_timeframes': ['15m', '1h'], 'hold_duration': '60 minutes'},
    '4h': {'timeframe': '1h', 'analysis_timeframes': ['1h', '4h'], 'hold_duration': '4 hours'}, 
    '1d': {'timeframe': '4h', 'analysis_timeframes': ['4h', '1d'], 'hold_duration': '1 day'}
}
```

## 📊 API Endpoints

### GET `/`
Trang chủ

### GET `/predict_buy`
Trang dự đoán mua

### POST `/api/predict_buy`
API phân tích dự đoán mua
- Response: Danh sách coin được recommend theo khung thời gian

### GET `/analyze_sell`
Trang phân tích bán

### POST `/api/analyze_sell`
API phân tích xu hướng để quyết định bán
- Body: `{"symbol": "XRPJPY"}`
- Response: Kết quả phân tích xu hướng

### GET `/api/status`
Kiểm tra trạng thái hệ thống

## 🎨 Công nghệ sử dụng

### Backend
- **Flask** - Web framework
- **Pandas** - Data manipulation
- **NumPy** - Numerical computing
- **Requests** - HTTP client for Binance API

### Frontend
- **Bootstrap 5** - UI framework
- **jQuery** - JavaScript library
- **Bootstrap Icons** - Icon set
- **Custom CSS** - Responsive design

### API
- **Binance API** - Cryptocurrency data source

## 🔍 Thuật toán phân tích

### Signal Scoring
Hệ thống tính điểm tín hiệu dựa trên:
1. **Ichimoku Cloud Analysis** (trọng số cao nhất)
2. **Multi-timeframe EMA alignment**
3. **Stochastic Oscillator with divergence**
4. **Enhanced RSI analysis**
5. **Volume confirmation with OBV**
6. **MACD with histogram momentum**
7. **Fibonacci retracement levels**
8. **Candlestick patterns**
9. **Pivot points analysis**

### Risk Management
- Tự động tính Stop Loss dựa trên ATR
- Take Profit levels tối ưu theo trend strength
- Risk/Reward ratio validation
- Fibonacci-based target adjustment

## ⚠️ Lưu ý quan trọng

1. **Không phải lời khuyên tài chính**: Đây chỉ là công cụ hỗ trợ phân tích kỹ thuật
2. **Tự nghiên cứu**: Luôn DYOR (Do Your Own Research) trước khi đầu tư
3. **Rủi ro cao**: Cryptocurrency là khoản đầu tư có rủi ro rất cao
4. **Quản lý vốn**: Chỉ đầu tư số tiền bạn có thể chấp nhận mất

## 📈 Roadmap

- [ ] Thêm nhiều coin/pair hơn
- [ ] Backtesting engine
- [ ] Alert system (email/telegram)
- [ ] Portfolio management
- [ ] Mobile responsive optimization
- [ ] Real-time WebSocket data
- [ ] Historical performance tracking

## 🐛 Báo lỗi

Nếu gặp lỗi, vui lòng tạo issue với thông tin:
- Mô tả lỗi
- Các bước tái hiện
- Screenshot (nếu có)
- Log error từ terminal

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết.

---

**Disclaimer**: Đây là công cụ phân tích kỹ thuật, không phải lời khuyên đầu tư. Cryptocurrency có rủi ro cao, hãy cân nhắc kỹ trước khi đầu tư.
