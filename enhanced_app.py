#!/usr/bin/env python3
"""
Enhanced Crypto Analysis với Dashboard đẹp
"""

import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
import talib
import warnings
import os
from tabulate import tabulate
import colorama
from colorama import Fore, Back, Style

warnings.filterwarnings('ignore')
colorama.init()

class EnhancedCryptoPredictionApp:
    def __init__(self):
        self.pairs = ['XRPJPY', 'XLMJPY', 'ADAJPY', 'SUIJPY']
        self.base_url = "https://api.binance.com/api/v3/klines"
        
    def print_header(self):
        """In header đẹp"""
        header = f"""
{Fore.CYAN}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════════════════╗
║                          🚀 CRYPTO PREDICTION DASHBOARD                     ║
║                             Advanced Technical Analysis                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}

{Fore.YELLOW}📊 Analyzing: {', '.join(self.pairs)}{Style.RESET_ALL}
{Fore.GREEN}⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}
{Fore.BLUE}🎯 Timeframes: 15m, 1h, 4h{Style.RESET_ALL}
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
        
        # Stochastic
        if not pd.isna(latest['STOCH_K']) and not pd.isna(latest['STOCH_D']):
            if latest['STOCH_K'] < 20 and latest['STOCH_K'] > latest['STOCH_D']:
                buy_score += 1.5
                signals['STOCH_oversold_cross'] = True
            elif latest['STOCH_K'] > 80 and latest['STOCH_K'] < latest['STOCH_D']:
                sell_score += 1.5
                signals['STOCH_overbought_cross'] = True
        
        # 3. Volatility Signals
        # Bollinger Bands
        if not pd.isna(latest['BB_lower']):
            bb_position = (latest['close'] - latest['BB_lower']) / (latest['BB_upper'] - latest['BB_lower'])
            if bb_position < 0.1 and latest['close'] > prev['close']:
                buy_score += 2
                signals['BB_oversold_bounce'] = True
            elif bb_position > 0.9 and latest['close'] < prev['close']:
                sell_score += 2
                signals['BB_overbought_rejection'] = True
        
        # Keltner Channel Breakout
        if not pd.isna(latest['Keltner_upper']):
            if latest['close'] > latest['Keltner_upper'] and prev['close'] <= prev['Keltner_upper']:
                buy_score += 1.5
                signals['Keltner_bullish_breakout'] = True
            elif latest['close'] < latest['Keltner_lower'] and prev['close'] >= prev['Keltner_lower']:
                sell_score += 1.5
                signals['Keltner_bearish_breakdown'] = True
        
        # 4. Volume Analysis
        if latest['volume_ratio'] > 1.5:  # High volume
            if latest['close'] > prev['close']:
                buy_score += 1.5
                signals['volume_bullish_confirmation'] = True
            elif latest['close'] < prev['close']:
                sell_score += 1.5
                signals['volume_bearish_confirmation'] = True
        
        # OBV Trend
        if not pd.isna(latest['OBV']) and not pd.isna(prev2['OBV']):
            if latest['OBV'] > prev2['OBV'] and latest['close'] > prev2['close']:
                buy_score += 1
                signals['OBV_bullish_trend'] = True
            elif latest['OBV'] < prev2['OBV'] and latest['close'] < prev2['close']:
                sell_score += 1
                signals['OBV_bearish_trend'] = True
        
        # 5. Price Action Patterns
        if latest['hammer'] > 0:
            buy_score += 1.5
            signals['hammer_pattern'] = True
        elif latest['hammer'] < 0:
            sell_score += 1.5
            signals['hanging_man_pattern'] = True
        
        if latest['engulfing'] > 0:
            buy_score += 2
            signals['bullish_engulfing'] = True
        elif latest['engulfing'] < 0:
            sell_score += 2
            signals['bearish_engulfing'] = True
        
        # 6. Support/Resistance
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
        """Dự đoán xác suất thành công nâng cao"""
        max_score = max(buy_score, sell_score)
        signal_type = 'BUY' if buy_score > sell_score else 'SELL'
        
        # Base probability (tối đa 70%)
        base_prob = min(max_score / 15.0, 0.7)
        
        # Trend bonus
        trend_bonus, trend_strength = self.analyze_trend_strength(trends)
        
        # RSI bonus
        rsi_bonus = 0
        if signal_type == 'BUY' and 25 < rsi_value < 45:
            rsi_bonus = 0.1
        elif signal_type == 'SELL' and 55 < rsi_value < 75:
            rsi_bonus = 0.1
        
        # Volume bonus
        volume_bonus = 0
        if volume_ratio > 1.5:
            volume_bonus = 0.05
        elif volume_ratio > 2.0:
            volume_bonus = 0.1
        
        # Score difference bonus
        score_diff = abs(buy_score - sell_score)
        if score_diff > 5:
            score_bonus = 0.1
        else:
            score_bonus = 0
        
        final_prob = min(base_prob + trend_bonus + rsi_bonus + volume_bonus + score_bonus, 0.95)
        
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
            time.sleep(0.5)  # Tránh rate limit
        
        # Tính điểm tín hiệu nâng cao
        buy_score, sell_score, signals = self.calculate_enhanced_signal_score(df_15m)
        
        latest = df_15m.iloc[-1]
        current_price = latest['close']
        
        # Dự đoán xác suất thành công
        success_prob, signal_type, trend_strength = self.predict_enhanced_probability(
            buy_score, sell_score, trends, latest['RSI'], latest['volume_ratio']
        )
        
        # Tính TP levels dựa trên ATR và volatility
        atr_multiplier = 1.5 if latest['volume_ratio'] > 1.5 else 1.2
        tp1_atr = latest['ATR'] * atr_multiplier
        tp2_atr = latest['ATR'] * (atr_multiplier + 1.0)
        sl_atr = latest['ATR'] * 1.0
        
        if signal_type == 'BUY':
            tp1 = current_price + tp1_atr
            tp2 = current_price + tp2_atr
            stop_loss = current_price - sl_atr
        else:
            tp1 = current_price - tp1_atr
            tp2 = current_price - tp2_atr
            stop_loss = current_price + sl_atr
        
        # Risk/Reward ratio
        if signal_type == 'BUY':
            rr_ratio = tp1_atr / sl_atr
        else:
            rr_ratio = tp1_atr / sl_atr
        
        result = {
            'symbol': symbol,
            'current_price': current_price,
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
            'entry_quality': 'HIGH' if success_prob > 0.75 else 'MEDIUM' if success_prob > 0.6 else 'LOW'
        }
        
        return result
    
    def create_results_table(self, results):
        """Tạo bảng kết quả đẹp"""
        if not results:
            return "No results available"
        
        table_data = []
        for i, result in enumerate(results, 1):
            # Tính % change cho TP và SL
            if result['signal_type'] == 'BUY':
                tp1_pct = ((result['tp1']/result['current_price']-1)*100)
                tp2_pct = ((result['tp2']/result['current_price']-1)*100)
                sl_pct = -((1-result['stop_loss']/result['current_price'])*100)
            else:
                tp1_pct = -((1-result['tp1']/result['current_price'])*100)
                tp2_pct = -((1-result['tp2']/result['current_price'])*100)
                sl_pct = ((result['stop_loss']/result['current_price']-1)*100)
            
            # Màu sắc cho signal
            signal_color = Fore.GREEN if result['signal_type'] == 'BUY' else Fore.RED
            
            # Trend summary
            trends_summary = f"{len([t for t in result['trends'].values() if t == 'UPTREND'])}↑ {len([t for t in result['trends'].values() if t == 'DOWNTREND'])}↓"
            
            table_data.append([
                f"#{i}",
                result['symbol'],
                f"{result['current_price']:.6f}",
                f"{signal_color}{result['signal_type']}{Style.RESET_ALL}",
                f"{result['success_probability']:.1%}",
                result['entry_quality'],
                f"{result['rsi']:.1f}",
                trends_summary,
                f"{tp1_pct:+.2f}%",
                f"{sl_pct:+.2f}%",
                f"{result['rr_ratio']:.2f}"
            ])
        
        headers = [
            "Rank", "Symbol", "Price", "Signal", "Probability", 
            "Quality", "RSI", "Trends", "TP1%", "SL%", "R/R"
        ]
        
        return tabulate(table_data, headers=headers, tablefmt="grid")
    
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
        
        # Display results
        print(f"\n{Fore.CYAN}{Style.BRIGHT}📊 ANALYSIS RESULTS{Style.RESET_ALL}")
        print("=" * 120)
        print(self.create_results_table(results))
        
        # Best recommendation
        if results:
            best = results[0]
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}🏆 TOP RECOMMENDATION{Style.RESET_ALL}")
            print("-" * 50)
            print(f"{Fore.WHITE}Symbol: {Fore.CYAN}{best['symbol']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Signal: {Fore.GREEN if best['signal_type'] == 'BUY' else Fore.RED}{best['signal_type']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Probability: {Fore.YELLOW}{best['success_probability']:.1%}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Quality: {Fore.GREEN if best['entry_quality'] == 'HIGH' else Fore.YELLOW if best['entry_quality'] == 'MEDIUM' else Fore.RED}{best['entry_quality']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}R/R Ratio: {Fore.CYAN}{best['rr_ratio']:.2f}{Style.RESET_ALL}")
            
            # Active signals
            active_signals = [k for k, v in best['signals'].items() if v]
            if active_signals:
                print(f"{Fore.WHITE}Active Signals: {Fore.MAGENTA}{', '.join(active_signals[:3])}{Style.RESET_ALL}")
            
            # Recommendation
            if best['success_probability'] > 0.75:
                print(f"{Fore.GREEN}✅ STRONG SIGNAL - Recommended for trading{Style.RESET_ALL}")
            elif best['success_probability'] > 0.6:
                print(f"{Fore.YELLOW}⚠️  MODERATE SIGNAL - Trade with caution{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ WEAK SIGNAL - Not recommended{Style.RESET_ALL}")
        
        print(f"\n{Fore.BLUE}⏰ Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}💡 Next update recommended in 15-30 minutes{Style.RESET_ALL}")
        
        return results

def main():
    try:
        app = EnhancedCryptoPredictionApp()
        results = app.run_enhanced_analysis()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Analysis interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Critical error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
