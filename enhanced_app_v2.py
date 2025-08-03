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
            
            return df
            
        except Exception as e:
            print(f"{Fore.RED}❌ Indicator calculation error: {e}{Style.RESET_ALL}")
            return None
    

    def calculate_tp_sl_by_investment_type(self, entry_price, signal_type, atr_value, trend_strength, investment_type='60m'):
        """Tính toán TP/SL theo kiểu đầu tư (60m, 4h, 1d)"""
        
        # Điều chỉnh multiplier theo kiểu đầu tư
        if investment_type == '60m':
            # Scalping/Short-term (giữ 60 phút)
            if trend_strength == "STRONG_UP":
                # Tăng TP cho STRONG_UP để tận dụng momentum
                tp1_multiplier = 2.8  # Tăng từ 2.5 → 2.8
                tp2_multiplier = 4.5  # Tăng từ 4.0 → 4.5
                sl_multiplier = 1.5
            elif trend_strength in ["STRONG_DOWN", "WAIT_FOR_UPTREND"]:
                # Giảm TP cho trend yếu/đảo chiều
                tp1_multiplier = 1.2  # Giảm từ 1.5 → 1.2
                tp2_multiplier = 2.0  # Giảm từ 2.5 → 2.0
                sl_multiplier = 1.0
            else:
                # Giảm TP cho MIXED/Sideway (trend yếu)
                tp1_multiplier = 1.8  # Giảm từ 2.0 → 1.8
                tp2_multiplier = 2.8  # Giảm từ 3.0 → 2.8
                sl_multiplier = 1.2
                
        elif investment_type == '4h':
            # Swing trading (giữ 4 giờ) - Điều chỉnh TP phù hợp với xu hướng
            if trend_strength == "STRONG_UP":
                # Tăng TP cho STRONG_UP để tận dụng momentum mạnh
                tp1_multiplier = 4.2  # Tăng từ 3.5 → 4.2
                tp2_multiplier = 6.5  # Tăng từ 5.5 → 6.5
                sl_multiplier = 1.8
            elif trend_strength in ["STRONG_DOWN", "WAIT_FOR_UPTREND"]:
                # Giảm TP cho trend yếu/đảo chiều
                tp1_multiplier = 1.6  # Giảm từ 2.0 → 1.6
                tp2_multiplier = 2.6  # Giảm từ 3.2 → 2.6
                sl_multiplier = 1.3
            else:
                # Giảm TP cho Sideway/MIXED (trend yếu)
                tp1_multiplier = 2.3  # Giảm từ 2.8 → 2.3
                tp2_multiplier = 3.6  # Giảm từ 4.2 → 3.6
                sl_multiplier = 1.5
                
        elif investment_type == '1d':
            # Position trading (giữ 1 ngày) - TP phù hợp với xu hướng dài hạn
            if trend_strength == "STRONG_UP":
                # Tăng TP cho STRONG_UP để tận dụng xu hướng dài hạn mạnh
                tp1_multiplier = 5.5  # Tăng từ 4.5 → 5.5
                tp2_multiplier = 9.0  # Tăng từ 7.5 → 9.0
                sl_multiplier = 2.2
            elif trend_strength in ["STRONG_DOWN", "WAIT_FOR_UPTREND"]:
                # Giảm TP cho trend yếu/đảo chiều
                tp1_multiplier = 2.2  # Giảm từ 2.8 → 2.2
                tp2_multiplier = 3.6  # Giảm từ 4.5 → 3.6
                sl_multiplier = 1.8
            else:
                # Giảm TP cho Sideway/MIXED (trend yếu)
                tp1_multiplier = 3.0  # Giảm từ 3.5 → 3.0
                tp2_multiplier = 5.2  # Giảm từ 6.0 → 5.2
                sl_multiplier = 2.0
        
        if signal_type == 'BUY':
            # SPOT BUY: Mua thấp, bán cao
            tp1 = entry_price + (atr_value * tp1_multiplier)
            tp2 = entry_price + (atr_value * tp2_multiplier)
            stop_loss = entry_price - (atr_value * sl_multiplier)
        else:  # WAIT
            # Không trade, đặt level thấp để chờ
            tp1 = entry_price + (atr_value * 1.0)
            tp2 = entry_price + (atr_value * 2.0)
            stop_loss = entry_price - (atr_value * 0.5)
        
        return tp1, tp2, stop_loss

    def calculate_tp_sl_fixed(self, entry_price, signal_type, atr_value, trend_strength):
        """Tính toán TP/SL cho SPOT TRADING (chỉ BUY) - backward compatibility"""
        return self.calculate_tp_sl_by_investment_type(entry_price, signal_type, atr_value, trend_strength, '60m')
    
    def calculate_enhanced_signal_score(self, df):
        """Tính điểm tín hiệu nâng cao với trọng số"""
        if df is None or len(df) < 3:
            return 0, 0, {}
            
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]
        
        buy_score = 0
        sell_score = 0
        signals = {}
        
        # 1. Trend Following Signals (Trọng số cao)
        # EMA Crossover
        if latest['EMA_10'] > latest['EMA_20'] and prev['EMA_10'] <= prev['EMA_20']:
            buy_score += 3
            signals['EMA_bullish_cross'] = True
        elif latest['EMA_10'] < latest['EMA_20'] and prev['EMA_10'] >= prev['EMA_20']:
            sell_score += 3
            signals['EMA_bearish_cross'] = True
        
        # Price vs EMA Alignment
        if latest['close'] > latest['EMA_10'] > latest['EMA_20'] > latest['EMA_50']:
            buy_score += 2
            signals['bullish_alignment'] = True
        elif latest['close'] < latest['EMA_10'] < latest['EMA_20'] < latest['EMA_50']:
            sell_score += 2
            signals['bearish_alignment'] = True
        
        # 2. Momentum Signals
        # RSI Signals
        if latest['RSI'] < 30 and latest['RSI'] > prev['RSI']:
            buy_score += 2.5
            signals['RSI_oversold_recovery'] = True
        elif latest['RSI'] > 70 and latest['RSI'] < prev['RSI']:
            sell_score += 2.5
            signals['RSI_overbought_decline'] = True
        
        # RSI Divergence (simplified)
        if (latest['close'] < prev2['close'] and latest['RSI'] > prev2['RSI'] and latest['RSI'] < 50):
            buy_score += 2
            signals['RSI_bullish_divergence'] = True
        elif (latest['close'] > prev2['close'] and latest['RSI'] < prev2['RSI'] and latest['RSI'] > 50):
            sell_score += 2
            signals['RSI_bearish_divergence'] = True
        
        # MACD Signals
        if not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_signal']):
            if latest['MACD'] > latest['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
                buy_score += 2.5
                signals['MACD_bullish_cross'] = True
            elif latest['MACD'] < latest['MACD_signal'] and prev['MACD'] >= prev['MACD_signal']:
                sell_score += 2.5
                signals['MACD_bearish_cross'] = True
        
        # 3. Volume Analysis
        if latest['volume_ratio'] > 1.5:  # High volume
            if latest['close'] > prev['close']:
                buy_score += 1.5
                signals['volume_bullish_confirmation'] = True
            elif latest['close'] < prev['close']:
                sell_score += 1.5
                signals['volume_bearish_confirmation'] = True
        
        # 4. Support/Resistance
        price_near_support = abs(latest['close'] - latest['support']) / latest['close'] < 0.015
        price_near_resistance = abs(latest['close'] - latest['resistance']) / latest['close'] < 0.015
        
        if price_near_support and latest['close'] > prev['close']:
            buy_score += 1.5
            signals['support_bounce'] = True
        elif price_near_resistance and latest['close'] < prev['close']:
            sell_score += 1.5
            signals['resistance_rejection'] = True
        
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
    
    def predict_enhanced_probability(self, buy_score, sell_score, trends, rsi_value, volume_ratio, volume_analysis):
        """Dự đoán xác suất thành công cho SPOT TRADING với volume analysis"""
        signal_type = 'BUY'
        max_score = buy_score
        
        # Nếu sell_score cao hơn buy_score, chờ cơ hội tốt hơn
        if sell_score > buy_score:
            max_score = 0
            signal_type = 'WAIT'
        
        # Base probability
        if signal_type == 'BUY':
            base_prob = min(max_score / 15.0, 0.7)
        else:
            base_prob = 0
        
        # Trend bonus với volume
        trend_bonus, trend_strength = self.analyze_trend_strength(trends, volume_analysis)
        if trend_strength == "STRONG_DOWN":
            trend_bonus = -0.2
            trend_strength = "WAIT_FOR_UPTREND"
        
        # RSI bonus
        rsi_bonus = 0
        if signal_type == 'BUY':
            if rsi_value < 30:
                rsi_bonus = 0.15
            elif 30 <= rsi_value <= 45:
                rsi_bonus = 0.1
            elif rsi_value > 70:
                rsi_bonus = -0.15
        
        # Volume bonus từ analysis đa khung thời gian
        volume_bonus = 0
        volume_consistency = 0
        
        for tf, vol_data in volume_analysis.items():
            if vol_data['trend'] in ['HIGH', 'ELEVATED']:
                if vol_data['price_change'] > 0 and signal_type == 'BUY':
                    volume_bonus += 0.05
                    volume_consistency += 1
                elif vol_data['price_change'] < 0:
                    volume_bonus -= 0.03
        
        # Consistency bonus
        if volume_consistency >= 2:
            volume_bonus += 0.05
        
        # Score difference bonus
        score_diff = buy_score - sell_score
        if score_diff > 5:
            score_bonus = 0.1
        elif score_diff < -2:
            score_bonus = -0.15
        else:
            score_bonus = 0
        
        final_prob = max(0, min(base_prob + trend_bonus + rsi_bonus + volume_bonus + score_bonus, 0.95))
        
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
        
        # Dự đoán xác suất thành công
        success_prob, signal_type, trend_strength = self.predict_enhanced_probability(
            buy_score, sell_score, trends, latest['RSI'], latest['volume_ratio'], volume_analysis
        )
        
        # Entry price = current price
        entry_price = current_price

        # Tính TP/SL dựa trên investment_type
        tp1, tp2, stop_loss = self.calculate_tp_sl_by_investment_type(
            entry_price, signal_type, latest['ATR'], trend_strength, investment_type
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
        
        # Dự đoán xác suất thành công
        success_prob, signal_type, trend_strength = self.predict_enhanced_probability(
            buy_score, sell_score, trends, latest['RSI'], latest['volume_ratio'], volume_analysis
        )
        
        # Entry price = current price
        entry_price = current_price

        # Tính TP/SL dựa trên entry_price
        tp1, tp2, stop_loss = self.calculate_tp_sl_fixed(
            entry_price, signal_type, latest['ATR'], trend_strength
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
