#!/usr/bin/env python3
"""
Enhanced Crypto Analysis với logic sửa đổi và tracking kết quả
"""

import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
# Thay thế TA-Lib bằng các hàm tự viết
import warnings
import os
import json
from tabulate import tabulate
import colorama
from colorama import Fore, Back, Style

warnings.filterwarnings('ignore')
colorama.init()

# ================== THAY THẾ TA-LIB BẰNG CÁC HÀM TỰ VIẾT ==================

def calculate_ema(data, window):
    """Tính Exponential Moving Average"""
    return data.ewm(span=window, adjust=False).mean()

def calculate_sma(data, window):
    """Tính Simple Moving Average"""
    return data.rolling(window=window).mean()

def calculate_rsi(data, window=14):
    """Tính Relative Strength Index"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast=12, slow=26, signal=9):
    """Tính MACD"""
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    macd = ema_fast - ema_slow
    macd_signal = calculate_ema(macd, signal)
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist

def calculate_bollinger_bands(data, window=20, num_std=2):
    """Tính Bollinger Bands"""
    sma = calculate_sma(data, window)
    std = data.rolling(window=window).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    return upper, sma, lower

def calculate_atr(high, low, close, window=14):
    """Tính Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    return atr

def calculate_stochastic(high, low, close, k_window=14, d_window=3):
    """Tính Stochastic Oscillator"""
    lowest_low = low.rolling(window=k_window).min()
    highest_high = high.rolling(window=k_window).max()
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = calculate_sma(k_percent, d_window)
    return k_percent, d_percent

def calculate_obv(close, volume):
    """Tính On-Balance Volume"""
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv

def calculate_adx(high, low, close, window=14):
    """Tính Average Directional Index"""
    tr = calculate_atr(high, low, close, 1)
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0)
    minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0)
    
    plus_dm = pd.Series(plus_dm).rolling(window=window).mean()
    minus_dm = pd.Series(minus_dm).rolling(window=window).mean()
    tr_avg = tr.rolling(window=window).mean()
    
    plus_di = 100 * (plus_dm / tr_avg)
    minus_di = 100 * (minus_dm / tr_avg)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=window).mean()
    
    return adx, plus_di, minus_di

def is_hammer(open_price, high, low, close):
    """Kiểm tra nến Hammer"""
    body = abs(close - open_price)
    upper_shadow = high - max(close, open_price)
    lower_shadow = min(close, open_price) - low
    
    is_hammer = (lower_shadow > 2 * body) & (upper_shadow < body)
    return is_hammer.astype(int) * 100

def is_doji(open_price, high, low, close):
    """Kiểm tra nến Doji"""
    body = abs(close - open_price)
    total_range = high - low
    
    is_doji = body < (total_range * 0.1)
    return is_doji.astype(int) * 100

def is_engulfing_bullish(open_price, high, low, close):
    """Kiểm tra mô hình Bullish Engulfing"""
    prev_open = open_price.shift(1)
    prev_close = close.shift(1)
    
    is_bullish = (prev_close < prev_open) & (close > open_price) & \
                 (open_price < prev_close) & (close > prev_open)
    return is_bullish.astype(int) * 100

def is_morning_star(open_price, high, low, close):
    """Kiểm tra mô hình Morning Star (đơn giản hóa)"""
    prev_close = close.shift(1)
    prev2_close = close.shift(2)
    
    is_morning = (prev2_close > prev_close) & (close > prev_close) & \
                 (close > open_price)
    return is_morning.astype(int) * 100

def is_hanging_man(open_price, high, low, close):
    """Kiểm tra nến Hanging Man"""
    body = abs(close - open_price)
    upper_shadow = high - max(close, open_price)
    lower_shadow = min(close, open_price) - low
    
    is_hanging = (lower_shadow > 2 * body) & (upper_shadow < body) & \
                 (close < open_price)
    return is_hanging.astype(int) * 100

def is_evening_star(open_price, high, low, close):
    """Kiểm tra mô hình Evening Star (đơn giản hóa)"""
    prev_close = close.shift(1)
    prev2_close = close.shift(2)
    
    is_evening = (prev2_close < prev_close) & (close < prev_close) & \
                 (close < open_price)
    return is_evening.astype(int) * 100

class PredictionTracker:
    """Class để theo dõi và đánh giá kết quả dự đoán"""
    
    def __init__(self):
        self.predictions = {}
    
    def load_predictions(self):
        return {}
    
    def save_predictions(self):
        pass
    
    def add_prediction(self, symbol, prediction_data):
        if symbol not in self.predictions:
            self.predictions[symbol] = []
        prediction_data['timestamp'] = datetime.now().isoformat()
        prediction_data['status'] = 'PENDING'
        self.predictions[symbol].append(prediction_data)
        if len(self.predictions[symbol]) > 50:
            self.predictions[symbol] = self.predictions[symbol][-50:]
        # Không lưu ra file
    
    def check_predictions(self, symbol, current_price):
        """Kiểm tra kết quả các dự đoán và tính accuracy mới"""
        if symbol not in self.predictions:
            return {'total': 0, 'hit_tp1': 0, 'hit_tp2': 0, 'hit_sl': 0, 'pending': 0, 
                   'latest_accuracy': 0, 'average_accuracy': 0}
        
        results = {'total': 0, 'hit_tp1': 0, 'hit_tp2': 0, 'hit_sl': 0, 'pending': 0}
        accuracy_list = []
        latest_accuracy = 0
        
        for i, prediction in enumerate(self.predictions[symbol]):
            # Tính accuracy cho từng prediction
            single_accuracy = self.calculate_single_accuracy(prediction, current_price)
            
            # Lưu accuracy vào prediction nếu chưa có
            if 'accuracy' not in prediction:
                prediction['accuracy'] = single_accuracy
            
            accuracy_list.append(prediction['accuracy'])
            
            # Accuracy của prediction gần nhất
            if i == len(self.predictions[symbol]) - 1:
                latest_accuracy = single_accuracy
                # Cập nhật accuracy cho prediction gần nhất
                prediction['accuracy'] = single_accuracy
            
            if prediction['status'] == 'PENDING':
                # Kiểm tra thời gian hết hạn (24h)
                pred_time = datetime.fromisoformat(prediction['timestamp'])
                if datetime.now() - pred_time > timedelta(hours=24):
                    prediction['status'] = 'EXPIRED'
                    continue
                
                # Kiểm tra TP/SL cho status cũ
                signal_type = prediction['signal_type']
                entry_price = prediction['entry_price']
                tp1 = prediction['tp1']
                tp2 = prediction['tp2']
                stop_loss = prediction['stop_loss']
                
                if signal_type == 'BUY':
                    if current_price >= tp2:
                        prediction['status'] = 'HIT_TP2'
                        prediction['actual_exit_price'] = current_price
                    elif current_price >= tp1:
                        prediction['status'] = 'HIT_TP1'
                        prediction['actual_exit_price'] = current_price
                    elif current_price <= stop_loss:
                        prediction['status'] = 'HIT_SL'
                        prediction['actual_exit_price'] = current_price
                elif signal_type == 'SELL':
                    if current_price <= tp2:
                        prediction['status'] = 'HIT_TP2'
                        prediction['actual_exit_price'] = current_price
                    elif current_price <= tp1:
                        prediction['status'] = 'HIT_TP1'
                        prediction['actual_exit_price'] = current_price
                    elif current_price >= stop_loss:
                        prediction['status'] = 'HIT_SL'
                        prediction['actual_exit_price'] = current_price
        
        # Tính toán thống kê cũ
        for prediction in self.predictions[symbol]:
            results['total'] += 1
            if prediction['status'] == 'HIT_TP1':
                results['hit_tp1'] += 1
            elif prediction['status'] == 'HIT_TP2':
                results['hit_tp2'] += 1
            elif prediction['status'] == 'HIT_SL':
                results['hit_sl'] += 1
            elif prediction['status'] == 'PENDING':
                results['pending'] += 1
        
        # Tính accuracy trung bình
        average_accuracy = sum(accuracy_list) / len(accuracy_list) if accuracy_list else 0
        
        results['latest_accuracy'] = latest_accuracy
        results['average_accuracy'] = average_accuracy
        
        self.save_predictions()
        return results
    
    def calculate_single_accuracy(self, prediction, current_price):
        """Tính accuracy cho một prediction dựa trên logic mới"""
        try:
            signal_type = prediction['signal_type']
            tp1 = prediction['tp1']
            tp2 = prediction['tp2']
            
            if signal_type == 'BUY':
                # Với BUY: nếu giá hiện tại >= TP1 hoặc TP2 thì accuracy = 100%
                if current_price >= tp2:
                    return 100.0  # Đạt TP2 = 100%
                elif current_price >= tp1:
                    return 100.0  # Đạt TP1 = 100%
                else:
                    return 0.0    # Chưa đạt TP = 0%
            
            elif signal_type == 'SELL':
                # Với SELL: nếu giá hiện tại <= TP1 hoặc TP2 thì accuracy = 100%
                if current_price <= tp2:
                    return 100.0  # Đạt TP2 = 100%
                elif current_price <= tp1:
                    return 100.0  # Đạt TP1 = 100%
                else:
                    return 0.0    # Chưa đạt TP = 0%
            
            else:  # WAIT signal
                return 0.0
                
        except Exception as e:
            #print(f"❌ Error calculating accuracy: {e}")
            return 0.0

class EnhancedCryptoPredictionAppV2:
    def __init__(self):
        # Removed fixed pairs - will be dynamic now
        self.base_url = "https://api.binance.com/api/v3/klines"
        self.exchange_info_url = "https://api.binance.com/api/v3/exchangeInfo"
        self.ticker_24hr_url = "https://api.binance.com/api/v3/ticker/24hr"
        self.tracker = PredictionTracker()
        
        # Supported base currencies
        self.supported_base_currencies = ['JPY', 'USDT']
        
        # Market Patterns Configuration
        self.market_patterns = {
            "default": {
                "name": "Mặc định",
                "description": "Thông số cân bằng cho mọi tình huống",
                "tp1_multiplier": 1.0,
                "tp2_multiplier": 2.0,
                "sl_multiplier": 1.0,
                "atr_period": 14,
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "ema_fast": 12,
                "ema_slow": 26,
                "bb_period": 20,
                "bb_std": 2.0,
                "volume_threshold": 1.2,
                "volume_multiplier": 1.2,
                "success_boost": 1.0
            },
            "bull_market": {
                "name": "Thị trường tăng",
                "description": "Tối ưu cho xu hướng tăng mạnh",
                "tp1_multiplier": 1.5,
                "tp2_multiplier": 3.0,
                "sl_multiplier": 1.2,
                "atr_period": 21,
                "rsi_period": 21,
                "rsi_oversold": 40,
                "rsi_overbought": 80,
                "ema_fast": 8,
                "ema_slow": 21,
                "bb_period": 20,
                "bb_std": 2.2,
                "volume_threshold": 1.5,
                "volume_multiplier": 1.5,
                "success_boost": 1.15
            },
            "bear_market": {
                "name": "Thị trường giảm", 
                "description": "Bảo thủ cho xu hướng giảm",
                "tp1_multiplier": 0.8,
                "tp2_multiplier": 1.5,
                "sl_multiplier": 0.7,
                "atr_period": 10,
                "rsi_period": 10,
                "rsi_oversold": 20,
                "rsi_overbought": 60,
                "ema_fast": 5,
                "ema_slow": 13,
                "bb_period": 14,
                "bb_std": 1.8,
                "volume_threshold": 1.0,
                "volume_multiplier": 1.0,
                "success_boost": 0.9
            },
            "sideways": {
                "name": "Thị trường ngang",
                "description": "Chiến lược cho thị trường sideway",
                "tp1_multiplier": 0.6,
                "tp2_multiplier": 1.2,
                "sl_multiplier": 0.5,
                "atr_period": 7,
                "rsi_period": 7,
                "rsi_oversold": 35,
                "rsi_overbought": 65,
                "ema_fast": 5,
                "ema_slow": 10,
                "bb_period": 10,
                "bb_std": 1.5,
                "volume_threshold": 0.8,
                "volume_multiplier": 0.8,
                "success_boost": 0.85
            },
            "high_volatility": {
                "name": "Biến động cao",
                "description": "Thích ứng với biến động lớn",
                "tp1_multiplier": 2.0,
                "tp2_multiplier": 4.0,
                "sl_multiplier": 1.5,
                "atr_period": 28,
                "rsi_period": 28,
                "rsi_oversold": 25,
                "rsi_overbought": 75,
                "ema_fast": 21,
                "ema_slow": 50,
                "bb_period": 25,
                "bb_std": 2.5,
                "volume_threshold": 2.0,
                "volume_multiplier": 2.0,
                "success_boost": 1.1
            },
            "low_volatility": {
                "name": "Biến động thấp",
                "description": "Tối ưu cho thị trường ít biến động",
                "tp1_multiplier": 0.4,
                "tp2_multiplier": 0.8,
                "sl_multiplier": 0.3,
                "atr_period": 5,
                "rsi_period": 5,
                "rsi_oversold": 40,
                "rsi_overbought": 60,
                "ema_fast": 3,
                "ema_slow": 8,
                "bb_period": 8,
                "bb_std": 1.2,
                "volume_threshold": 0.6,
                "volume_multiplier": 0.6,
                "success_boost": 0.8
            },
            "breakout": {
                "name": "Đột phá",
                "description": "Bắt xu hướng đột phá mạnh",
                "tp1_multiplier": 2.5,
                "tp2_multiplier": 5.0,
                "sl_multiplier": 1.8,
                "atr_period": 20,
                "rsi_period": 20,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "ema_fast": 10,
                "ema_slow": 30,
                "bb_period": 20,
                "bb_std": 3.0,
                "volume_threshold": 3.0,
                "volume_multiplier": 3.0,
                "success_boost": 1.2
            },
            "scalping": {
                "name": "Scalping",
                "description": "Giao dịch ngắn hạn tần suất cao",
                "tp1_multiplier": 0.3,
                "tp2_multiplier": 0.6,
                "sl_multiplier": 0.2,
                "atr_period": 3,
                "rsi_period": 3,
                "rsi_oversold": 45,
                "rsi_overbought": 55,
                "ema_fast": 2,
                "ema_slow": 5,
                "bb_period": 5,
                "bb_std": 1.0,
                "volume_threshold": 0.5,
                "volume_multiplier": 0.5,
                "success_boost": 0.75
            }
        }
        
        # Current active pattern
        self.active_pattern = "default"
        
        # Các kiểu đầu tư
        self.investment_types = {
            '60m': {'timeframe': '15m', 'analysis_timeframes': ['15m', '1h'], 'hold_duration': '60 minutes'},
            '4h': {'timeframe': '1h', 'analysis_timeframes': ['1h', '4h'], 'hold_duration': '4 hours'}, 
            '1d': {'timeframe': '4h', 'analysis_timeframes': ['4h', '1d'], 'hold_duration': '1 day'}
        }

    def get_top_coins_by_base_currency(self, base_currency='USDT', limit=15):
        """
        Lấy top coins theo base currency từ Binance API
        Sắp xếp theo lượng tiền giao dịch (price * volume) để có các coin hot nhất
        """
        try:
            response = requests.get(self.ticker_24hr_url, timeout=30)
            response.raise_for_status()
            tickers = response.json()
            
            # Lọc các coin có base currency được chỉ định
            filtered_coins = []
            for ticker in tickers:
                symbol = ticker['symbol']
                if symbol.endswith(base_currency):
                    # Loại bỏ những coin có tên quá dài hoặc là leverage tokens và BTC
                    base_coin = symbol.replace(base_currency, '')
                    if (len(base_coin) <= 10 and 
                        not any(x in base_coin for x in ['UP', 'DOWN', 'BEAR', 'BULL']) and
                        base_coin not in ['BUSD', 'TUSD', 'USDC', 'DAI', 'PAX', 'BTC']):  # Loại bỏ stablecoins và BTC
                        
                        price = float(ticker['lastPrice'])
                        volume = float(ticker['volume'])
                        money_traded = price * volume  # Tính lượng tiền giao dịch
                        
                        filtered_coins.append({
                            'symbol': symbol,
                            'baseAsset': base_coin,
                            'volume': volume,
                            'priceChange': float(ticker['priceChangePercent']),
                            'price': price,
                            'money_traded': money_traded
                        })
            
            # Sắp xếp theo lượng tiền giao dịch giảm dần
            filtered_coins.sort(key=lambda x: x['money_traded'], reverse=True)
            
            # Lấy top coins
            top_coins = filtered_coins[:limit]
            
            #print(f"🔍 Found {len(top_coins)} top coins for {base_currency}")
            return top_coins
            
        except Exception as e:
            #print(f"❌ Error getting top coins: {e}")
            # Fallback to some popular coins (excluding BTC)
            fallback_coins = {
                'USDT': ['ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'LINKUSDT', 'AVAXUSDT'],
                'JPY': ['ETHJPY', 'XRPJPY', 'ADAJPY', 'BNBJPY']
            }
            
            fallback_list = fallback_coins.get(base_currency, [])[:limit]
            return [{
                'symbol': coin, 
                'baseAsset': coin.replace(base_currency, ''),
                'volume': 0,
                'priceChange': 0,
                'price': 0,
                'money_traded': 0
            } for coin in fallback_list]

    def get_available_base_currencies(self):
        """Trả về danh sách base currencies được hỗ trợ"""
        return self.supported_base_currencies
        

    def get_kline_data(self, symbol, interval='15m', limit=200):
        """Lấy dữ liệu giá từ Binance API với error handling tốt hơn"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return None
            
            # Chuyển đổi thành DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Chuyển đổi kiểu dữ liệu
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            # Keep timestamp as a column, not index
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except requests.exceptions.RequestException as e:
            #print(f"{Fore.RED}❌ Network error for {symbol}: {e}{Style.RESET_ALL}")
            return None
        except Exception as e:
            #print(f"{Fore.RED}❌ Data error for {symbol}: {e}{Style.RESET_ALL}")
            return None
    
    def calculate_advanced_indicators(self, df):
        """Tính toán các chỉ báo kỹ thuật nâng cao"""
        if df is None or len(df) < 50:
            return None
            
        try:
            # Moving Averages
            df['EMA_10'] = calculate_ema(df['close'], 10)
            df['EMA_20'] = calculate_ema(df['close'], 20)
            df['EMA_50'] = calculate_ema(df['close'], 50)
            
            # Momentum Indicators
            df['RSI'] = calculate_rsi(df['close'], 14)
            df['MACD'], df['MACD_signal'], df['MACD_hist'] = calculate_macd(df['close'])
            
            # Volatility Indicators
            df['BB_upper'], df['BB_middle'], df['BB_lower'] = calculate_bollinger_bands(df['close'])
            df['ATR'] = calculate_atr(df['high'], df['low'], df['close'], 14)
            
            # Volume Indicators
            df['volume_sma'] = calculate_sma(df['volume'], 20)
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # Support/Resistance
            df['resistance'] = df['high'].rolling(window=20).max()
            df['support'] = df['low'].rolling(window=20).min()
            
            # === NEW ADVANCED INDICATORS ===
            
            # Ichimoku Cloud Components
            high9 = df['high'].rolling(window=9).max()
            low9 = df['low'].rolling(window=9).min()
            df['tenkan_sen'] = (high9 + low9) / 2
            
            high26 = df['high'].rolling(window=26).max()
            low26 = df['low'].rolling(window=26).min()
            df['kijun_sen'] = (high26 + low26) / 2
            
            df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
            
            high52 = df['high'].rolling(window=52).max()
            low52 = df['low'].rolling(window=52).min()
            df['senkou_span_b'] = ((high52 + low52) / 2).shift(26)
            
            df['chikou_span'] = df['close'].shift(-26)
            
            # Stochastic Oscillator
            df['stoch_k'], df['stoch_d'] = calculate_stochastic(df['high'], df['low'], df['close'], 
                                                               k_window=14, d_window=3)
            
            # On-Balance Volume (OBV)
            df['OBV'] = calculate_obv(df['close'], df['volume'])
            df['OBV_sma'] = calculate_sma(df['OBV'], 20)
            
            # Average Directional Index (ADX) - Đo sức mạnh xu hướng
            df['ADX'], df['DI_plus'], df['DI_minus'] = calculate_adx(df['high'], df['low'], df['close'], 14)
            
            # Bollinger Band Width (để phát hiện thị trường sideway)
            df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
            df['BB_width_sma'] = df['BB_width'].rolling(window=20).mean()
            
            # Fibonacci Retracement Levels (tự động tính)
            df = self.calculate_fibonacci_levels(df)
            
            # Candlestick Pattern Recognition
            df = self.detect_candlestick_patterns(df)
            
            return df
            
        except Exception as e:
            #print(f"{Fore.RED}❌ Indicator calculation error: {e}{Style.RESET_ALL}")
            return None
    
    def calculate_fibonacci_levels(self, df):
        """Tự động tính các mức Fibonacci Retracement"""
        try:
            # Tìm high và low trong 50 periods gần nhất
            recent_high = df['high'].rolling(window=50).max().iloc[-1]
            recent_low = df['low'].rolling(window=50).min().iloc[-1]
            
            if pd.isna(recent_high) or pd.isna(recent_low):
                df['fib_236'] = df['close']
                df['fib_382'] = df['close'] 
                df['fib_500'] = df['close']
                df['fib_618'] = df['close']
                return df
            
            # Tính các mức Fibonacci
            diff = recent_high - recent_low
            df['fib_236'] = recent_high - (diff * 0.236)
            df['fib_382'] = recent_high - (diff * 0.382)
            df['fib_500'] = recent_high - (diff * 0.500)
            df['fib_618'] = recent_high - (diff * 0.618)
            
            return df
        except Exception:
            # Fallback values
            df['fib_236'] = df['close']
            df['fib_382'] = df['close']
            df['fib_500'] = df['close'] 
            df['fib_618'] = df['close']
            return df
    
    def detect_candlestick_patterns(self, df):
        """Phát hiện các mô hình nến quan trọng"""
        try:
            # Bullish patterns
            df['hammer'] = is_hammer(df['open'], df['high'], df['low'], df['close'])
            df['engulfing_bullish'] = is_engulfing_bullish(df['open'], df['high'], df['low'], df['close'])
            df['morning_star'] = is_morning_star(df['open'], df['high'], df['low'], df['close'])
            
            # Bearish patterns  
            df['hanging_man'] = is_hanging_man(df['open'], df['high'], df['low'], df['close'])
            df['evening_star'] = is_evening_star(df['open'], df['high'], df['low'], df['close'])
            
            # Reversal patterns
            df['doji'] = is_doji(df['open'], df['high'], df['low'], df['close'])
            
            return df
        except Exception:
            # Fallback - set all pattern columns to 0
            pattern_cols = ['hammer', 'engulfing_bullish', 'morning_star', 'hanging_man', 'evening_star', 'doji']
            for col in pattern_cols:
                df[col] = 0
            return df
    

    def calculate_tp_sl_by_investment_type(self, entry_price, signal_type, atr_value, trend_strength, investment_type='60m', df_main=None):
        """Tính toán TP/SL theo kiểu đầu tư với Fibonacci và Pivot Points"""
        
        # Base multipliers theo investment type
        if investment_type == '60m':
            if trend_strength == "STRONG_UP":
                tp1_multiplier = 2.8
                tp2_multiplier = 4.5
                sl_multiplier = 1.5
            elif trend_strength in ["STRONG_DOWN", "WAIT_FOR_UPTREND"]:
                tp1_multiplier = 1.2
                tp2_multiplier = 2.0
                sl_multiplier = 1.0
            else:
                tp1_multiplier = 1.8
                tp2_multiplier = 2.8
                sl_multiplier = 1.2
                
        elif investment_type == '4h':
            if trend_strength == "STRONG_UP":
                tp1_multiplier = 4.2
                tp2_multiplier = 6.5
                sl_multiplier = 1.8
            elif trend_strength in ["STRONG_DOWN", "WAIT_FOR_UPTREND"]:
                tp1_multiplier = 1.6
                tp2_multiplier = 2.6
                sl_multiplier = 1.3
            else:
                tp1_multiplier = 2.3
                tp2_multiplier = 3.6
                sl_multiplier = 1.5
                
        elif investment_type == '1d':
            if trend_strength == "STRONG_UP":
                tp1_multiplier = 5.5
                tp2_multiplier = 9.0
                sl_multiplier = 2.2
            elif trend_strength in ["STRONG_DOWN", "WAIT_FOR_UPTREND"]:
                tp1_multiplier = 2.2
                tp2_multiplier = 3.6
                sl_multiplier = 1.8
            else:
                tp1_multiplier = 3.0
                tp2_multiplier = 5.2
                sl_multiplier = 2.0
        
        # Basic TP/SL calculation
        if signal_type == 'BUY':
            base_tp1 = entry_price + (atr_value * tp1_multiplier)
            base_tp2 = entry_price + (atr_value * tp2_multiplier)
            base_sl = entry_price - (atr_value * sl_multiplier)
        else:  # WAIT
            base_tp1 = entry_price + (atr_value * 1.0)
            base_tp2 = entry_price + (atr_value * 2.0)
            base_sl = entry_price - (atr_value * 0.5)
        
        # === ENHANCED TP/SL WITH FIBONACCI & TECHNICAL LEVELS ===
        
        if df_main is not None and len(df_main) > 0 and signal_type == 'BUY':
            latest = df_main.iloc[-1]
            
            # Fibonacci-based TP adjustment
            if not pd.isna(latest['fib_236']) and not pd.isna(latest['fib_618']):
                # TP1: Aim for next Fibonacci level above entry
                fib_levels = [latest['fib_236'], latest['fib_382'], latest['fib_500'], latest['fib_618']]
                fib_levels.sort()
                
                # Find next Fibonacci resistance above entry price
                next_fib_resistance = None
                for fib_level in fib_levels:
                    if fib_level > entry_price * 1.005:  # At least 0.5% above entry
                        next_fib_resistance = fib_level
                        break
                
                if next_fib_resistance:
                    # Adjust TP1 to Fibonacci level if it's reasonable
                    fib_tp1 = next_fib_resistance
                    if entry_price * 1.01 <= fib_tp1 <= entry_price * 1.15:  # 1-15% range
                        base_tp1 = (base_tp1 + fib_tp1) / 2  # Blend with ATR-based TP
                
                # TP2: Target higher Fibonacci level
                higher_fib = None
                for fib_level in reversed(fib_levels):
                    if fib_level > entry_price * 1.02:
                        higher_fib = fib_level
                        break
                
                if higher_fib and higher_fib > base_tp1:
                    fib_tp2 = higher_fib
                    if fib_tp2 <= entry_price * 1.25:  # Max 25% gain
                        base_tp2 = (base_tp2 + fib_tp2) / 2
            
            # Support-based SL adjustment
            support_level = latest['support']
            if not pd.isna(support_level) and support_level < entry_price:
                # Place SL slightly below support
                support_sl = support_level * 0.995  # 0.5% below support
                
                # Use support-based SL if it's not too far from ATR-based SL
                sl_distance_atr = entry_price - base_sl
                sl_distance_support = entry_price - support_sl
                
                if 0.5 <= sl_distance_support / sl_distance_atr <= 2.0:  # Within reasonable range
                    base_sl = (base_sl + support_sl) / 2  # Blend
            
            # Bollinger Band adjustment
            if not pd.isna(latest['BB_upper']) and not pd.isna(latest['BB_lower']):
                # If entry is near BB lower, adjust TP to BB middle/upper
                bb_position = (entry_price - latest['BB_lower']) / (latest['BB_upper'] - latest['BB_lower'])
                
                if bb_position < 0.3:  # Entry near lower band
                    bb_tp1 = latest['BB_middle']
                    bb_tp2 = latest['BB_upper']
                    
                    if bb_tp1 > entry_price * 1.005:
                        base_tp1 = min(base_tp1, bb_tp1)  # Don't exceed BB middle initially
                    if bb_tp2 > base_tp1:
                        base_tp2 = (base_tp2 + bb_tp2) / 2  # Blend with BB upper
            
            # ADX-based adjustment (stronger trends = wider targets)
            if not pd.isna(latest['ADX']):
                if latest['ADX'] > 40:  # Very strong trend
                    base_tp2 *= 1.1  # Extend TP2 by 10%
                elif latest['ADX'] < 20:  # Weak trend
                    base_tp1 *= 0.9  # Reduce TP1 by 10%
                    base_tp2 *= 0.9  # Reduce TP2 by 10%
            
            # Volume confirmation adjustment
            if not pd.isna(latest['volume_ratio']):
                if latest['volume_ratio'] > 2.0:  # High volume breakout
                    base_tp2 *= 1.05  # Slightly extend TP2
                elif latest['volume_ratio'] < 0.8:  # Low volume
                    base_tp1 *= 0.95  # Reduce targets
                    base_tp2 *= 0.95
        
        # Final validation and rounding
        tp1 = round(max(base_tp1, entry_price * 1.002), 6)  # Min 0.2% profit
        tp2 = round(max(base_tp2, tp1 * 1.2), 6)  # TP2 at least 20% higher than TP1
        stop_loss = round(min(base_sl, entry_price * 0.98), 6)  # Max 2% loss for BUY
        
        # Risk management: Ensure reasonable R:R ratio
        risk = entry_price - stop_loss
        reward1 = tp1 - entry_price
        
        if risk > 0 and reward1 / risk < 1.5:  # Poor R:R ratio
            tp1 = entry_price + (risk * 1.5)  # Ensure at least 1.5:1 R:R
            tp2 = entry_price + (risk * 2.5)  # Ensure at least 2.5:1 R:R for TP2
        
        return tp1, tp2, stop_loss

    def calculate_tp_sl_fixed(self, entry_price, signal_type, atr_value, trend_strength, df_main=None):
        """Tính toán TP/SL cho SPOT TRADING (chỉ BUY) - backward compatibility với enhanced features"""
        return self.calculate_tp_sl_by_investment_type(entry_price, signal_type, atr_value, trend_strength, '60m', df_main)
    
    def calculate_enhanced_signal_score(self, df):
        """Tính điểm tín hiệu nâng cao với trọng số thông minh - OPTIMIZED theo gợi ý"""
        if df is None or len(df) < 3:
            return 0, 0, {}
            
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]
        
        buy_score = 0
        sell_score = 0
        signals = {}
        
        # === MARKET CONDITION ANALYSIS ===
        # Kiểm tra độ mạnh xu hướng với ADX - ĐÃ CÓ NHƯNG TỐI ƯU HÓA
        adx_strength = 1.0
        trend_quality = "WEAK"
        
        if not pd.isna(latest['ADX']):
            if latest['ADX'] > 30:  # Xu hướng rất mạnh
                adx_strength = 1.5
                trend_quality = "VERY_STRONG"
                signals['very_strong_trend'] = True
            elif latest['ADX'] > 25:  # Xu hướng mạnh
                adx_strength = 1.3
                trend_quality = "STRONG"
                signals['strong_trend'] = True
            elif latest['ADX'] > 20:  # Xu hướng trung bình
                adx_strength = 1.0
                trend_quality = "MODERATE"
            else:  # Xu hướng yếu/sideway
                adx_strength = 0.6  # Giảm mạnh để tránh sideway
                trend_quality = "WEAK"
                signals['weak_trend'] = True
        
        # Kiểm tra thị trường sideway với Bollinger Band Width - TỐI ƯU HÓA
        is_sideway = False
        sideway_penalty = 1.0
        
        if not pd.isna(latest['BB_width']) and not pd.isna(latest['BB_width_sma']):
            bb_width_ratio = latest['BB_width'] / latest['BB_width_sma']
            if bb_width_ratio < 0.7:  # Rất hẹp
                is_sideway = True
                sideway_penalty = 0.3  # Penalty mạnh
                signals['very_narrow_range'] = True
            elif bb_width_ratio < 0.8:  # Hẹp
                sideway_penalty = 0.5
                signals['narrow_range'] = True
            elif bb_width_ratio > 1.3:  # Mở rộng - tốt cho breakout
                sideway_penalty = 1.2
                signals['expanding_range'] = True
        
        # === 1. ICHIMOKU CLOUD ANALYSIS (Trọng số cao nhất) ===
        ichimoku_signal_strength = 0
        
        if not pd.isna(latest['tenkan_sen']) and not pd.isna(latest['kijun_sen']):
            # Tenkan-sen cross Kijun-sen với volume confirmation
            if latest['tenkan_sen'] > latest['kijun_sen'] and prev['tenkan_sen'] <= prev['kijun_sen']:
                # Kiểm tra volume confirmation
                volume_boost = 1.0
                if not pd.isna(latest['volume_ratio']) and latest['volume_ratio'] > 1.2:
                    volume_boost = 1.3
                
                ichimoku_signal_strength = 5 * adx_strength * volume_boost
                buy_score += ichimoku_signal_strength
                signals['ichimoku_bullish_cross'] = True
                
            elif latest['tenkan_sen'] < latest['kijun_sen'] and prev['tenkan_sen'] >= prev['kijun_sen']:
                ichimoku_signal_strength = 5 * adx_strength
                sell_score += ichimoku_signal_strength
                signals['ichimoku_bearish_cross'] = True
            
            # Price position vs Cloud - TỐI ƯU HÓA
            if not pd.isna(latest['senkou_span_a']) and not pd.isna(latest['senkou_span_b']):
                cloud_top = max(latest['senkou_span_a'], latest['senkou_span_b'])
                cloud_bottom = min(latest['senkou_span_a'], latest['senkou_span_b'])
                cloud_thickness = (cloud_top - cloud_bottom) / latest['close']
                
                if latest['close'] > cloud_top:
                    # Bonus nếu cloud dày (strong support)
                    cloud_bonus = 1.2 if cloud_thickness > 0.02 else 1.0
                    buy_score += 4 * adx_strength * cloud_bonus
                    signals['price_above_cloud'] = True
                    
                elif latest['close'] < cloud_bottom:
                    cloud_bonus = 1.2 if cloud_thickness > 0.02 else 1.0
                    sell_score += 4 * adx_strength * cloud_bonus
                    signals['price_below_cloud'] = True
                    
                elif cloud_bottom <= latest['close'] <= cloud_top:
                    # Trong cloud - neutral với penalty
                    buy_score *= 0.7
                    sell_score *= 0.7
                    signals['price_in_cloud'] = True
        
        # === 2. WEIGHTED MULTI-TIMEFRAME EMA ANALYSIS ===
        ema_alignment_score = 0
        
        # EMA Crossover với signal strength
        if (not pd.isna(latest['EMA_10']) and not pd.isna(latest['EMA_20']) and 
            not pd.isna(latest['EMA_50'])):
            
            # Bullish crossover
            if latest['EMA_10'] > latest['EMA_20'] and prev['EMA_10'] <= prev['EMA_20']:
                # Tính signal strength dựa trên angle và distance
                ema_distance = (latest['EMA_10'] - latest['EMA_20']) / latest['close']
                signal_strength = min(ema_distance * 1000, 2.0)  # Cap at 2.0
                
                ema_alignment_score = 3.5 * adx_strength * (1 + signal_strength)
                buy_score += ema_alignment_score
                signals['EMA_bullish_cross'] = True
                
            elif latest['EMA_10'] < latest['EMA_20'] and prev['EMA_10'] >= prev['EMA_20']:
                ema_distance = (latest['EMA_20'] - latest['EMA_10']) / latest['close']
                signal_strength = min(ema_distance * 1000, 2.0)
                
                ema_alignment_score = 3.5 * adx_strength * (1 + signal_strength)
                sell_score += ema_alignment_score
                signals['EMA_bearish_cross'] = True
            
            # Perfect alignment bonus
            if latest['close'] > latest['EMA_10'] > latest['EMA_20'] > latest['EMA_50']:
                alignment_strength = 1.0
                # Check EMA angles
                if (latest['EMA_10'] > prev['EMA_10'] and 
                    latest['EMA_20'] > prev['EMA_20'] and 
                    latest['EMA_50'] > prev['EMA_50']):
                    alignment_strength = 1.5  # All EMAs rising
                
                buy_score += 3 * adx_strength * alignment_strength
                signals['perfect_bullish_alignment'] = True
                
            elif latest['close'] < latest['EMA_10'] < latest['EMA_20'] < latest['EMA_50']:
                alignment_strength = 1.0
                if (latest['EMA_10'] < prev['EMA_10'] and 
                    latest['EMA_20'] < prev['EMA_20'] and 
                    latest['EMA_50'] < prev['EMA_50']):
                    alignment_strength = 1.5
                
                sell_score += 3 * adx_strength * alignment_strength
                signals['perfect_bearish_alignment'] = True
        
        # === 3. ADVANCED STOCHASTIC OSCILLATOR ANALYSIS ===
        stochastic_signal_strength = 0
        
        if not pd.isna(latest['stoch_k']) and not pd.isna(latest['stoch_d']):
            # Stochastic crossover với divergence detection
            if latest['stoch_k'] > latest['stoch_d'] and prev['stoch_k'] <= prev['stoch_d']:
                # Bullish crossover strength dựa trên vị trí
                if latest['stoch_k'] < 30:  # Oversold recovery
                    stochastic_signal_strength = 4 * adx_strength
                elif latest['stoch_k'] < 50:  # Mid-level recovery
                    stochastic_signal_strength = 3 * adx_strength
                else:  # Overbought area - weaker signal
                    stochastic_signal_strength = 1.5 * adx_strength
                    
                buy_score += stochastic_signal_strength
                signals['stoch_bullish_cross'] = True
                
            elif latest['stoch_k'] < latest['stoch_d'] and prev['stoch_k'] >= prev['stoch_d']:
                # Bearish crossover
                if latest['stoch_k'] > 70:  # Overbought decline
                    stochastic_signal_strength = 4 * adx_strength
                elif latest['stoch_k'] > 50:
                    stochastic_signal_strength = 3 * adx_strength
                else:
                    stochastic_signal_strength = 1.5 * adx_strength
                    
                sell_score += stochastic_signal_strength
                signals['stoch_bearish_cross'] = True
            
            # Stochastic Divergence Analysis
            if len(df) >= 10:
                # Simple divergence check over last 10 periods
                stoch_trend = latest['stoch_k'] - df.iloc[-10]['stoch_k']
                price_trend = latest['close'] - df.iloc[-10]['close']
                
                # Bullish divergence: price down, stoch up
                if price_trend < 0 and stoch_trend > 0 and latest['stoch_k'] < 40:
                    buy_score += 2.5 * adx_strength
                    signals['stoch_bullish_divergence'] = True
                    
                # Bearish divergence: price up, stoch down
                elif price_trend > 0 and stoch_trend < 0 and latest['stoch_k'] > 60:
                    sell_score += 2.5 * adx_strength
                    signals['stoch_bearish_divergence'] = True
        
        # === 4. ENHANCED RSI WITH MULTI-LEVEL ANALYSIS ===
        rsi_signal_strength = 0
        
        if not pd.isna(latest['RSI']) and not pd.isna(prev['RSI']):
            # RSI level-based scoring với momentum
            rsi_momentum = latest['RSI'] - prev['RSI']
            
            if latest['RSI'] < 25 and rsi_momentum > 0:  # Deep oversold recovery
                rsi_signal_strength = 3.5 * adx_strength
                signals['rsi_deep_oversold_recovery'] = True
            elif latest['RSI'] < 35 and rsi_momentum > 1:  # Oversold strong recovery
                rsi_signal_strength = 3 * adx_strength
                signals['rsi_oversold_recovery'] = True
            elif 40 <= latest['RSI'] <= 55 and rsi_momentum > 0:  # Neutral bullish
                rsi_signal_strength = 2 * adx_strength
                signals['rsi_neutral_bullish'] = True
            elif latest['RSI'] > 75 and rsi_momentum < 0:  # Overbought decline
                rsi_signal_strength = 3.5 * adx_strength
                signals['rsi_overbought_decline'] = True
            elif latest['RSI'] > 65 and rsi_momentum < -1:  # Strong decline from overbought
                rsi_signal_strength = 3 * adx_strength
                signals['rsi_strong_decline'] = True
            
            if rsi_signal_strength > 0:
                if signals.get('rsi_deep_oversold_recovery') or signals.get('rsi_oversold_recovery') or signals.get('rsi_neutral_bullish'):
                    buy_score += rsi_signal_strength
                else:
                    sell_score += rsi_signal_strength
        
        # === 5. ENHANCED VOLUME ANALYSIS WITH OBV ===
        volume_confirmation_score = 0
        
        # On-Balance Volume analysis
        if not pd.isna(latest['OBV']) and not pd.isna(latest['OBV_sma']) and not pd.isna(prev['OBV']):
            obv_momentum = latest['OBV'] - prev['OBV']
            price_momentum = latest['close'] - prev['close']
            
            # OBV-Price confirmation
            if obv_momentum > 0 and price_momentum > 0:  # Both rising
                if latest['OBV'] > latest['OBV_sma']:  # Above average
                    volume_confirmation_score = 3 * adx_strength
                    signals['obv_price_bullish_confirm'] = True
                else:
                    volume_confirmation_score = 2 * adx_strength
                    signals['obv_price_mild_bullish'] = True
                    
                buy_score += volume_confirmation_score
                
            elif obv_momentum < 0 and price_momentum < 0:  # Both falling
                if latest['OBV'] < latest['OBV_sma']:
                    volume_confirmation_score = 3 * adx_strength
                    signals['obv_price_bearish_confirm'] = True
                else:
                    volume_confirmation_score = 2 * adx_strength
                    signals['obv_price_mild_bearish'] = True
                    
                sell_score += volume_confirmation_score
                
            # OBV Divergence
            elif obv_momentum > 0 and price_momentum < 0:  # OBV up, price down
                buy_score += 2 * adx_strength
                signals['obv_bullish_divergence'] = True
            elif obv_momentum < 0 and price_momentum > 0:  # OBV down, price up
                sell_score += 2 * adx_strength
                signals['obv_bearish_divergence'] = True
        
        # === 6. ENHANCED MACD ANALYSIS ===
        macd_signal_strength = 0
        
        if (not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_signal']) and 
            not pd.isna(latest['MACD_hist']) and not pd.isna(prev['MACD_hist'])):
            
            # MACD Histogram momentum
            hist_momentum = latest['MACD_hist'] - prev['MACD_hist']
            
            # MACD Line crossover với histogram confirmation
            if latest['MACD'] > latest['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
                # Bullish crossover strength dựa trên histogram
                if latest['MACD_hist'] > 0 and hist_momentum > 0:  # Strong bullish
                    macd_signal_strength = 4 * adx_strength
                    signals['macd_strong_bullish'] = True
                elif hist_momentum > 0:  # Improving
                    macd_signal_strength = 3 * adx_strength
                    signals['macd_bullish_improving'] = True
                else:  # Weak signal
                    macd_signal_strength = 2 * adx_strength
                    signals['macd_weak_bullish'] = True
                    
                buy_score += macd_signal_strength
                
            elif latest['MACD'] < latest['MACD_signal'] and prev['MACD'] >= prev['MACD_signal']:
                # Bearish crossover
                if latest['MACD_hist'] < 0 and hist_momentum < 0:  # Strong bearish
                    macd_signal_strength = 4 * adx_strength
                    signals['macd_strong_bearish'] = True
                elif hist_momentum < 0:  # Deteriorating
                    macd_signal_strength = 3 * adx_strength
                    signals['macd_bearish_deteriorating'] = True
                else:
                    macd_signal_strength = 2 * adx_strength
                    signals['macd_weak_bearish'] = True
                    
                sell_score += macd_signal_strength
            
            # MACD Zero line analysis
            elif latest['MACD'] > 0 and prev['MACD'] <= 0:  # Cross above zero
                buy_score += 2.5 * adx_strength
                signals['macd_above_zero'] = True
            elif latest['MACD'] < 0 and prev['MACD'] >= 0:  # Cross below zero
                sell_score += 2.5 * adx_strength
                signals['macd_below_zero'] = True
        
        # === 7. FIBONACCI RETRACEMENT ANALYSIS ===
        fibonacci_signal_strength = 0
        
        if (not pd.isna(latest['fib_236']) and not pd.isna(latest['fib_382']) and 
            not pd.isna(latest['fib_500']) and not pd.isna(latest['fib_618'])):
            
            current_price = latest['close']
            fib_levels = [
                ('23.6%', latest['fib_236']),
                ('38.2%', latest['fib_382']),
                ('50.0%', latest['fib_500']),
                ('61.8%', latest['fib_618'])
            ]
            
            # Check if price is near any Fibonacci level
            for fib_name, fib_level in fib_levels:
                price_distance = abs(current_price - fib_level) / current_price
                
                if price_distance < 0.008:  # Within 0.8% of Fibonacci level
                    # Fibonacci bounce/rejection signals
                    if current_price > prev['close']:  # Price bouncing up
                        if fib_name in ['38.2%', '50.0%', '61.8%']:  # Strong support levels
                            fibonacci_signal_strength = 3 * adx_strength
                            signals[f'fib_{fib_name}_bounce'] = True
                        else:
                            fibonacci_signal_strength = 2 * adx_strength
                            signals[f'fib_{fib_name}_mild_bounce'] = True
                            
                        buy_score += fibonacci_signal_strength
                        
                    elif current_price < prev['close']:  # Price rejecting down
                        if fib_name in ['38.2%', '50.0%', '61.8%']:  # Strong resistance levels
                            fibonacci_signal_strength = 3 * adx_strength
                            signals[f'fib_{fib_name}_rejection'] = True
                        else:
                            fibonacci_signal_strength = 2 * adx_strength
                            signals[f'fib_{fib_name}_mild_rejection'] = True
                            
                        sell_score += fibonacci_signal_strength
                    break
        
        # === 8. ENHANCED CANDLESTICK PATTERN ANALYSIS ===
        candlestick_signal_strength = 0
        
        # Bullish patterns với context
        bullish_patterns = ['hammer', 'engulfing_bullish', 'morning_star']
        for pattern in bullish_patterns:
            if pattern in latest and latest[pattern] > 0:
                # Pattern strength dựa trên vị trí và volume
                pattern_strength = 2.5
                
                # Bonus nếu pattern xuất hiện ở support level
                if (not pd.isna(latest['support']) and 
                    abs(latest['close'] - latest['support']) / latest['close'] < 0.015):
                    pattern_strength *= 1.5
                    signals[f'{pattern}_at_support'] = True
                
                # Volume confirmation
                if not pd.isna(latest['volume_ratio']) and latest['volume_ratio'] > 1.2:
                    pattern_strength *= 1.2
                    signals[f'{pattern}_volume_confirm'] = True
                
                candlestick_signal_strength += pattern_strength * adx_strength
                signals[f'bullish_{pattern}'] = True
        
        if candlestick_signal_strength > 0:
            buy_score += candlestick_signal_strength
        
        # Bearish patterns
        bearish_patterns = ['hanging_man', 'evening_star']
        candlestick_signal_strength = 0
        
        for pattern in bearish_patterns:
            if pattern in latest and latest[pattern] < 0:  # Bearish patterns are negative
                pattern_strength = 2.5
                
                # Bonus nếu pattern xuất hiện ở resistance level
                if (not pd.isna(latest['resistance']) and 
                    abs(latest['close'] - latest['resistance']) / latest['close'] < 0.015):
                    pattern_strength *= 1.5
                    signals[f'{pattern}_at_resistance'] = True
                
                # Volume confirmation
                if not pd.isna(latest['volume_ratio']) and latest['volume_ratio'] > 1.2:
                    pattern_strength *= 1.2
                
                candlestick_signal_strength += pattern_strength * adx_strength
                signals[f'bearish_{pattern}'] = True
        
        if candlestick_signal_strength > 0:
            sell_score += candlestick_signal_strength
        
        # Doji indecision penalty
        if 'doji' in latest and latest['doji'] != 0:
            buy_score *= 0.7
            sell_score *= 0.7
            signals['doji_indecision'] = True
        
        # === 9. PIVOT POINTS ANALYSIS ===
        pivot_signal_strength = 0
        
        if (not pd.isna(latest.get('pivot', pd.NA)) and not pd.isna(latest.get('r1', pd.NA)) and 
            not pd.isna(latest.get('s1', pd.NA))):
            
            current_price = latest['close']
            pivot_levels = [
                ('R3', latest.get('r3', latest.get('r1', 0) * 1.1)),
                ('R2', latest.get('r2', latest.get('r1', 0) * 1.05)),
                ('R1', latest.get('r1', 0)),
                ('PIVOT', latest.get('pivot', 0)),
                ('S1', latest.get('s1', 0)),
                ('S2', latest.get('s2', latest.get('s1', 0) * 0.95)),
                ('S3', latest.get('s3', latest.get('s1', 0) * 0.9))
            ]
            
            for level_name, level_price in pivot_levels:
                if pd.isna(level_price) or level_price == 0:
                    continue
                    
                price_distance = abs(current_price - level_price) / current_price
                
                if price_distance < 0.01:  # Within 1% of pivot level
                    if current_price > prev['close']:  # Bouncing up from support
                        if level_name in ['S1', 'S2', 'S3', 'PIVOT']:
                            pivot_signal_strength = 3 * adx_strength
                            signals[f'pivot_{level_name}_bounce'] = True
                            buy_score += pivot_signal_strength
                            
                    elif current_price < prev['close']:  # Rejecting down from resistance
                        if level_name in ['R1', 'R2', 'R3', 'PIVOT']:
                            pivot_signal_strength = 3 * adx_strength
                            signals[f'pivot_{level_name}_rejection'] = True
                            sell_score += pivot_signal_strength
                    break
        
        # === 10. MARKET STRUCTURE ANALYSIS ===
        # Apply sideway penalty and trend quality bonuses
        buy_score *= sideway_penalty
        sell_score *= sideway_penalty
        
        # Trend quality bonus
        if trend_quality == "VERY_STRONG":
            if buy_score > sell_score:
                buy_score *= 1.2
            else:
                sell_score *= 1.2
        
        # === 11. FINAL SIGNAL CONSENSUS CHECK ===
        # Multi-timeframe consensus bonus (if available from previous analysis)
        signal_consensus = 0
        strong_signals = ['ichimoku_bullish_cross', 'perfect_bullish_alignment', 
                         'macd_strong_bullish', 'fib_50.0%_bounce', 'obv_price_bullish_confirm']
        
        consensus_count = sum(1 for signal in strong_signals if signals.get(signal, False))
        if consensus_count >= 3:  # At least 3 strong bullish signals
            buy_score *= 1.15  # Consensus bonus
            signals['strong_bullish_consensus'] = True
        
        strong_bearish_signals = ['ichimoku_bearish_cross', 'perfect_bearish_alignment',
                                'macd_strong_bearish', 'fib_50.0%_rejection', 'obv_price_bearish_confirm']
        
        bearish_consensus_count = sum(1 for signal in strong_bearish_signals if signals.get(signal, False))
        if bearish_consensus_count >= 3:
            sell_score *= 1.15
            signals['strong_bearish_consensus'] = True
        
        return buy_score, sell_score, signals
        
        # RSI Signals (Trọng số điều chỉnh)
        if latest['RSI'] < 30 and latest['RSI'] > prev['RSI']:
            buy_score += 2.5 * adx_strength
            signals['RSI_oversold_recovery'] = True
        elif latest['RSI'] > 70 and latest['RSI'] < prev['RSI']:
            sell_score += 2.5 * adx_strength
            signals['RSI_overbought_decline'] = True
        
        # RSI Divergence (simplified)
        if (latest['close'] < prev2['close'] and latest['RSI'] > prev2['RSI'] and latest['RSI'] < 50):
            buy_score += 2.5 * adx_strength
            signals['RSI_bullish_divergence'] = True
        elif (latest['close'] > prev2['close'] and latest['RSI'] < prev2['RSI'] and latest['RSI'] > 50):
            sell_score += 2.5 * adx_strength
            signals['RSI_bearish_divergence'] = True
        
        # MACD Signals (Strengthened with trend confirmation)
        if not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_signal']):
            # MACD crossover with histogram confirmation
            if latest['MACD'] > latest['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
                macd_strength = 3 if latest['MACD_hist'] > prev['MACD_hist'] else 2
                buy_score += macd_strength * adx_strength
                signals['MACD_bullish_cross'] = True
            elif latest['MACD'] < latest['MACD_signal'] and prev['MACD'] >= prev['MACD_signal']:
                macd_strength = 3 if latest['MACD_hist'] < prev['MACD_hist'] else 2
                sell_score += macd_strength * adx_strength
                signals['MACD_bearish_cross'] = True
        
        # === 3. VOLUME ANALYSIS (Nâng cao với OBV) ===
        
        # On-Balance Volume confirmation
        obv_bullish = False
        obv_bearish = False
        if not pd.isna(latest['OBV']) and not pd.isna(latest['OBV_sma']):
            if latest['OBV'] > latest['OBV_sma'] and prev['OBV'] <= prev['OBV_sma']:
                obv_bullish = True
                signals['OBV_bullish'] = True
            elif latest['OBV'] < latest['OBV_sma'] and prev['OBV'] >= prev['OBV_sma']:
                obv_bearish = True
                signals['OBV_bearish'] = True
        
        # Volume + Price confirmation (Nâng cao)
        if latest['volume_ratio'] > 1.5:  # High volume
            if latest['close'] > prev['close']:
                volume_score = 2 if obv_bullish else 1.5
                buy_score += volume_score * adx_strength
                signals['volume_bullish_confirmation'] = True
            elif latest['close'] < prev['close']:
                volume_score = 2 if obv_bearish else 1.5
                sell_score += volume_score * adx_strength
                signals['volume_bearish_confirmation'] = True
        
        # === 4. SUPPORT/RESISTANCE + FIBONACCI ===
        
        # Fibonacci Support/Resistance
        fib_support_bounce = False
        fib_resistance_reject = False
        
        if not pd.isna(latest['fib_382']) and not pd.isna(latest['fib_618']):
            # Price near Fibonacci support levels
            fib_levels = [latest['fib_236'], latest['fib_382'], latest['fib_500'], latest['fib_618']]
            for fib_level in fib_levels:
                if abs(latest['close'] - fib_level) / latest['close'] < 0.01:  # Within 1%
                    if latest['close'] > prev['close']:  # Bouncing from support
                        buy_score += 2 * adx_strength
                        fib_support_bounce = True
                        signals['fibonacci_support_bounce'] = True
                        break
                    elif latest['close'] < prev['close']:  # Rejected at resistance
                        sell_score += 2 * adx_strength
                        fib_resistance_reject = True
                        signals['fibonacci_resistance_reject'] = True
                        break
        
        # Traditional Support/Resistance
        price_near_support = abs(latest['close'] - latest['support']) / latest['close'] < 0.015
        price_near_resistance = abs(latest['close'] - latest['resistance']) / latest['close'] < 0.015
        
        if price_near_support and latest['close'] > prev['close'] and not fib_support_bounce:
            buy_score += 1.5 * adx_strength
            signals['support_bounce'] = True
        elif price_near_resistance and latest['close'] < prev['close'] and not fib_resistance_reject:
            sell_score += 1.5 * adx_strength
            signals['resistance_rejection'] = True
        
        # === 5. CANDLESTICK PATTERNS ===
        
        # Bullish patterns
        if latest['hammer'] > 0 or latest['engulfing_bullish'] > 0 or latest['morning_star'] > 0:
            buy_score += 2 * adx_strength
            signals['bullish_candlestick'] = True
        
        # Bearish patterns
        if latest['hanging_man'] < 0 or latest['evening_star'] < 0:
            sell_score += 2 * adx_strength
            signals['bearish_candlestick'] = True
        
        # Doji (indecision - reduce both scores)
        if latest['doji'] != 0:
            buy_score *= 0.8
            sell_score *= 0.8
            signals['doji_indecision'] = True
        
        # === 6. PENALTY FOR SIDEWAY MARKET ===
        if is_sideway:
            buy_score *= 0.5  # Giảm mạnh tín hiệu trong sideway
            sell_score *= 0.5
        
        return buy_score, sell_score, signals
    
    def analyze_trend_strength(self, trends, volume_analysis):
        """Phân tích sức mạnh xu hướng với volume"""
        if not trends:
            return 0, "UNKNOWN"
        
        uptrend_count = sum(1 for trend in trends.values() if 'UPTREND' in trend)
        downtrend_count = sum(1 for trend in trends.values() if 'DOWNTREND' in trend)
        strong_uptrend_count = sum(1 for trend in trends.values() if trend == 'STRONG_UPTREND')
        strong_downtrend_count = sum(1 for trend in trends.values() if trend == 'STRONG_DOWNTREND')
        
        # Tính volume bonus
        volume_bonus = 0
        for tf, vol_data in volume_analysis.items():
            if vol_data['trend'] in ['HIGH', 'ELEVATED']:
                if vol_data['price_change'] > 0:
                    volume_bonus += 0.05
                elif vol_data['price_change'] < 0:
                    volume_bonus -= 0.05
        
        if strong_uptrend_count >= 2 or (uptrend_count >= 2 and volume_bonus > 0.1):
            return (uptrend_count * 0.15) + volume_bonus, "STRONG_UP"
        elif uptrend_count >= 2:
            return (uptrend_count * 0.1) + volume_bonus, "STRONG_UP"
        elif strong_downtrend_count >= 2 or (downtrend_count >= 2 and volume_bonus < -0.1):
            return (downtrend_count * 0.15) + volume_bonus, "STRONG_DOWN"
        elif downtrend_count >= 2:
            return (downtrend_count * 0.1) + volume_bonus, "STRONG_DOWN"
        else:
            return volume_bonus, "MIXED"
    
    def predict_enhanced_probability(self, buy_score, sell_score, trends, rsi_value, volume_ratio, volume_analysis, 
                                   main_timeframe='15m', df_main=None):
        """Dự đoán xác suất thành công với Weighted Multi-Timeframe Analysis"""
        signal_type = 'BUY'
        max_score = buy_score
        
        # Nếu sell_score cao hơn buy_score, chờ cơ hội tốt hơn
        if sell_score > buy_score:
            max_score = 0
            signal_type = 'WAIT'
        
        # Base probability từ signal score
        if signal_type == 'BUY':
            base_prob = min(max_score / 20.0, 0.7)  # Điều chỉnh do có nhiều chỉ báo hơn
        else:
            base_prob = 0
        
        # === WEIGHTED MULTI-TIMEFRAME ANALYSIS ===
        # Trọng số cho các khung thời gian
        timeframe_weights = {
            '15m': 0.4 if main_timeframe == '15m' else 0.2,
            '1h': 0.3 if main_timeframe == '1h' else 0.25,
            '4h': 0.2 if main_timeframe == '4h' else 0.35,
            '1d': 0.1 if main_timeframe == '1d' else 0.2
        }
        
        # Tính trend consensus với trọng số
        weighted_trend_score = 0
        total_weight = 0
        
        for tf, trend in trends.items():
            weight = timeframe_weights.get(tf, 0.1)
            total_weight += weight
            
            if 'STRONG_UPTREND' in trend:
                weighted_trend_score += 2 * weight
            elif 'UPTREND' in trend:
                weighted_trend_score += 1 * weight
            elif 'STRONG_DOWNTREND' in trend:
                weighted_trend_score -= 2 * weight
            elif 'DOWNTREND' in trend:
                weighted_trend_score -= 1 * weight
        
        if total_weight > 0:
            weighted_trend_score /= total_weight
        
        # Trend bonus dựa trên weighted score
        trend_bonus = 0
        trend_strength = "MIXED"
        
        if weighted_trend_score >= 1.5:
            trend_bonus = 0.25
            trend_strength = "STRONG_UP"
        elif weighted_trend_score >= 0.8:
            trend_bonus = 0.15
            trend_strength = "STRONG_UP"
        elif weighted_trend_score <= -1.5:
            trend_bonus = -0.3
            trend_strength = "WAIT_FOR_UPTREND"
        elif weighted_trend_score <= -0.8:
            trend_bonus = -0.2
            trend_strength = "STRONG_DOWN"
        else:
            trend_bonus = weighted_trend_score * 0.1
            trend_strength = "MIXED"
        
        # === ADVANCED SIGNAL CONFIRMATIONS ===
        confirmation_bonus = 0
        
        if df_main is not None and len(df_main) > 0:
            latest = df_main.iloc[-1]
            
            # ADX confirmation (xu hướng mạnh)
            if not pd.isna(latest['ADX']) and latest['ADX'] > 25:
                if signal_type == 'BUY' and trend_strength in ["STRONG_UP"]:
                    confirmation_bonus += 0.1
            
            # Ichimoku Cloud confirmation
            if not pd.isna(latest['senkou_span_a']) and not pd.isna(latest['senkou_span_b']):
                cloud_top = max(latest['senkou_span_a'], latest['senkou_span_b'])
                if signal_type == 'BUY' and latest['close'] > cloud_top:
                    confirmation_bonus += 0.08
            
            # Stochastic confirmation
            if not pd.isna(latest['stoch_k']) and signal_type == 'BUY':
                if latest['stoch_k'] < 20:  # Oversold area
                    confirmation_bonus += 0.05
                elif latest['stoch_k'] > 80:  # Overbought area
                    confirmation_bonus -= 0.1
            
            # Volume flow confirmation (OBV)
            if not pd.isna(latest['OBV']) and not pd.isna(latest['OBV_sma']):
                if signal_type == 'BUY' and latest['OBV'] > latest['OBV_sma']:
                    confirmation_bonus += 0.06
            
            # Bollinger Band position
            if not pd.isna(latest['BB_lower']) and not pd.isna(latest['BB_upper']):
                bb_position = (latest['close'] - latest['BB_lower']) / (latest['BB_upper'] - latest['BB_lower'])
                if signal_type == 'BUY' and bb_position < 0.2:  # Near lower band (oversold)
                    confirmation_bonus += 0.05
        
        # RSI bonus (refined)
        rsi_bonus = 0
        if signal_type == 'BUY':
            if rsi_value < 25:  # Deep oversold
                rsi_bonus = 0.2
            elif 25 <= rsi_value <= 40:  # Moderate oversold
                rsi_bonus = 0.15
            elif 40 < rsi_value <= 55:  # Neutral bullish
                rsi_bonus = 0.05
            elif rsi_value > 75:  # Overbought
                rsi_bonus = -0.2
        
        # Volume analysis với trọng số đa khung thời gian
        volume_bonus = 0
        volume_consistency = 0
        
        for tf, vol_data in volume_analysis.items():
            tf_weight = timeframe_weights.get(tf, 0.1)
            
            if vol_data['trend'] in ['HIGH', 'ELEVATED']:
                if vol_data['price_change'] > 0 and signal_type == 'BUY':
                    volume_bonus += 0.05 * tf_weight
                    volume_consistency += tf_weight
                elif vol_data['price_change'] < 0:
                    volume_bonus -= 0.03 * tf_weight
        
        # Multi-timeframe volume consistency bonus
        if volume_consistency >= 0.6:  # Consistency across timeframes
            volume_bonus += 0.08
        
        # Score difference bonus (signal strength)
        score_diff = buy_score - sell_score
        if score_diff > 8:  # Strong signal separation
            score_bonus = 0.15
        elif score_diff > 5:
            score_bonus = 0.1
        elif score_diff < -3:
            score_bonus = -0.2
        else:
            score_bonus = 0
        
        # === RISK MANAGEMENT PENALTIES ===
        risk_penalty = 0
        
        # Sideway market penalty
        if df_main is not None and len(df_main) > 0:
            latest = df_main.iloc[-1]
            if not pd.isna(latest['BB_width']) and not pd.isna(latest['BB_width_sma']):
                if latest['BB_width'] < latest['BB_width_sma'] * 0.7:  # Very narrow range
                    risk_penalty += 0.15
        
        # Time of analysis penalty (market hours consideration)
        current_hour = datetime.now().hour
        if 2 <= current_hour <= 6:  # Low liquidity hours
            risk_penalty += 0.05
        
        # Final probability calculation
        final_prob = max(0, min(
            base_prob + trend_bonus + rsi_bonus + volume_bonus + 
            score_bonus + confirmation_bonus - risk_penalty, 
            0.95
        ))
        
        return final_prob, signal_type, trend_strength
    
    def analyze_single_pair_by_investment_type(self, symbol, investment_type='60m'):
        """Phân tích một cặp coin theo kiểu đầu tư"""
        investment_config = self.investment_types[investment_type]
        main_timeframe = investment_config['timeframe']
        analysis_timeframes = investment_config['analysis_timeframes']
        
        # Lấy dữ liệu khung thời gian chính
        df_main = self.get_kline_data(symbol, main_timeframe, 200)
        if df_main is None:
            return None
        
        df_main = self.calculate_advanced_indicators(df_main)
        if df_main is None:
            return None
        
        # Kiểm tra kết quả dự đoán trước đó
        current_price = df_main.iloc[-1]['close']
        prediction_results = self.tracker.check_predictions(symbol, current_price)
        
        # Phân tích xu hướng và volume đa khung thời gian
        trends = {}
        volume_analysis = {}
        
        for tf in analysis_timeframes:
            df = self.get_kline_data(symbol, tf, 100)
            if df is not None:
                df = self.calculate_advanced_indicators(df)
                if df is not None and len(df) > 0:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    
                    # Phân tích xu hướng giá
                    if not pd.isna(latest['EMA_10']) and not pd.isna(latest['EMA_20']):
                        if latest['EMA_10'] > latest['EMA_20'] and latest['close'] > latest['EMA_10']:
                            price_trend = 'UPTREND'
                        elif latest['EMA_10'] < latest['EMA_20'] and latest['close'] < latest['EMA_10']:
                            price_trend = 'DOWNTREND'
                        else:
                            price_trend = 'SIDEWAYS'
                    else:
                        price_trend = 'UNKNOWN'
                    
                    trends[tf] = price_trend
                    
                    # Phân tích volume
                    if not pd.isna(latest['volume_ratio']):
                        if latest['volume_ratio'] > 2.0:
                            volume_trend = 'HIGH'
                        elif latest['volume_ratio'] > 1.5:
                            volume_trend = 'ELEVATED'
                        elif latest['volume_ratio'] > 0.8:
                            volume_trend = 'NORMAL'
                        else:
                            volume_trend = 'LOW'
                        
                        price_change = ((latest['close'] - prev['close']) / prev['close']) * 100
                        volume_analysis[tf] = {
                            'trend': volume_trend,
                            'ratio': latest['volume_ratio'],
                            'price_change': price_change
                        }
            
            time.sleep(0.5)  # Rate limit
        
        # Tính điểm tín hiệu nâng cao
        buy_score, sell_score, signals = self.calculate_enhanced_signal_score(df_main)
        
        latest = df_main.iloc[-1]
        
        # Dự đoán xác suất thành công với weighted multi-timeframe analysis
        success_prob, signal_type, trend_strength = self.predict_enhanced_probability(
            buy_score, sell_score, trends, latest['RSI'], latest['volume_ratio'], 
            volume_analysis, main_timeframe, df_main
        )
        
        # Entry price = current price
        entry_price = current_price

        # Tính TP/SL dựa trên investment_type với Fibonacci và technical levels
        tp1, tp2, stop_loss = self.calculate_tp_sl_by_investment_type(
            entry_price, signal_type, latest['ATR'], trend_strength, investment_type, df_main
        )
        
        # Risk/Reward ratio - chỉ tính cho BUY
        if signal_type == 'BUY':
            rr_ratio = (tp1 - entry_price) / (entry_price - stop_loss)
        else:  # WAIT
            rr_ratio = 0  # Không trade
        
        result = {
            'symbol': symbol,
            'investment_type': investment_type,
            'timeframe': main_timeframe,
            'hold_duration': investment_config['hold_duration'],
            'current_price': current_price,
            'entry_price': entry_price,
            'signal_type': signal_type,
            'buy_score': buy_score,
            'sell_score': sell_score,
            'success_probability': success_prob,
            'trends': trends,
            'trend_strength': trend_strength,
            'tp1': tp1,
            'tp2': tp2,
            'stop_loss': stop_loss,
            'rr_ratio': rr_ratio,
            'rsi': latest['RSI'],
            'atr': latest['ATR'],
            'signals': signals,
            'entry_quality': 'HIGH' if success_prob > 0.75 else 'MEDIUM' if success_prob > 0.6 else 'LOW',
            'prediction_results': prediction_results,
            'volume_analysis': volume_analysis,
        }
        
        # Lưu dự đoán mới
        prediction_data = {
            'current_price': current_price,
            'entry_price': entry_price,
            'signal_type': signal_type,
            'success_probability': success_prob,
            'tp1': tp1,
            'tp2': tp2,
            'stop_loss': stop_loss,
            'trend_strength': trend_strength,
            'entry_quality': result['entry_quality'],
            'investment_type': investment_type
        }
        self.tracker.add_prediction(symbol, prediction_data)
        
        return result
    
    def analyze_single_pair_enhanced(self, symbol):
        """Phân tích nâng cao một cặp coin"""
        #print(f"{Fore.BLUE}📊 Analyzing {symbol}...{Style.RESET_ALL}")
        
        # Lấy dữ liệu 15m
        df_15m = self.get_kline_data(symbol, '15m', 200)
        if df_15m is None:
            return None
        
        df_15m = self.calculate_advanced_indicators(df_15m)
        if df_15m is None:
            return None
        
        # Kiểm tra kết quả dự đoán trước đó
        current_price = df_15m.iloc[-1]['close']
        prediction_results = self.tracker.check_predictions(symbol, current_price)
        
        # Phân tích xu hướng và volume đa khung thời gian
        trends = {}
        volume_analysis = {}
        timeframes = ['1h', '4h', '1d']
        
        for tf in timeframes:
            df = self.get_kline_data(symbol, tf, 100)
            if df is not None:
                df = self.calculate_advanced_indicators(df)
                if df is not None and len(df) > 0:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    
                    # Phân tích xu hướng giá
                    if not pd.isna(latest['EMA_10']) and not pd.isna(latest['EMA_20']):
                        if latest['EMA_10'] > latest['EMA_20'] and latest['close'] > latest['EMA_10']:
                            price_trend = 'UPTREND'
                        elif latest['EMA_10'] < latest['EMA_20'] and latest['close'] < latest['EMA_10']:
                            price_trend = 'DOWNTREND'
                        else:
                            price_trend = 'SIDEWAYS'
                    else:
                        price_trend = 'UNKNOWN'
                    
                    # Phân tích volume
                    volume_trend = 'NORMAL'
                    volume_strength = 1.0
                    
                    if not pd.isna(latest['volume_ratio']):
                        volume_strength = latest['volume_ratio']
                        if latest['volume_ratio'] > 2.0:
                            volume_trend = 'HIGH'
                        elif latest['volume_ratio'] > 1.5:
                            volume_trend = 'ELEVATED'
                        elif latest['volume_ratio'] < 0.7:
                            volume_trend = 'LOW'
                    
                    # Kết hợp price action và volume
                    price_change = (latest['close'] - prev['close']) / prev['close'] * 100
                    
                    # Xác định xu hướng tổng hợp
                    if price_trend == 'UPTREND' and volume_trend in ['HIGH', 'ELEVATED'] and price_change > 0:
                        trends[tf] = 'STRONG_UPTREND'
                    elif price_trend == 'UPTREND':
                        trends[tf] = 'UPTREND'
                    elif price_trend == 'DOWNTREND' and volume_trend in ['HIGH', 'ELEVATED'] and price_change < 0:
                        trends[tf] = 'STRONG_DOWNTREND'
                    elif price_trend == 'DOWNTREND':
                        trends[tf] = 'DOWNTREND'
                    else:
                        trends[tf] = 'SIDEWAYS'
                    
                    volume_analysis[tf] = {
                        'trend': volume_trend,
                        'strength': volume_strength,
                        'price_change': price_change
                    }
            
            time.sleep(0.5)  # Rate limit
        
        # Tính điểm tín hiệu nâng cao
        buy_score, sell_score, signals = self.calculate_enhanced_signal_score(df_15m)
        
        latest = df_15m.iloc[-1]
        
        # Dự đoán xác suất thành công với weighted analysis
        success_prob, signal_type, trend_strength = self.predict_enhanced_probability(
            buy_score, sell_score, trends, latest['RSI'], latest['volume_ratio'], 
            volume_analysis, '15m', df_15m
        )
        
        # Entry price = current price
        entry_price = current_price

        # Tính TP/SL dựa trên entry_price với enhanced technical analysis
        tp1, tp2, stop_loss = self.calculate_tp_sl_fixed(
            entry_price, signal_type, latest['ATR'], trend_strength, df_15m
        )
        
        # Risk/Reward ratio - chỉ tính cho BUY
        if signal_type == 'BUY':
            rr_ratio = (tp1 - entry_price) / (entry_price - stop_loss)
        else:  # WAIT
            rr_ratio = 0  # Không trade
        
        result = {
            'symbol': symbol,
            'current_price': current_price,
            'entry_price': entry_price,
            'signal_type': signal_type,
            'buy_score': buy_score,
            'sell_score': sell_score,
            'success_probability': success_prob,
            'trends': trends,
            'trend_strength': trend_strength,
            'tp1': tp1,
            'tp2': tp2,
            'stop_loss': stop_loss,
            'rr_ratio': rr_ratio,
            'rsi': latest['RSI'],
            'atr': latest['ATR'],
            'signals': signals,
            'entry_quality': 'HIGH' if success_prob > 0.75 else 'MEDIUM' if success_prob > 0.6 else 'LOW',
            'prediction_results': prediction_results,
            'volume_analysis': volume_analysis,
        }
        
        # Lưu dự đoán mới
        prediction_data = {
            'current_price': current_price,
            'entry_price': entry_price,
            'signal_type': signal_type,
            'success_probability': success_prob,
            'tp1': tp1,
            'tp2': tp2,
            'stop_loss': stop_loss,
            'trend_strength': trend_strength,
            'entry_quality': result['entry_quality']
        }
        self.tracker.add_prediction(symbol, prediction_data)
        
        return result
    

    def display_prediction_history(self, results):
        """Hiển thị lịch sử dự đoán - đã tắt"""
        pass
    
    def run_multi_timeframe_analysis(self, coin_pairs=None):
        """Chạy phân tích cho tất cả các kiểu đầu tư (60m, 4h, 1d)"""
        all_results = {}
        
        # Use provided coin_pairs or fall back to self.pairs
        pairs_to_analyze = coin_pairs if coin_pairs else self.pairs
        
        #print(f"\n{Fore.YELLOW}{Style.BRIGHT}🎯 GỢI Ý COIN TỐT NHẤT CHO TỪNG KHUNG THỜI GIAN{Style.RESET_ALL}")
        #print("=" * 70)
        
        for investment_type in ['60m', '4h', '1d']:
            results = []
            
            for pair in pairs_to_analyze:
                try:
                    result = self.analyze_single_pair_by_investment_type(pair, investment_type)
                    if result:
                        results.append(result)
                    time.sleep(1)  # Rate limit protection
                except Exception as e:
                    print(f"{Fore.RED}❌ Error analyzing {pair} for {investment_type}: {e}{Style.RESET_ALL}")
            
            # Sort by success probability
            results.sort(key=lambda x: x['success_probability'], reverse=True)
            all_results[investment_type] = results
            
            # Display simple recommendation
            if results:
                best = results[0]
                
                #print(f"\n{Fore.CYAN}📈 {investment_type.upper()} ({self.investment_types[investment_type]['hold_duration']}){Style.RESET_ALL}")
                #print(f"Coin: {Fore.YELLOW}{best['symbol']}{Style.RESET_ALL}")
                #print(f"Giá vào lệnh: {Fore.GREEN}{best['entry_price']:.6f}{Style.RESET_ALL}")
                #print(f"SL: {Fore.RED}{best['stop_loss']:.6f}{Style.RESET_ALL}")
                #print(f"TP1: {Fore.GREEN}{best['tp1']:.6f}{Style.RESET_ALL}")
                #print(f"TP2: {Fore.GREEN}{best['tp2']:.6f}{Style.RESET_ALL}")
                #print(f"Tỷ lệ chính xác: {Fore.YELLOW}{best['success_probability']:.1%}{Style.RESET_ALL}")
        
        #print(f"\n{Fore.BLUE}⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        
        return all_results

    def run_enhanced_analysis(self):
        """Chạy phân tích nâng cao"""
        results = []
        
        for pair in self.pairs:
            try:
                result = self.analyze_single_pair_enhanced(pair)
                if result:
                    results.append(result)
                time.sleep(1)  # Rate limit protection
            except Exception as e:
                print(f"{Fore.RED}❌ Error analyzing {pair}: {e}{Style.RESET_ALL}")
        
        # Sort by success probability
        results.sort(key=lambda x: x['success_probability'], reverse=True)
        
        # Display prediction history
        self.display_prediction_history(results)
        
        # Best recommendation
        if results:
            best = results[0]
            #print(f"\n{Fore.YELLOW}{Style.BRIGHT}� COIN TỐT NHẤT (60m){Style.RESET_ALL}")
            #print("=" * 40)
            #print(f"Coin: {Fore.YELLOW}{best['symbol']}{Style.RESET_ALL}")
            #print(f"Giá vào lệnh: {Fore.GREEN}{best['entry_price']:.6f}{Style.RESET_ALL}")
            #print(f"SL: {Fore.RED}{best['stop_loss']:.6f}{Style.RESET_ALL}")
            #print(f"TP1: {Fore.GREEN}{best['tp1']:.6f}{Style.RESET_ALL}")
            #print(f"TP2: {Fore.GREEN}{best['tp2']:.6f}{Style.RESET_ALL}")
            #print(f"Tỷ lệ chính xác: {Fore.YELLOW}{best['success_probability']:.1%}{Style.RESET_ALL}")
        
        #print(f"\n{Fore.BLUE}⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        
        return results

    def set_market_pattern(self, pattern_name):
        """Thiết lập pattern thị trường hiện tại"""
        if pattern_name in self.market_patterns:
            self.active_pattern = pattern_name
            #print(f"{Fore.YELLOW}🎯 Chuyển sang pattern: {self.market_patterns[pattern_name]['name']}{Style.RESET_ALL}")
            return True
        return False
    
    def get_current_pattern(self):
        """Lấy thông tin pattern hiện tại"""
        return self.market_patterns[self.active_pattern]
    
    def get_pattern_adjusted_params(self, base_atr, base_price):
        """Tính toán thông số đã điều chỉnh theo pattern"""
        pattern = self.get_current_pattern()
        
        return {
            'tp1': base_price + (base_atr * pattern['tp1_multiplier']),
            'tp2': base_price + (base_atr * pattern['tp2_multiplier']),
            'sl': base_price - (base_atr * pattern['sl_multiplier']),
            'volume_threshold': pattern['volume_threshold'],
            'success_boost': pattern['success_boost']
        }

    def run_backtest(self, symbol, timeframe='4h', days_back=30, pattern_name=None):
        """
        Chạy backtest thực sự với dữ liệu lịch sử và pattern cụ thể
        """
        try:
            # Thiết lập pattern nếu được chỉ định
            original_pattern = self.active_pattern
            if pattern_name and pattern_name in self.market_patterns:
                self.active_pattern = pattern_name
            
            pattern = self.get_current_pattern()
            
            #print(f"\n{Fore.YELLOW}{Style.BRIGHT}🎯 REAL BACKTEST TRADING SIGNALS{Style.RESET_ALL}")
            #print(f"Symbol: {symbol} | Timeframe: {timeframe} | Days: {days_back}")
            #print(f"Pattern: {pattern['name']} - {pattern['description']}")
            #print("=" * 70)
            
            # Lấy dữ liệu lịch sử thực
            limit = self._calculate_limit_for_timeframe(timeframe, days_back)
            df = self.get_kline_data(symbol, timeframe, limit)
            
            if df is None or len(df) < 50:
                #print(f"{Fore.RED}❌ Không đủ dữ liệu cho backtest{Style.RESET_ALL}")
                return None
            
            # Tính indicators dựa trên pattern
            df['ema_fast'] = calculate_ema(df['close'], pattern['ema_fast'])
            df['ema_slow'] = calculate_ema(df['close'], pattern['ema_slow'])
            df['rsi'] = calculate_rsi(df['close'], 14)
            df['atr'] = self._calculate_atr(df, 14)
            
            # Tạo signals dựa trên pattern
            signals = []
            for i in range(50, len(df) - 1):  # Bỏ qua 50 nến đầu để có đủ data cho indicators
                current = df.iloc[i]
                prev = df.iloc[i-1]
                
                # Logic tạo signal dựa trên pattern
                signal_created = False
                
                # Điều kiện cơ bản cho BUY signal
                ema_signal = current['ema_fast'] > current['ema_slow']
                rsi_signal = pattern['rsi_oversold'] < current['rsi'] < pattern['rsi_overbought']
                volume_signal = current['volume'] > df['volume'].rolling(20).mean().iloc[i] * pattern['volume_multiplier']
                
                # Tạo signal dựa trên pattern cụ thể
                if pattern_name == "bull_market":
                    signal_created = ema_signal and current['rsi'] > 40
                elif pattern_name == "bear_market":
                    signal_created = ema_signal and current['rsi'] > 50 and volume_signal
                elif pattern_name == "sideways":
                    signal_created = abs(current['ema_fast'] - current['ema_slow']) < current['close'] * 0.01 and rsi_signal
                elif pattern_name == "high_volatility":
                    signal_created = ema_signal and current['atr'] > df['atr'].rolling(20).mean().iloc[i] * 1.5
                elif pattern_name == "low_volatility":
                    signal_created = ema_signal and rsi_signal and current['atr'] < df['atr'].rolling(20).mean().iloc[i] * 0.8
                elif pattern_name == "breakout":
                    # Breakout từ consolidation
                    high_20 = df['high'].rolling(20).max().iloc[i-1]
                    signal_created = current['close'] > high_20 * 1.02  # Break above 20-period high
                elif pattern_name == "scalping":
                    signal_created = ema_signal and 45 < current['rsi'] < 55 and volume_signal
                else:  # default
                    signal_created = ema_signal and rsi_signal
                
                if signal_created:
                    entry_price = current['close']
                    tp1 = entry_price * (1 + (2 * pattern['tp1_multiplier']) / 100)
                    tp2 = entry_price * (1 + (4 * pattern['tp2_multiplier']) / 100)
                    stop_loss = entry_price * (1 - (2 * pattern['sl_multiplier']) / 100)
                    
                    signals.append({
                        'entry_index': i,
                        'entry_time': pd.to_datetime(current['timestamp'], unit='ms'),
                        'entry_price': entry_price,
                        'tp1': tp1,
                        'tp2': tp2,
                        'stop_loss': stop_loss
                    })
            
            if not signals:
                return {
                    'symbol': symbol,
                    'total_trades': 0,
                    'message': f'Không có signal nào được tạo với pattern {pattern["name"]} trong {days_back} ngày'
                }
            
            # Simulate trades dựa trên signals thực
            trades = []
            for signal in signals:
                trade = self._simulate_trade(signal, df, pattern)
                if trade:
                    trades.append(trade)
            
            if not trades:
                return {
                    'symbol': symbol,
                    'total_trades': 0,
                    'message': 'Không có trade nào được thực hiện'
                }
            
            # Tính toán kết quả thực
            winning_trades = sum(1 for t in trades if t['pnl_percent'] > 0)
            losing_trades = len(trades) - winning_trades
            win_rate = (winning_trades / len(trades)) * 100 if trades else 0
            
            total_pnl = sum(t['pnl_percent'] for t in trades)
            avg_win = sum(t['pnl_percent'] for t in trades if t['pnl_percent'] > 0) / max(winning_trades, 1)
            avg_loss = sum(t['pnl_percent'] for t in trades if t['pnl_percent'] < 0) / max(losing_trades, 1) if losing_trades > 0 else 0
            
            # Tính Profit Factor
            total_profit = sum(t['pnl_percent'] for t in trades if t['pnl_percent'] > 0)
            total_loss = abs(sum(t['pnl_percent'] for t in trades if t['pnl_percent'] < 0))
            profit_factor = total_profit / max(total_loss, 0.01)  # Avoid division by zero
            
            # Average PnL percent
            avg_pnl_percent = total_pnl / len(trades) if trades else 0
            
            # Phân loại theo exit reason
            tp1_hits = sum(1 for t in trades if t['exit_reason'] == 'TP1')
            sl_hits = sum(1 for t in trades if t['exit_reason'] == 'STOP_LOSS')
            timeouts = sum(1 for t in trades if t['exit_reason'] == 'TIMEOUT')
            
            # Tính điểm performance thực
            performance_score = (win_rate * 0.4) + (profit_factor * 20) + (avg_pnl_percent * 2)
            performance_score = max(0, min(100, performance_score))  # Clamp between 0-100
            
            results = {
                'symbol': symbol,
                'timeframe': timeframe,
                'days_back': days_back,
                'pattern_name': pattern_name or 'default',
                'pattern_info': pattern,
                'total_trades': len(trades),
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_factor': round(profit_factor, 2),
                'avg_pnl_percent': round(avg_pnl_percent, 2),
                'tp1_hits': tp1_hits,
                'sl_hits': sl_hits,
                'timeouts': timeouts,
                'performance_score': round(performance_score, 2),
                'trades': trades[-10:],  # 10 giao dịch gần nhất
                'best_trade': max(trades, key=lambda x: x['pnl_percent']) if trades else None,
                'worst_trade': min(trades, key=lambda x: x['pnl_percent']) if trades else None
            }
            
            # Display results
            #print(f"\n{Fore.CYAN}📊 KẾT QUẢ BACKTEST THỰC{Style.RESET_ALL}")
            #print(f"Pattern: {pattern['name']}")
            #print(f"Signals generated: {len(signals)}")
            #print(f"Trades executed: {len(trades)}")
            #print(f"Thắng: {winning_trades} | Thua: {losing_trades}")
            #print(f"Tỷ lệ thắng: {win_rate:.1f}%")
            #print(f"PnL tổng: {total_pnl:+.2f}%")
            #print(f"Profit Factor: {profit_factor:.2f}")
            #print(f"Avg PnL: {avg_pnl_percent:+.2f}%")
            #print(f"TP1: {tp1_hits} | SL: {sl_hits} | Timeout: {timeouts}")
            #print(f"Performance Score: {performance_score:.2f}/100")
            
            # Khôi phục pattern gốc
            self.active_pattern = original_pattern
            
            return results
            
        except Exception as e:
            # Khôi phục pattern gốc khi có lỗi
            if 'original_pattern' in locals():
                self.active_pattern = original_pattern
            #print(f"{Fore.RED}❌ Lỗi backtest: {e}{Style.RESET_ALL}")
            return None

    def _calculate_limit_for_timeframe(self, timeframe, days_back):
        """Tính limit cần thiết cho mỗi timeframe"""
        timeframe_minutes = {
            '60m': 60,
            '4h': 240,
            '1d': 1440
        }
        
        minutes_in_day = 1440
        total_minutes = days_back * minutes_in_day
        candles_needed = total_minutes // timeframe_minutes.get(timeframe, 240)
        
        # Thêm buffer để đảm bảo đủ data cho indicators
        return min(max(candles_needed + 100, 200), 1000)

    def _calculate_atr(self, df, period=14):
        """Tính Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=period).mean()

    def _simulate_trade(self, signal, df, pattern):
        """Simulate một trade dựa trên signal và pattern"""
        try:
            entry_index = signal['entry_index']
            entry_price = signal['entry_price']
            tp1 = signal['tp1']
            stop_loss = signal['stop_loss']
            
            # Tìm exit point trong data tiếp theo
            max_hold_periods = {
                '60m': 48,  # 48 hours max hold
                '4h': 72,   # 12 days max hold  
                '1d': 30    # 30 days max hold
            }
            
            max_periods = max_hold_periods.get('4h', 72)  # Default 4h
            exit_index = min(entry_index + max_periods, len(df) - 1)
            
            # Scan từng nến để tìm TP1 hoặc SL
            for i in range(entry_index + 1, exit_index + 1):
                if i >= len(df):
                    break
                    
                current_candle = df.iloc[i]
                
                # Check TP1 hit
                if current_candle['high'] >= tp1:
                    exit_price = tp1
                    exit_reason = 'TP1'
                    pnl_percent = ((exit_price / entry_price) - 1) * 100
                    
                    return {
                        'entry_time': signal['entry_time'].isoformat(),
                        'entry_price': entry_price,
                        'exit_time': pd.to_datetime(current_candle['timestamp'], unit='ms').isoformat(),
                        'exit_price': exit_price,
                        'exit_reason': exit_reason,
                        'pnl_percent': pnl_percent,
                        'tp1': tp1,
                        'stop_loss': stop_loss
                    }
                
                # Check SL hit
                if current_candle['low'] <= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'STOP_LOSS'
                    pnl_percent = ((exit_price / entry_price) - 1) * 100
                    
                    return {
                        'entry_time': signal['entry_time'].isoformat(),
                        'entry_price': entry_price,
                        'exit_time': pd.to_datetime(current_candle['timestamp'], unit='ms').isoformat(),
                        'exit_price': exit_price,
                        'exit_reason': exit_reason,
                        'pnl_percent': pnl_percent,
                        'tp1': tp1,
                        'stop_loss': stop_loss
                    }
            
            # Timeout - exit at market price
            final_candle = df.iloc[exit_index]
            exit_price = final_candle['close']
            exit_reason = 'TIMEOUT'
            pnl_percent = ((exit_price / entry_price) - 1) * 100
            
            return {
                'entry_time': signal['entry_time'].isoformat(),
                'entry_price': entry_price,
                'exit_time': pd.to_datetime(final_candle['timestamp'], unit='ms').isoformat(),
                'exit_price': exit_price,
                'exit_reason': exit_reason,
                'pnl_percent': pnl_percent,
                'tp1': tp1,
                'stop_loss': stop_loss
            }
            
        except Exception as e:
            #print(f"Error simulating trade: {e}")
            return None

def main():
    import sys
    
    try:
        app = EnhancedCryptoPredictionAppV2()
        
        # Kiểm tra arguments để chọn loại phân tích
        if len(sys.argv) > 1 and sys.argv[1] in ['60m', '4h', '1d']:
            # Phân tích cho một kiểu đầu tư cụ thể
            investment_type = sys.argv[1]
            #print(f"{Fore.CYAN}🎯 Chạy phân tích chuyên biệt cho {investment_type.upper()}{Style.RESET_ALL}")
            
            results = []
            for pair in app.pairs:
                result = app.analyze_single_pair_by_investment_type(pair, investment_type)
                if result:
                    results.append(result)
                time.sleep(1)
            
            # Hiển thị kết quả
            if results:
                results.sort(key=lambda x: x['success_probability'], reverse=True)
                best = results[0]
                #print(f"\n{Fore.YELLOW}{Style.BRIGHT}🏆 TOP {investment_type.upper()} RECOMMENDATION{Style.RESET_ALL}")
                #print(f"Symbol: {best['symbol']} | Signal: {best['signal_type']} | Probability: {best['success_probability']:.1%}")
                
        elif len(sys.argv) > 1 and sys.argv[1] == '--multi':
            # Phân tích tất cả các kiểu đầu tư
            all_results = app.run_multi_timeframe_analysis()
            
        else:
            # Mặc định: chạy phân tích 60m (backward compatibility)
            results = app.run_enhanced_analysis()
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Analysis interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Critical error: {e}{Style.RESET_ALL}")

def main_multi_timeframe():
    """Chạy phân tích đa khung thời gian - function riêng cho dễ gọi"""
    try:
        app = EnhancedCryptoPredictionAppV2()
        return app.run_multi_timeframe_analysis()
    except Exception as e:
        #print(f"\n{Fore.RED}❌ Critical error: {e}{Style.RESET_ALL}")
        return None

if __name__ == "__main__":
    main()
