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
        self.pairs = ['XRPJPY', 'XLMJPY', 'ADAJPY', 'SUIJPY']
        self.base_url = "https://api.binance.com/api/v3/klines"
        self.tracker = PredictionTracker()
        

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
    

    def calculate_tp_sl_fixed(self, entry_price, signal_type, atr_value, trend_strength):
        """Tính toán TP/SL cho SPOT TRADING (chỉ BUY)"""
        
        # Điều chỉnh multiplier cho spot trading
        if trend_strength == "STRONG_UP":
            tp1_multiplier = 2.5  # TP cao hơn cho uptrend mạnh
            tp2_multiplier = 4.0  
            sl_multiplier = 1.5   # SL conservative
        elif trend_strength in ["STRONG_DOWN", "WAIT_FOR_UPTREND"]:
            tp1_multiplier = 1.5  # TP conservative trong downtrend
            tp2_multiplier = 2.5
            sl_multiplier = 1.0   # SL tight hơn
        else:
            tp1_multiplier = 2.0
            tp2_multiplier = 3.0
            sl_multiplier = 1.2
        
        if signal_type == 'BUY':
            # SPOT BUY: Mua thấp, bán cao
            tp1 = entry_price + (atr_value * tp1_multiplier)    # Bán một phần
            tp2 = entry_price + (atr_value * tp2_multiplier)    # Bán phần còn lại
            stop_loss = entry_price - (atr_value * sl_multiplier)  # Cắt lỗ nếu giá tiếp tục giảm
        else:  # WAIT
            # Không trade, đặt level thấp để chờ
            tp1 = entry_price + (atr_value * 1.0)
            tp2 = entry_price + (atr_value * 2.0)
            stop_loss = entry_price - (atr_value * 0.5)
        
        return tp1, tp2, stop_loss
    
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
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}🏆 TOP RECOMMENDATION{Style.RESET_ALL}")
            print("-" * 60)
            print(f"{Fore.WHITE}Symbol: {Fore.CYAN}{best['symbol']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Current Price: {Fore.YELLOW}{best['current_price']:.6f}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Entry Price: {Fore.YELLOW}{best['entry_price']:.6f}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Signal: {Fore.GREEN if best['signal_type'] == 'BUY' else Fore.RED}{best['signal_type']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Probability: {Fore.YELLOW}{best['success_probability']:.1%}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Quality: {Fore.GREEN if best['entry_quality'] == 'HIGH' else Fore.YELLOW if best['entry_quality'] == 'MEDIUM' else Fore.RED}{best['entry_quality']}{Style.RESET_ALL}")
            
            # Volume analysis summary
            vol_summary = []
            for tf, vol_data in best['volume_analysis'].items():
                if vol_data['trend'] in ['HIGH', 'ELEVATED']:
                    vol_summary.append(f"{tf}:{vol_data['trend']}")
            if vol_summary:
                print(f"{Fore.WHITE}Volume: {Fore.MAGENTA}{', '.join(vol_summary)}{Style.RESET_ALL}")
            
            # Entry vs Current và Trading Instructions
            if best['signal_type'] == 'BUY':
                entry_diff = ((best['entry_price']/best['current_price']-1)*100)
                tp1_pct = ((best['tp1']/best['entry_price']-1)*100)
                tp2_pct = ((best['tp2']/best['entry_price']-1)*100)
                sl_pct = ((1-best['stop_loss']/best['entry_price'])*100)
                
                print(f"{Fore.WHITE}Entry vs Current: {Fore.CYAN}{entry_diff:+.2f}%{Style.RESET_ALL}")
                print(f"{Fore.GREEN}🔸 Entry: MUA SPOT tại {best['entry_price']:.6f}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}🎯 TP1: BÁN 50% tại {best['tp1']:.6f} (+{tp1_pct:.2f}% lãi){Style.RESET_ALL}")
                print(f"{Fore.GREEN}🎯 TP2: BÁN 50% còn lại tại {best['tp2']:.6f} (+{tp2_pct:.2f}% lãi){Style.RESET_ALL}")
                print(f"{Fore.RED}🛑 SL: BÁN TẤT CẢ tại {best['stop_loss']:.6f} (-{sl_pct:.2f}% lỗ){Style.RESET_ALL}")
                
            else:  # WAIT
                entry_diff = ((best['entry_price']/best['current_price']-1)*100)
                
                print(f"{Fore.WHITE}Entry vs Current: {Fore.CYAN}{entry_diff:+.2f}%{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}⏳ Tín hiệu: CHỜ THỜI ĐIỂM TỐT HƠN{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}💡 Chờ mua tại: {best['entry_price']:.6f} (giảm {abs(entry_diff):.2f}%){Style.RESET_ALL}")
                print(f"{Fore.YELLOW}📊 Hoặc chờ tín hiệu tốt hơn trong 30-45 phút{Style.RESET_ALL}")
            
            # Active signals
            active_signals = [k for k, v in best['signals'].items() if v]
            if active_signals:
                print(f"{Fore.WHITE}Active Signals: {Fore.MAGENTA}{', '.join(active_signals[:3])}{Style.RESET_ALL}")
            
            # Recommendation cho SPOT TRADING
            if best['signal_type'] == 'BUY':
                if best['success_probability'] > 0.75:
                    print(f"{Fore.GREEN}✅ TÍN HIỆU MUA MẠNH - Khuyến nghị mua spot{Style.RESET_ALL}")
                elif best['success_probability'] > 0.6:
                    print(f"{Fore.YELLOW}⚠️  TÍN HIỆU MUA VỪA - Cân nhắc mua với volume nhỏ{Style.RESET_ALL}")
                elif best['success_probability'] > 0.3:
                    print(f"{Fore.YELLOW}🤔 TÍN HIỆU MUA YẾU - Chờ xác nhận thêm{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}❌ TÍN HIỆU MUA RẤT YẾU - Không nên mua{Style.RESET_ALL}")
            else:  # WAIT
                print(f"{Fore.YELLOW}⏳ CHƯA CÓ CỚ HỘI TỐT - Chờ thị trường tích cực hơn{Style.RESET_ALL}")
                print(f"{Fore.BLUE}💡 Tip: Theo dõi trong 30-45 phút để tìm tín hiệu mua tốt{Style.RESET_ALL}")
        
        print(f"\n{Fore.BLUE}⏰ Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}💡 Next update recommended in 30-45 minutes for optimal accuracy{Style.RESET_ALL}")
        
        return results
        
        # Display results
        # print(f"\n{Fore.CYAN}{Style.BRIGHT}📊 ANALYSIS RESULTS{Style.RESET_ALL}")
        # print("=" * 140)
        # print(self.create_results_table(results))
        
        # Best recommendation
        if results:
            best = results[0]
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}🏆 TOP RECOMMENDATION{Style.RESET_ALL}")
            print("-" * 60)
            print(f"{Fore.WHITE}Symbol: {Fore.CYAN}{best['symbol']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Current Price: {Fore.YELLOW}{best['current_price']:.6f}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Entry Price: {Fore.YELLOW}{best['entry_price']:.6f}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Signal: {Fore.GREEN if best['signal_type'] == 'BUY' else Fore.RED}{best['signal_type']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Probability: {Fore.YELLOW}{best['success_probability']:.1%}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Quality: {Fore.GREEN if best['entry_quality'] == 'HIGH' else Fore.YELLOW if best['entry_quality'] == 'MEDIUM' else Fore.RED}{best['entry_quality']}{Style.RESET_ALL}")
            #print(f"{Fore.WHITE}R/R Ratio: {Fore.CYAN}{best['rr_ratio']:.2f}{Style.RESET_ALL}")
            
            # Entry vs Current và Trading Instructions
            if best['signal_type'] == 'BUY':
                entry_diff = ((best['entry_price']/best['current_price']-1)*100)
                tp1_pct = ((best['tp1']/best['entry_price']-1)*100)
                tp2_pct = ((best['tp2']/best['entry_price']-1)*100)
                sl_pct = ((1-best['stop_loss']/best['entry_price'])*100)
                
                print(f"{Fore.WHITE}Entry vs Current: {Fore.CYAN}{entry_diff:+.2f}%{Style.RESET_ALL}")
                print(f"{Fore.GREEN}🔸 Entry: MUA SPOT tại {best['entry_price']:.6f}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}🎯 TP1: BÁN 50% tại {best['tp1']:.6f} (+{tp1_pct:.2f}% lãi){Style.RESET_ALL}")
                print(f"{Fore.GREEN}🎯 TP2: BÁN 50% còn lại tại {best['tp2']:.6f} (+{tp2_pct:.2f}% lãi){Style.RESET_ALL}")
                print(f"{Fore.RED}🛑 SL: BÁN TẤT CẢ tại {best['stop_loss']:.6f} (-{sl_pct:.2f}% lỗ){Style.RESET_ALL}")
                
            else:  # WAIT
                entry_diff = ((best['entry_price']/best['current_price']-1)*100)
                
                print(f"{Fore.WHITE}Entry vs Current: {Fore.CYAN}{entry_diff:+.2f}%{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}⏳ Tín hiệu: CHỜ THỜI ĐIỂM TỐT HỚN{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}💡 Chờ mua tại: {best['entry_price']:.6f} (giảm {abs(entry_diff):.2f}%){Style.RESET_ALL}")
                print(f"{Fore.YELLOW}📊 Hoặc chờ tín hiệu tốt hơn trong 30-45 phút{Style.RESET_ALL}")
            
            # Active signals
            active_signals = [k for k, v in best['signals'].items() if v]
            if active_signals:
                print(f"{Fore.WHITE}Active Signals: {Fore.MAGENTA}{', '.join(active_signals[:3])}{Style.RESET_ALL}")
            
            # Recommendation cho SPOT TRADING
            if best['signal_type'] == 'BUY':
                if best['success_probability'] > 0.75:
                    print(f"{Fore.GREEN}✅ TÍN HIỆU MUA MẠNH - Khuyến nghị mua spot{Style.RESET_ALL}")
                elif best['success_probability'] > 0.6:
                    print(f"{Fore.YELLOW}⚠️  TÍN HIỆU MUA VỪA - Cân nhắc mua với volume nhỏ{Style.RESET_ALL}")
                elif best['success_probability'] > 0.3:
                    print(f"{Fore.YELLOW}🤔 TÍN HIỆU MUA YẾU - Chờ xác nhận thêm{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}❌ TÍN HIỆU MUA RẤT YẾU - Không nên mua{Style.RESET_ALL}")
            else:  # WAIT
                print(f"{Fore.YELLOW}⏳ CHƯA CÓ CỚ HỘI TỐT - Chờ thị trường tích cực hơn{Style.RESET_ALL}")
                print(f"{Fore.BLUE}💡 Tip: Theo dõi trong 30-45 phút để tìm tín hiệu mua tốt{Style.RESET_ALL}")
        
        print(f"\n{Fore.BLUE}⏰ Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}💡 Next update recommended in 30-45 minutes for optimal accuracy{Style.RESET_ALL}")
        
        return results

def main():
    try:
        app = EnhancedCryptoPredictionAppV2()
        results = app.run_enhanced_analysis()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Analysis interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Critical error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
