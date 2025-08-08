# Dynamic Coin System - Hệ thống Coin Động

## Tổng quan
Hệ thống đã được nâng cấp từ việc sử dụng các cặp coin cố định sang hệ thống coin động, tự động lấy dữ liệu từ Binance API theo base currency và volume.

## Tính năng mới

### 1. Base Currency Selection
- **JPY**: Các cặp coin với đồng Yên Nhật
- **USDT**: Các cặp coin với Tether USD
- Hệ thống tự động lấy top coin có volume cao nhất cho mỗi base currency

### 2. Phân trang theo chức năng
- **Predict Buy (Dự đoán mua)**: Top 10 coin với volume cao nhất
- **Analyze Sell (Phân tích bán)**: Top 15 coin với volume cao nhất  
- **Backtest**: Top 15 coin với volume cao nhất

### 3. Real-time Data
- Dữ liệu coin được cập nhật real-time từ Binance API
- Hiển thị volume giao dịch 24h cho mỗi coin
- Tự động sắp xếp theo volume từ cao xuống thấp

## Cải tiến kỹ thuật

### Backend Changes
1. **enhanced_app_v2.py**:
   - `get_top_coins_by_base_currency()`: Lấy top coin theo base currency
   - `get_available_base_currencies()`: Trả về ['JPY', 'USDT']
   - `run_multi_timeframe_analysis(coin_pairs)`: Hỗ trợ phân tích coin list tùy chỉnh

2. **app.py**:
   - `/api/coins/<base_currency>`: API endpoint lấy coin động
   - Cập nhật tất cả routes để truyền `base_currencies`
   - Cập nhật API predict_buy để sử dụng base_currency parameter

### Frontend Changes
1. **index.html**: 
   - Hiển thị base currencies thay vì fixed pairs
   - Hiển thị sample coins từ USDT

2. **predict_buy.html**:
   - Base currency selection dropdown
   - Dynamic coin loading khi chọn base currency
   - JavaScript xử lý state management

3. **analyze_sell.html**:
   - Base currency selection dropdown  
   - Top 15 coin selection
   - JavaScript dynamic loading

4. **backtest.html**:
   - Base currency selection dropdown
   - Top 15 coin selection cho backtest
   - JavaScript dynamic loading

## API Endpoints

### GET /api/coins/{base_currency}
Trả về top coins cho base currency được chọn.

**Response:**
```json
{
  "success": true,
  "coins": [
    {
      "symbol": "BTCUSDT",
      "volume": 1234567890.12,
      "volume_display": "1.23B USDT"
    }
  ]
}
```

### POST /api/predict_buy
Chạy phân tích dự đoán mua với base currency.

**Request:**
```json
{
  "base_currency": "USDT"
}
```

## User Experience

### Workflow mới:
1. **Chọn Base Currency**: Người dùng chọn JPY hoặc USDT
2. **Auto-load Coins**: Hệ thống tự động tải top coins
3. **Chọn Coin**: Người dùng chọn coin từ danh sách động
4. **Thực hiện phân tích**: Chạy phân tích với coin đã chọn

### UI Improvements:
- ✅ Base currency selection rõ ràng
- ✅ Loading states khi fetch data
- ✅ Error handling cho API calls  
- ✅ Responsive design
- ✅ Volume display cho từng coin
- ✅ Disabled states để guide user flow

## Lợi ích

### 1. Tính linh hoạt
- Không bị giới hạn bởi danh sách coin cố định
- Tự động cập nhật theo thị trường
- Hỗ trợ nhiều base currencies

### 2. Dữ liệu chính xác
- Real-time data từ Binance
- Volume-based ranking
- Loại bỏ các coin có volume thấp

### 3. User Experience tốt hơn
- Interface trực quan, dễ sử dụng
- Clear workflow với visual feedback
- Error handling tốt

## Cấu hình hệ thống

### Binance API Endpoints được sử dụng:
- `/api/v3/ticker/24hr`: Lấy volume 24h
- `/api/v3/exchangeInfo`: Lấy thông tin symbols

### Rate Limiting:
- Built-in delay 1 giây giữa các API calls
- Error handling cho timeout và rate limits

### Coin Limits:
- Predict Buy: 10 coins
- Analyze Sell: 15 coins  
- Backtest: 15 coins

## Testing

Hệ thống đã được test với:
- ✅ Base currency selection (JPY, USDT)
- ✅ Dynamic coin loading
- ✅ API endpoints response
- ✅ Frontend state management
- ✅ Error handling
- ✅ Responsive design

## Migration từ Fixed Pairs

Cách thức migration:
1. ✅ Backend: Thêm dynamic coin methods
2. ✅ API: Cập nhật endpoints và parameters  
3. ✅ Frontend: Cập nhật UI và JavaScript
4. ✅ Testing: Kiểm tra toàn bộ workflow

## Kết luận

Hệ thống coin động đã được triển khai thành công, cung cấp:
- Flexibility trong việc chọn coin
- Real-time market data
- Better user experience
- Scalable architecture cho future enhancements

Người dùng giờ có thể:
- Chọn base currency (JPY/USDT)
- Xem top coins theo volume real-time
- Thực hiện phân tích với coins phù hợp nhất với thị trường hiện tại
