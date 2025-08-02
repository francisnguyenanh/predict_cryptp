# 🚀 Crypto Prediction Suite

Hệ thống dự đoán và phân tích cryptocurrency tiên tiến cho các cặp JPY, sử dụng phân tích kỹ thuật đa khung thời gian và machine learning để đưa ra các tín hiệu giao dịch chính xác.

## ✨ Tính năng nổi bật

### 🎯 Phân tích đa chiều
- **Multi-timeframe Analysis**: Phân tích trên 15m, 1h, 4h để xác định xu hướng tổng thể
- **Advanced Technical Indicators**: 15+ chỉ báo kỹ thuật chuyên nghiệp
- **Smart Signal Scoring**: Hệ thống tính điểm thông minh với trọng số tối ưu
- **Risk/Reward Optimization**: Tính toán TP/SL dựa trên ATR và volatility

### 📊 Chỉ báo kỹ thuật
- **Trend Analysis**: EMA 10/20/50, Price Alignment, Trend Strength
- **Momentum**: RSI, MACD, Stochastic, RSI Divergence
- **Volatility**: Bollinger Bands, ATR, Keltner Channels
- **Volume**: OBV, A/D Line, Volume Confirmation
- **Pattern Recognition**: Hammer, Engulfing, Doji, Support/Resistance

### 🤖 Tự động hóa
- **Auto Trading Signals**: Tín hiệu giao dịch tự động theo chu kỳ
- **Real-time Dashboard**: Giao diện real-time với màu sắc trực quan
- **HTML Reports**: Báo cáo chi tiết với biểu đồ và phân tích sâu
- **Alert System**: Cảnh báo khi có tín hiệu chất lượng cao

## 📊 Các cặp coin được hỗ trợ

| Coin | Pair | Đặc điểm |
|------|------|----------|
| 🚀 XRP | XRP/JPY | Thanh khoản cao, volatility trung bình |
| ⭐ XLM | XLM/JPY | Correlation với XRP, nhanh nhạy |
| 🔵 ADA | ADA/JPY | Stable trends, tốt cho swing trading |
| 🟣 SUI | SUI/JPY | Coin mới, volatility cao, cơ hội lớn |

## 🛠️ Cài đặt và sử dụng

### 1. Clone repository
```bash
git clone https://github.com/yourusername/crypto-prediction.git
cd crypto-prediction
```

### 2. Cài đặt Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Cài đặt TA-Lib

#### macOS:
```bash
brew install ta-lib
pip install TA-Lib
```

#### Windows:
```bash
# Tải file wheel từ: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
pip install TA_Lib‑0.4.25‑cp39‑cp39‑win_amd64.whl
```

#### Linux:
```bash
sudo apt-get install libta-lib-dev
pip install TA-Lib
```

## 🚀 Các cách sử dụng

### 1. Chạy phân tích cơ bản
```bash
python main.py
# Hoặc
python main.py --basic
```

### 2. Chạy phân tích nâng cao (Khuyến nghị)
```bash
python main.py --enhanced
```

### 3. Chế độ tự động
```bash
# Chạy tự động mỗi 15 phút
python main.py --auto

# Chạy tự động với interval tùy chỉnh
python main.py --auto --interval 30
```

### 4. Tạo báo cáo chi tiết
```bash
python report_generator.py
```

### 5. So sánh các phương pháp
```bash
python main.py --compare
```

### 6. Chỉ chạy một lần
```bash
python main.py --once
```

## 📈 Hiểu kết quả phân tích

### Ví dụ output:
```
🏆 #1 - XLMJPY
💰 Giá hiện tại: 56.420000
📊 Tín hiệu: SELL
🎯 Xác suất thành công: 85.2%
⭐ Chất lượng Entry: HIGH
📈 RSI: 32.8
📊 Xu hướng: 15m: DOWNTREND | 1h: DOWNTREND | 4h: DOWNTREND
🎯 Take Profit 1: 55.950 (-0.83%)
🎯 Take Profit 2: 55.650 (-1.36%)
🛑 Stop Loss: 56.890 (+0.83%)
🔔 Tín hiệu kích hoạt: EMA_bearish_cross, RSI_oversold_recovery, volume_confirm
```

### Giải thích các chỉ số:

#### 🎯 Xác suất thành công
- **>75%**: Tín hiệu mạnh, khuyến nghị giao dịch
- **60-75%**: Tín hiệu trung bình, giao dịch thận trọng  
- **<60%**: Tín hiệu yếu, không khuyến nghị

#### ⭐ Chất lượng Entry
- **HIGH**: Điểm entry tuyệt vời với nhiều xác nhận
- **MEDIUM**: Điểm entry ổn, cần quan sát thêm
- **LOW**: Điểm entry kém, nên chờ cơ hội khác

#### 📊 Xu hướng đa khung thời gian
- **UPTREND**: Xu hướng tăng mạnh
- **DOWNTREND**: Xu hướng giảm mạnh
- **SIDEWAYS**: Đi ngang, chờ breakout

#### 🎯 Take Profit & Stop Loss
- **TP1**: Mục tiêu conservative (1.5x ATR)
- **TP2**: Mục tiêu aggressive (2.5x ATR)
- **SL**: Stop loss bảo vệ (1.0x ATR)

## 🔧 Tùy chỉnh nâng cao

### 1. Thay đổi cặp coin trong `config.json`:
```json
{
  "trading_pairs": [
    "BTCUSDT",
    "ETHUSDT", 
    "ADAUSDT",
    "SOLUSDT"
  ]
}
```

### 2. Điều chỉnh ngưỡng xác suất:
```json
{
  "risk_management": {
    "probability_thresholds": {
      "high_quality": 0.8,
      "medium_quality": 0.65,
      "low_quality": 0.45
    }
  }
}
```

### 3. Tùy chỉnh TP/SL ratio:
```json
{
  "risk_management": {
    "atr_multipliers": {
      "tp1": 2.0,
      "tp2": 3.0,
      "stop_loss": 1.2
    }
  }
}
```

## 📊 Methodology & Algorithm

### 1. Data Collection
- **Source**: Binance API real-time data
- **Timeframes**: 15m (primary), 1h, 4h for trend confirmation
- **History**: 200 candles for accurate calculation

### 2. Technical Analysis
```
Signal Score = Σ(Indicator_Weight × Indicator_Signal)

Where:
- EMA Cross: 3.0 points
- RSI Signals: 2.5 points  
- MACD Cross: 2.5 points
- Bollinger Bounce: 2.0 points
- Volume Confirmation: 1.5 points
- Pattern Recognition: 1.5-2.0 points
```

### 3. Probability Calculation
```
P(success) = min(
    base_probability + 
    trend_bonus + 
    rsi_bonus + 
    volume_bonus + 
    score_difference_bonus,
    0.95
)
```

### 4. Risk Management
```
TP1 = Current_Price ± (ATR × 1.5)
TP2 = Current_Price ± (ATR × 2.5)  
SL = Current_Price ± (ATR × 1.0)
R/R_Ratio = (TP1_Distance) / (SL_Distance)
```

## 📱 Features

### 🎨 Beautiful Dashboard
- Real-time colorized output
- Progress indicators and status updates
- Professional table formatting
- Signal strength visualization

### 📊 Advanced Analytics
- Multi-timeframe trend analysis
- Volume pattern recognition
- Volatility-based position sizing
- Divergence detection

### 🤖 Automation Ready
- Scheduled analysis runs
- Auto-report generation
- Alert notifications
- Log file management

### 📈 Comprehensive Reports
- Interactive HTML reports
- Price charts with indicators
- Signal history tracking
- Performance analytics

## ⚡ Performance Tips

### 1. Optimal Usage
- **Best Timeframe**: 15 phút cho scalping, 1h cho swing
- **Market Hours**: Hoạt động tốt nhất trong giờ Asian/European session
- **Update Frequency**: Chạy lại mỗi 15-30 phút
- **Pair Selection**: Focus vào 2-3 pairs để quản lý tốt hơn

### 2. Trading Guidelines
- **Entry**: Chỉ giao dịch signals HIGH quality (>75%)
- **Position Size**: Không quá 2-3% account per trade
- **Stop Loss**: Luôn đặt SL theo khuyến nghị
- **Take Profit**: Có thể take partial profit tại TP1

## 🔒 Risk Management

### ⚠️ Lưu ý quan trọng
1. **Đây chỉ là công cụ hỗ trợ**, không phải lời khuyên đầu tư
2. **Luôn DYOR** (Do Your Own Research)
3. **Chỉ đầu tư số tiền có thể chấp nhận mất**
4. **Backtest trước khi sử dụng real money**
5. **Kết hợp với fundamental analysis**

### 📋 Checklist trước khi trade
- [ ] Signal quality HIGH (>75%)
- [ ] Multi-timeframe alignment
- [ ] Volume confirmation
- [ ] Clear TP/SL levels
- [ ] Position size calculated
- [ ] Risk/reward ratio > 1:1

## � Troubleshooting

### Lỗi thường gặp:

#### 1. Import TA-Lib failed
```bash
# macOS
brew install ta-lib
pip install TA-Lib

# Windows: Tải wheel file và install manually
```

#### 2. API Connection Error
- Kiểm tra internet connection
- Verify Binance API status
- Try again after 1-2 minutes

#### 3. No data returned
- Check symbol format (phải đúng theo Binance)
- Verify pair exists và đang active
- Check timeframe parameter

#### 4. Charts not generating
```bash
# Cài đặt matplotlib backend
pip install matplotlib seaborn
```

## 📞 Support & Updates

### 🔄 Auto Updates
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### 🆘 Getting Help
1. Check troubleshooting section
2. Verify all dependencies installed
3. Test with basic mode first
4. Check log files in `/logs` directory

### 🌟 Contributing
Pull requests welcome! Please follow:
1. Code style consistency
2. Add comments for complex logic
3. Test với sample data
4. Update documentation

## � Roadmap

### v1.1 (Coming Soon)
- [ ] Machine Learning price prediction
- [ ] More cryptocurrency pairs
- [ ] Telegram/Discord bot integration
- [ ] Portfolio management features

### v1.2 (Future)
- [ ] Options/Futures analysis
- [ ] Social sentiment analysis
- [ ] Advanced backtesting
- [ ] Mobile app companion

## ⚖️ Legal Disclaimer

**QUAN TRỌNG: ĐỌC KỸ TRƯỚC KHI SỬ DỤNG**

- Phần mềm này chỉ phục vụ mục đích giáo dục và nghiên cứu
- Không phải lời khuyên đầu tư tài chính
- Cryptocurrency trading có rủi ro cao
- Tác giả không chịu trách nhiệm về any losses
- Luôn tham khảo chuyên gia tài chính trước khi đầu tư
- Tuân thủ pháp luật địa phương về crypto trading

---

<div align="center">

**Made with ❤️ for the Crypto Community**

⭐ Star this repo if it helped you | 🐛 Report issues | 🔄 Pull requests welcome


# Tối ưu (khuyến nghị)
python auto_runner.py --auto              # 35 phút
python auto_runner.py --interval 30       # 30 phút  
python auto_runner.py --interval 45       # 45 phút

# Nhanh hơn (ít chính xác hơn)
python auto_runner.py --interval 20       # 20 phút

# Chậm hơn (có thể bỏ lỡ cơ hội)
python auto_runner.py --interval 60       # 60 phút


</div>
