#!/usr/bin/env python3
"""
Enhanced Crypto Analysis với logic sửa đổi và tracking kết quả
"""

import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
import talib
import warnings
import os
import json
from tabulate import tabulate
import colorama
from colorama import Fore, Back, Style

warnings.filterwarnings('ignore')
colorama.init()

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
            print(f"❌ Error calculating accuracy: {e}")
            return 0.0

class EnhancedCryptoPredictionAppV2:
    def __init__(self):
        self.pairs = ['XRPJPY', 'XLMJPY', 'ADAJPY', 'SUIJPY', 'LINKJPY', 'SOLJPY', 'ETHJPY']
        self.base_url = "https://api.binance.com/api/v3/klines"
        self.tracker = PredictionTracker()
        # Các kiểu đầu tư
        self.investment_types = {
            '60m': {'timeframe': '15m', 'analysis_timeframes': ['15m', '1h'], 'hold_duration': '60 minutes'},
            '4h': {'timeframe': '1h', 'analysis_timeframes': ['1h', '4h'], 'hold_duration': '4 hours'}, 
            '1d': {'timeframe': '4h', 'analysis_timeframes': ['4h', '1d'], 'hold_duration': '1 day'}
        }
        

    def get_kline_data(self, symbol, interval='15m', limit=200):
        """Lấy dữ liệu giá từ Binance API với error handling tốt hơn"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
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
            df.set_index('timestamp', inplace=True)
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}❌ Network error for {symbol}: {e}{Style.RESET_ALL}")
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Data error for {symbol}: {e}{Style.RESET_ALL}")
            return None
    
    def calculate_advanced_indicators(self, df):
        """Tính toán các chỉ báo kỹ thuật nâng cao"""
        if df is None or len(df) < 50:
            return None
            
        try:
            # Moving Averages
            df['EMA_10'] = talib.EMA(df['close'], timeperiod=10)
            df['EMA_20'] = talib.EMA(df['close'], timeperiod=20)
            df['EMA_50'] = talib.EMA(df['close'], timeperiod=50)
            
            # Momentum Indicators
            df['RSI'] = talib.RSI(df['close'], timeperiod=14)
            df['MACD'], df['MACD_signal'], df['MACD_hist'] = talib.MACD(df['close'])
            
            # Volatility Indicators
            df['BB_upper'], df['BB_middle'], df['BB_lower'] = talib.BBANDS(df['close'])
            df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # Volume Indicators
            df['volume_sma'] = talib.SMA(df['volume'], timeperiod=20)
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
            df['stoch_k'], df['stoch_d'] = talib.STOCH(df['high'], df['low'], df['close'], 
                                                      fastk_period=14, slowk_period=3, slowd_period=3)
            
            # On-Balance Volume (OBV)
            df['OBV'] = talib.OBV(df['close'], df['volume'])
            df['OBV_sma'] = talib.SMA(df['OBV'], timeperiod=20)
            
            # Average Directional Index (ADX) - Đo sức mạnh xu hướng
            df['ADX'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
            df['DI_plus'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
            df['DI_minus'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
            
            # Bollinger Band Width (để phát hiện thị trường sideway)
            df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
            df['BB_width_sma'] = df['BB_width'].rolling(window=20).mean()
            
            # Fibonacci Retracement Levels (tự động tính)
            df = self.calculate_fibonacci_levels(df)
            
            # Candlestick Pattern Recognition
            df = self.detect_candlestick_patterns(df)
            
            return df
            
        except Exception as e:
            print(f"{Fore.RED}❌ Indicator calculation error: {e}{Style.RESET_ALL}")
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
            df['hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
            df['engulfing_bullish'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
            df['morning_star'] = talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close'])
            
            # Bearish patterns  
            df['hanging_man'] = talib.CDLHANGINGMAN(df['open'], df['high'], df['low'], df['close'])
            df['evening_star'] = talib.CDLEVENINGSTAR(df['open'], df['high'], df['low'], df['close'])
            
            # Reversal patterns
            df['doji'] = talib.CDLDOJI(df['open'], df['high'], df['low'], df['close'])
            
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
        """Tính điểm tín hiệu nâng cao với trọng số thông minh và các chỉ báo mới"""
        if df is None or len(df) < 3:
            return 0, 0, {}
            
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]
        
        buy_score = 0
        sell_score = 0
        signals = {}
        
        # Kiểm tra độ mạnh xu hướng với ADX trước
        adx_strength = 1.0  # Default multiplier
        if not pd.isna(latest['ADX']):
            if latest['ADX'] > 25:  # Xu hướng mạnh
                adx_strength = 1.3
                signals['strong_trend'] = True
            elif latest['ADX'] < 20:  # Xu hướng yếu/sideway
                adx_strength = 0.7
                signals['weak_trend'] = True
        
        # Kiểm tra thị trường sideway với Bollinger Band Width
        is_sideway = False
        if not pd.isna(latest['BB_width']) and not pd.isna(latest['BB_width_sma']):
            if latest['BB_width'] < latest['BB_width_sma'] * 0.8:
                is_sideway = True
                signals['sideway_market'] = True
        
        # === 1. TREND FOLLOWING SIGNALS (Trọng số cao) ===
        
        # Ichimoku Cloud Analysis (Trọng số cao - 4 điểm)
        if not pd.isna(latest['tenkan_sen']) and not pd.isna(latest['kijun_sen']):
            # Tenkan-sen cross Kijun-sen
            if latest['tenkan_sen'] > latest['kijun_sen'] and prev['tenkan_sen'] <= prev['kijun_sen']:
                buy_score += 4 * adx_strength
                signals['ichimoku_bullish_cross'] = True
            elif latest['tenkan_sen'] < latest['kijun_sen'] and prev['tenkan_sen'] >= prev['kijun_sen']:
                sell_score += 4 * adx_strength
                signals['ichimoku_bearish_cross'] = True
            
            # Price above/below Cloud
            if not pd.isna(latest['senkou_span_a']) and not pd.isna(latest['senkou_span_b']):
                cloud_top = max(latest['senkou_span_a'], latest['senkou_span_b'])
                cloud_bottom = min(latest['senkou_span_a'], latest['senkou_span_b'])
                
                if latest['close'] > cloud_top:
                    buy_score += 3 * adx_strength
                    signals['price_above_cloud'] = True
                elif latest['close'] < cloud_bottom:
                    sell_score += 3 * adx_strength
                    signals['price_below_cloud'] = True
        
        # EMA Crossover (Điều chỉnh trọng số)
        if latest['EMA_10'] > latest['EMA_20'] and prev['EMA_10'] <= prev['EMA_20']:
            buy_score += 3.5 * adx_strength
            signals['EMA_bullish_cross'] = True
        elif latest['EMA_10'] < latest['EMA_20'] and prev['EMA_10'] >= prev['EMA_20']:
            sell_score += 3.5 * adx_strength
            signals['EMA_bearish_cross'] = True
        
        # Price vs EMA Alignment (Weighted by trend strength)
        if latest['close'] > latest['EMA_10'] > latest['EMA_20'] > latest['EMA_50']:
            buy_score += 2.5 * adx_strength
            signals['bullish_alignment'] = True
        elif latest['close'] < latest['EMA_10'] < latest['EMA_20'] < latest['EMA_50']:
            sell_score += 2.5 * adx_strength
            signals['bearish_alignment'] = True
        
        # === 2. MOMENTUM SIGNALS (Nâng cao với Stochastic) ===
        
        # Stochastic Oscillator (Độ nhạy cao hơn RSI)
        if not pd.isna(latest['stoch_k']) and not pd.isna(latest['stoch_d']):
            # Stochastic oversold recovery
            if latest['stoch_k'] < 20 and latest['stoch_k'] > prev['stoch_k'] and latest['stoch_k'] > latest['stoch_d']:
                buy_score += 3 * adx_strength
                signals['stoch_oversold_recovery'] = True
            # Stochastic overbought decline  
            elif latest['stoch_k'] > 80 and latest['stoch_k'] < prev['stoch_k'] and latest['stoch_k'] < latest['stoch_d']:
                sell_score += 3 * adx_strength
                signals['stoch_overbought_decline'] = True
        
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
    
    def run_multi_timeframe_analysis(self):
        """Chạy phân tích cho tất cả các kiểu đầu tư (60m, 4h, 1d)"""
        all_results = {}
        
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}🎯 GỢI Ý COIN TỐT NHẤT CHO TỪNG KHUNG THỜI GIAN{Style.RESET_ALL}")
        print("=" * 70)
        
        for investment_type in ['60m', '4h', '1d']:
            results = []
            
            for pair in self.pairs:
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
                
                print(f"\n{Fore.CYAN}📈 {investment_type.upper()} ({self.investment_types[investment_type]['hold_duration']}){Style.RESET_ALL}")
                print(f"Coin: {Fore.YELLOW}{best['symbol']}{Style.RESET_ALL}")
                print(f"Giá vào lệnh: {Fore.GREEN}{best['entry_price']:.6f}{Style.RESET_ALL}")
                print(f"SL: {Fore.RED}{best['stop_loss']:.6f}{Style.RESET_ALL}")
                print(f"TP1: {Fore.GREEN}{best['tp1']:.6f}{Style.RESET_ALL}")
                print(f"TP2: {Fore.GREEN}{best['tp2']:.6f}{Style.RESET_ALL}")
                print(f"Tỷ lệ chính xác: {Fore.YELLOW}{best['success_probability']:.1%}{Style.RESET_ALL}")
        
        print(f"\n{Fore.BLUE}⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        
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
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}� COIN TỐT NHẤT (60m){Style.RESET_ALL}")
            print("=" * 40)
            print(f"Coin: {Fore.YELLOW}{best['symbol']}{Style.RESET_ALL}")
            print(f"Giá vào lệnh: {Fore.GREEN}{best['entry_price']:.6f}{Style.RESET_ALL}")
            print(f"SL: {Fore.RED}{best['stop_loss']:.6f}{Style.RESET_ALL}")
            print(f"TP1: {Fore.GREEN}{best['tp1']:.6f}{Style.RESET_ALL}")
            print(f"TP2: {Fore.GREEN}{best['tp2']:.6f}{Style.RESET_ALL}")
            print(f"Tỷ lệ chính xác: {Fore.YELLOW}{best['success_probability']:.1%}{Style.RESET_ALL}")
        
        print(f"\n{Fore.BLUE}⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        
        return results

def main():
    import sys
    
    try:
        app = EnhancedCryptoPredictionAppV2()
        
        # Kiểm tra arguments để chọn loại phân tích
        if len(sys.argv) > 1 and sys.argv[1] in ['60m', '4h', '1d']:
            # Phân tích cho một kiểu đầu tư cụ thể
            investment_type = sys.argv[1]
            print(f"{Fore.CYAN}🎯 Chạy phân tích chuyên biệt cho {investment_type.upper()}{Style.RESET_ALL}")
            
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
                print(f"\n{Fore.YELLOW}{Style.BRIGHT}🏆 TOP {investment_type.upper()} RECOMMENDATION{Style.RESET_ALL}")
                print(f"Symbol: {best['symbol']} | Signal: {best['signal_type']} | Probability: {best['success_probability']:.1%}")
                
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
        print(f"\n{Fore.RED}❌ Critical error: {e}{Style.RESET_ALL}")
        return None

if __name__ == "__main__":
    main()
