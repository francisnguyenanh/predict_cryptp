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
    
    def __init__(self, data_file="prediction_history.json"):
        self.data_file = data_file
        self.predictions = self.load_predictions()
    
    def load_predictions(self):
        """Load lịch sử dự đoán"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"❌ Error loading predictions: {e}")
            return {}
    
    def save_predictions(self):
        """Lưu lịch sử dự đoán"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.predictions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving predictions: {e}")
    
    def add_prediction(self, symbol, prediction_data):
        """Thêm dự đoán mới"""
        if symbol not in self.predictions:
            self.predictions[symbol] = []
        
        prediction_data['timestamp'] = datetime.now().isoformat()
        prediction_data['status'] = 'PENDING'  # PENDING, HIT_TP1, HIT_TP2, HIT_SL, EXPIRED
        
        self.predictions[symbol].append(prediction_data)
        
        # Giữ chỉ 50 predictions gần nhất cho mỗi symbol
        if len(self.predictions[symbol]) > 50:
            self.predictions[symbol] = self.predictions[symbol][-50:]
        
        self.save_predictions()
    
    def check_predictions(self, symbol, current_price):
        """Kiểm tra kết quả các dự đoán chưa hoàn thành"""
        if symbol not in self.predictions:
            return {'total': 0, 'hit_tp1': 0, 'hit_tp2': 0, 'hit_sl': 0, 'pending': 0}
        
        results = {'total': 0, 'hit_tp1': 0, 'hit_tp2': 0, 'hit_sl': 0, 'pending': 0}
        
        for prediction in self.predictions[symbol]:
            if prediction['status'] == 'PENDING':
                # Kiểm tra thời gian hết hạn (24h)
                pred_time = datetime.fromisoformat(prediction['timestamp'])
                if datetime.now() - pred_time > timedelta(hours=24):
                    prediction['status'] = 'EXPIRED'
                    continue
                
                # Kiểm tra TP/SL
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
                else:  # SELL
                    if current_price <= tp2:
                        prediction['status'] = 'HIT_TP2'
                        prediction['actual_exit_price'] = current_price
                    elif current_price <= tp1:
                        prediction['status'] = 'HIT_TP1'
                        prediction['actual_exit_price'] = current_price
                    elif current_price >= stop_loss:
                        prediction['status'] = 'HIT_SL'
                        prediction['actual_exit_price'] = current_price
        
        # Tính toán thống kê
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
        
        self.save_predictions()
        return results

class EnhancedCryptoPredictionAppV2:
    def __init__(self):
        self.pairs = ['XRPJPY', 'XLMJPY', 'ADAJPY', 'SUIJPY']
        self.base_url = "https://api.binance.com/api/v3/klines"
        self.tracker = PredictionTracker()
        
    def print_header(self):
        """In header đẹp"""
        header = f"""
{Fore.CYAN}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🚀 CRYPTO SPOT TRADING ANALYZER V2.0                     ║
║                     Find Best BUY Opportunities Only                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.YELLOW}📊 Analyzing: {', '.join(self.pairs)} - SPOT TRADING ONLY{Style.RESET_ALL}
{Fore.GREEN}⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}
{Fore.BLUE}🎯 Strategy: Buy Low → Hold → Sell High{Style.RESET_ALL}
"""
        print(header)
    
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
            df['SMA_200'] = talib.SMA(df['close'], timeperiod=min(len(df), 200))
            
            # Momentum Indicators
            df['RSI'] = talib.RSI(df['close'], timeperiod=14)
            df['RSI_fast'] = talib.RSI(df['close'], timeperiod=7)
            df['MACD'], df['MACD_signal'], df['MACD_hist'] = talib.MACD(df['close'])
            df['STOCH_K'], df['STOCH_D'] = talib.STOCH(df['high'], df['low'], df['close'])
            
            # Volatility Indicators
            df['BB_upper'], df['BB_middle'], df['BB_lower'] = talib.BBANDS(df['close'])
            df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            df['Keltner_upper'] = df['EMA_20'] + (2 * df['ATR'])
            df['Keltner_lower'] = df['EMA_20'] - (2 * df['ATR'])
            
            # Volume Indicators
            df['OBV'] = talib.OBV(df['close'], df['volume'])
            df['AD_line'] = talib.AD(df['high'], df['low'], df['close'], df['volume'])
            df['volume_sma'] = talib.SMA(df['volume'], timeperiod=20)
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # Support/Resistance và Pivot Points
            df['resistance'] = df['high'].rolling(window=20).max()
            df['support'] = df['low'].rolling(window=20).min()
            
            # Price Action Patterns
            df['hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
            df['engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
            df['doji'] = talib.CDLDOJI(df['open'], df['high'], df['low'], df['close'])
            
            return df
            
        except Exception as e:
            print(f"{Fore.RED}❌ Indicator calculation error: {e}{Style.RESET_ALL}")
            return None
    
    def calculate_entry_price(self, current_price, signal_type, trend_strength, atr_value, df):
        """Tính toán giá entry cho SPOT TRADING (chỉ mua)"""
        latest = df.iloc[-1]
        
        if signal_type == 'BUY':
            if trend_strength == "STRONG_UP":
                # Uptrend mạnh: có thể mua ngay hoặc chờ pullback nhẹ
                entry_price = current_price * 0.998  # Mua thấp hơn 0.2%
            elif trend_strength in ["STRONG_DOWN", "WAIT_FOR_UPTREND"]:
                # Downtrend: chờ support mạnh hoặc reversal signal
                support_level = latest['support']
                pullback_level = current_price * 0.95  # Chờ giảm 5%
                entry_price = max(support_level, pullback_level)
            else:
                # Mixed trend: chờ pullback về support
                pullback_level = current_price - (atr_value * 0.5)
                support_level = latest['support']
                entry_price = max(pullback_level, support_level)
                entry_price = min(entry_price, current_price * 0.995)
        
        else:  # WAIT signal
            # Không mua, đặt entry price thấp để chờ cơ hội tốt hơn
            entry_price = current_price * 0.95  # Chờ giảm 5%
        
        return entry_price
    
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
    
    def analyze_trend_strength(self, trends):
        """Phân tích sức mạnh xu hướng"""
        if not trends:
            return 0, "UNKNOWN"
        
        uptrend_count = sum(1 for trend in trends.values() if trend == 'UPTREND')
        downtrend_count = sum(1 for trend in trends.values() if trend == 'DOWNTREND')
        
        if uptrend_count >= 2:
            return uptrend_count * 0.1, "STRONG_UP"
        elif downtrend_count >= 2:
            return downtrend_count * 0.1, "STRONG_DOWN"
        else:
            return 0, "MIXED"
    
    def predict_enhanced_probability(self, buy_score, sell_score, trends, rsi_value, volume_ratio):
        """Dự đoán xác suất thành công cho SPOT TRADING (chỉ BUY)"""
        # SPOT TRADING: Chỉ quan tâm đến tín hiệu mua để bán cao hơn
        # Không trade short nên chỉ tìm cơ hội mua thấp bán cao
        
        signal_type = 'BUY'  # Chỉ spot buy
        max_score = buy_score
        
        # Nếu sell_score cao hơn buy_score, nghĩa là thị trường đang bearish
        # → Không mua, chờ cơ hội tốt hơn
        if sell_score > buy_score:
            # Thị trường bearish, không khuyến nghị mua
            max_score = 0
            signal_type = 'WAIT'  # Chờ thời điểm tốt hơn
        
        # Base probability cho BUY signal (tối đa 70%)
        if signal_type == 'BUY':
            base_prob = min(max_score / 15.0, 0.7)
        else:
            base_prob = 0  # Không mua khi thị trường bearish
        
        # Trend bonus - chỉ bonus khi uptrend
        trend_bonus, trend_strength = self.analyze_trend_strength(trends)
        if trend_strength == "STRONG_DOWN":
            trend_bonus = -0.2  # Penalty cho downtrend mạnh
            trend_strength = "WAIT_FOR_UPTREND"
        
        # RSI bonus - ưu tiên mua khi oversold
        rsi_bonus = 0
        if signal_type == 'BUY':
            if rsi_value < 30:  # Oversold - cơ hội tốt
                rsi_bonus = 0.15
            elif 30 <= rsi_value <= 45:  # Decent entry
                rsi_bonus = 0.1
            elif rsi_value > 70:  # Overbought - không nên mua
                rsi_bonus = -0.15
        
        # Volume bonus
        volume_bonus = 0
        if volume_ratio > 1.5:
            volume_bonus = 0.05
        elif volume_ratio > 2.0:
            volume_bonus = 0.1
        
        # Score difference bonus - chỉ khi BUY score thống trị
        score_diff = buy_score - sell_score
        if score_diff > 5:
            score_bonus = 0.1
        elif score_diff < -2:  # Sell signal mạnh hơn
            score_bonus = -0.15
        else:
            score_bonus = 0
        
        final_prob = max(0, min(base_prob + trend_bonus + rsi_bonus + volume_bonus + score_bonus, 0.95))
        
        return final_prob, signal_type, trend_strength
    
    def analyze_single_pair_enhanced(self, symbol):
        """Phân tích nâng cao một cặp coin"""
        print(f"{Fore.BLUE}📊 Analyzing {symbol}...{Style.RESET_ALL}")
        
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
        
        # Phân tích xu hướng đa khung thời gian
        trends = {}
        timeframes = ['15m', '1h', '4h']
        for tf in timeframes:
            df = self.get_kline_data(symbol, tf, 100)
            if df is not None:
                df = self.calculate_advanced_indicators(df)
                if df is not None and len(df) > 0:
                    latest = df.iloc[-1]
                    if not pd.isna(latest['EMA_10']) and not pd.isna(latest['EMA_20']):
                        if latest['EMA_10'] > latest['EMA_20'] and latest['close'] > latest['EMA_10']:
                            trends[tf] = 'UPTREND'
                        elif latest['EMA_10'] < latest['EMA_20'] and latest['close'] < latest['EMA_10']:
                            trends[tf] = 'DOWNTREND'
                        else:
                            trends[tf] = 'SIDEWAYS'
            time.sleep(0.5)  # Rate limit
        
        # Tính điểm tín hiệu nâng cao
        buy_score, sell_score, signals = self.calculate_enhanced_signal_score(df_15m)
        
        latest = df_15m.iloc[-1]
        
        # Dự đoán xác suất thành công
        success_prob, signal_type, trend_strength = self.predict_enhanced_probability(
            buy_score, sell_score, trends, latest['RSI'], latest['volume_ratio']
        )
        
        # Tính entry price phù hợp
        entry_price = self.calculate_entry_price(
            current_price, signal_type, trend_strength, latest['ATR'], df_15m
        )
        
        # Tính TP/SL với logic đúng
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
            'volume_ratio': latest['volume_ratio'],
            'atr': latest['ATR'],
            'signals': signals,
            'entry_quality': 'HIGH' if success_prob > 0.75 else 'MEDIUM' if success_prob > 0.6 else 'LOW',
            'prediction_results': prediction_results
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
    
    def create_results_table(self, results):
        """Tạo bảng kết quả đẹp"""
        if not results:
            return "No results available"
        
        table_data = []
        for i, result in enumerate(results, 1):
            # Tính % change cho TP và SL dựa trên Entry Price
            entry_price = result['entry_price']
            
            if result['signal_type'] == 'BUY':
                tp1_pct = ((result['tp1']/entry_price-1)*100)
                tp2_pct = ((result['tp2']/entry_price-1)*100)
                sl_pct = -((1-result['stop_loss']/entry_price)*100)
                entry_vs_current = ((entry_price/result['current_price']-1)*100)
            else:  # WAIT
                tp1_pct = ((result['tp1']/entry_price-1)*100) if entry_price > 0 else 0
                tp2_pct = ((result['tp2']/entry_price-1)*100) if entry_price > 0 else 0
                sl_pct = -((1-result['stop_loss']/entry_price)*100) if entry_price > 0 else 0
                entry_vs_current = ((entry_price/result['current_price']-1)*100)
            
            # Màu sắc cho signal
            signal_color = Fore.GREEN if result['signal_type'] == 'BUY' else Fore.YELLOW
            
            # Trend summary
            trends_summary = f"{len([t for t in result['trends'].values() if t == 'UPTREND'])}↑ {len([t for t in result['trends'].values() if t == 'DOWNTREND'])}↓"
            
            # Prediction accuracy
            pred_results = result['prediction_results']
            if pred_results['total'] > 0:
                success_rate = ((pred_results['hit_tp1'] + pred_results['hit_tp2']) / pred_results['total']) * 100
                accuracy = f"{success_rate:.0f}%"
            else:
                accuracy = "NEW"
            
            table_data.append([
                f"#{i}",
                result['symbol'],
                f"{result['current_price']:.6f}",
                f"{entry_price:.6f}",
                f"{entry_vs_current:+.2f}%",
                f"{signal_color}{result['signal_type']}{Style.RESET_ALL}",
                f"{result['success_probability']:.1%}",
                result['entry_quality'],
                f"{result['rsi']:.1f}",
                trends_summary,
                f"{tp1_pct:+.2f}%",
                f"{sl_pct:+.2f}%",
                f"{result['rr_ratio']:.2f}",
                accuracy
            ])
        
        headers = [
            "Rank", "Symbol", "Current", "Entry", "Entry%", "Signal", "Probability", 
            "Quality", "RSI", "Trends", "TP1%", "SL%", "R/R", "Accuracy"
        ]
        
        return tabulate(table_data, headers=headers, tablefmt="grid")
    
    def display_prediction_history(self, results):
        """Hiển thị lịch sử dự đoán"""
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}📈 PREDICTION ACCURACY SUMMARY{Style.RESET_ALL}")
        print("=" * 80)
        
        for result in results:
            pred_results = result['prediction_results']
            if pred_results['total'] > 0:
                total = pred_results['total']
                success = pred_results['hit_tp1'] + pred_results['hit_tp2']
                success_rate = (success / total) * 100
                
                print(f"{Fore.CYAN}{result['symbol']}{Style.RESET_ALL}: "
                      f"Total: {total}, Success: {success}, "
                      f"Rate: {Fore.GREEN if success_rate > 60 else Fore.YELLOW if success_rate > 40 else Fore.RED}{success_rate:.1f}%{Style.RESET_ALL}")
    
    def run_enhanced_analysis(self):
        """Chạy phân tích nâng cao"""
        self.print_header()
        
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
        
        # Display results
        print(f"\n{Fore.CYAN}{Style.BRIGHT}📊 ANALYSIS RESULTS{Style.RESET_ALL}")
        print("=" * 140)
        print(self.create_results_table(results))
        
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
            print(f"{Fore.WHITE}R/R Ratio: {Fore.CYAN}{best['rr_ratio']:.2f}{Style.RESET_ALL}")
            
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
                print(f"{Fore.YELLOW}� Hoặc chờ tín hiệu tốt hơn trong 15-30 phút{Style.RESET_ALL}")
            
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
                print(f"{Fore.BLUE}💡 Tip: Theo dõi trong 15-30 phút để tìm tín hiệu mua tốt{Style.RESET_ALL}")
        
        print(f"\n{Fore.BLUE}⏰ Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}💡 Next update recommended in 15-30 minutes{Style.RESET_ALL}")
        
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
