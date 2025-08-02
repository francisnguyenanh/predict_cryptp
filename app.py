import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
import talib
import warnings
warnings.filterwarnings('ignore')

class CryptoPredictionApp:
    def __init__(self):
        self.pairs = ['XRPJPY', 'XLMJPY', 'ADAJPY', 'SUIJPY']
        self.base_url = "https://api.binance.com/api/v3/klines"
        
    def get_kline_data(self, symbol, interval='15m', limit=200):
        """Lấy dữ liệu giá từ Binance API"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
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
            
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu cho {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(self, df):
        """Tính toán các chỉ báo kỹ thuật"""
        if df is None or len(df) < 50:
            return None
            
        try:
            # Moving Averages
            df['EMA_10'] = talib.EMA(df['close'], timeperiod=10)
            df['EMA_20'] = talib.EMA(df['close'], timeperiod=20)
            df['SMA_50'] = talib.SMA(df['close'], timeperiod=50)
            
            # RSI
            df['RSI'] = talib.RSI(df['close'], timeperiod=14)
            
            # MACD
            df['MACD'], df['MACD_signal'], df['MACD_hist'] = talib.MACD(df['close'])
            
            # Bollinger Bands
            df['BB_upper'], df['BB_middle'], df['BB_lower'] = talib.BBANDS(df['close'])
            
            # Support and Resistance levels
            df['resistance'] = df['high'].rolling(window=20).max()
            df['support'] = df['low'].rolling(window=20).min()
            
            # Volume indicators
            df['volume_sma'] = talib.SMA(df['volume'], timeperiod=20)
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            return df
            
        except Exception as e:
            print(f"Lỗi khi tính toán chỉ báo: {e}")
            return None
    
    def analyze_trend_multiple_timeframes(self, symbol):
        """Phân tích xu hướng trên nhiều khung thời gian"""
        trends = {}
        
        timeframes = ['15m', '1h', '4h']
        for tf in timeframes:
            df = self.get_kline_data(symbol, tf, 100)
            if df is not None:
                df = self.calculate_technical_indicators(df)
                if df is not None:
                    # Xác định xu hướng dựa trên EMA
                    latest = df.iloc[-1]
                    if latest['EMA_10'] > latest['EMA_20'] and latest['close'] > latest['EMA_10']:
                        trends[tf] = 'UPTREND'
                    elif latest['EMA_10'] < latest['EMA_20'] and latest['close'] < latest['EMA_10']:
                        trends[tf] = 'DOWNTREND'
                    else:
                        trends[tf] = 'SIDEWAYS'
        
        return trends
    
    def calculate_entry_signal_score(self, df):
        """Tính điểm số tín hiệu entry dựa trên các chỉ báo"""
        if df is None or len(df) < 2:
            return 0, 0, {}
            
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        buy_score = 0
        sell_score = 0
        signals = {}
        
        # 1. Moving Average Signal
        if latest['EMA_10'] > latest['EMA_20'] and prev['EMA_10'] <= prev['EMA_20']:
            buy_score += 2
            signals['MA_cross_up'] = True
        elif latest['EMA_10'] < latest['EMA_20'] and prev['EMA_10'] >= prev['EMA_20']:
            sell_score += 2
            signals['MA_cross_down'] = True
            
        # Giá trên/dưới MA
        if latest['close'] > latest['EMA_10'] > latest['EMA_20']:
            buy_score += 1
        elif latest['close'] < latest['EMA_10'] < latest['EMA_20']:
            sell_score += 1
        
        # 2. RSI Signal
        if latest['RSI'] < 30 and prev['RSI'] >= 30:  # Thoát khỏi vùng quá bán
            buy_score += 2
            signals['RSI_oversold_exit'] = True
        elif latest['RSI'] > 70 and prev['RSI'] <= 70:  # Thoát khỏi vùng quá mua
            sell_score += 2
            signals['RSI_overbought_exit'] = True
        elif 30 < latest['RSI'] < 50 and latest['RSI'] > prev['RSI']:  # RSI tăng từ vùng thấp
            buy_score += 1
        elif 50 < latest['RSI'] < 70 and latest['RSI'] < prev['RSI']:  # RSI giảm từ vùng cao
            sell_score += 1
        
        # 3. MACD Signal
        if not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_signal']):
            if latest['MACD'] > latest['MACD_signal'] and prev['MACD'] <= prev['MACD_signal']:
                buy_score += 2
                signals['MACD_cross_up'] = True
            elif latest['MACD'] < latest['MACD_signal'] and prev['MACD'] >= prev['MACD_signal']:
                sell_score += 2
                signals['MACD_cross_down'] = True
        
        # 4. Bollinger Bands Signal
        if not pd.isna(latest['BB_lower']) and not pd.isna(latest['BB_upper']):
            if latest['close'] <= latest['BB_lower'] and latest['close'] > prev['close']:
                buy_score += 1.5
                signals['BB_bounce_up'] = True
            elif latest['close'] >= latest['BB_upper'] and latest['close'] < prev['close']:
                sell_score += 1.5
                signals['BB_bounce_down'] = True
        
        # 5. Support/Resistance Signal
        price_near_support = abs(latest['close'] - latest['support']) / latest['close'] < 0.02
        price_near_resistance = abs(latest['close'] - latest['resistance']) / latest['close'] < 0.02
        
        if price_near_support and latest['close'] > prev['close']:
            buy_score += 1
            signals['support_bounce'] = True
        elif price_near_resistance and latest['close'] < prev['close']:
            sell_score += 1
            signals['resistance_rejection'] = True
        
        # 6. Volume Confirmation
        if latest['volume_ratio'] > 1.5:  # Khối lượng cao
            if buy_score > sell_score:
                buy_score += 1
                signals['volume_confirm_buy'] = True
            elif sell_score > buy_score:
                sell_score += 1
                signals['volume_confirm_sell'] = True
        
        return buy_score, sell_score, signals
    
    def calculate_tp_levels(self, current_price, signal_type, atr_value):
        """Tính toán mức Take Profit với R/R ratio tốt hơn"""
        if signal_type == 'BUY':
            # BUY: TP > Entry, SL < Entry
            tp1 = current_price + (atr_value * 1.8)  # TP xa hơn
            tp2 = current_price + (atr_value * 2.8)  
            stop_loss = current_price - (atr_value * 1.2)  # SL gần hơn
        else:  # SELL
            # SELL: TP < Entry (giá giảm để lãi), SL > Entry (giá tăng thì cắt lỗ)
            tp1 = current_price - (atr_value * 1.8)  # TP xa hơn
            tp2 = current_price - (atr_value * 2.8)   
            stop_loss = current_price + (atr_value * 1.2)  # SL gần hơn
        
        return tp1, tp2, stop_loss
    
    def predict_success_probability(self, buy_score, sell_score, trends, rsi_value):
        """Dự đoán xác suất thành công của tín hiệu"""
        max_score = max(buy_score, sell_score)
        signal_type = 'BUY' if buy_score > sell_score else 'SELL'
        
        # Base probability dựa trên điểm số
        base_prob = min(max_score / 10.0, 0.8)  # Tối đa 80%
        
        # Điều chỉnh dựa trên xu hướng đa khung thời gian
        trend_bonus = 0
        if signal_type == 'BUY':
            uptrend_count = sum(1 for trend in trends.values() if trend == 'UPTREND')
            trend_bonus = uptrend_count * 0.1
        else:
            downtrend_count = sum(1 for trend in trends.values() if trend == 'DOWNTREND')
            trend_bonus = downtrend_count * 0.1
        
        # Điều chỉnh dựa trên RSI
        rsi_bonus = 0
        if signal_type == 'BUY' and 20 < rsi_value < 40:
            rsi_bonus = 0.1
        elif signal_type == 'SELL' and 60 < rsi_value < 80:
            rsi_bonus = 0.1
        
        final_prob = min(base_prob + trend_bonus + rsi_bonus, 0.9)
        return final_prob, signal_type
    
    def analyze_single_pair(self, symbol):
        """Phân tích một cặp coin"""
        print(f"\n📊 Phân tích {symbol}...")
        
        # Lấy dữ liệu 15m
        df_15m = self.get_kline_data(symbol, '15m', 200)
        if df_15m is None:
            return None
        
        df_15m = self.calculate_technical_indicators(df_15m)
        if df_15m is None:
            return None
        
        # Phân tích xu hướng đa khung thời gian
        trends = self.analyze_trend_multiple_timeframes(symbol)
        
        # Tính ATR cho stop loss và take profit
        df_15m['ATR'] = talib.ATR(df_15m['high'], df_15m['low'], df_15m['close'], timeperiod=14)
        
        # Tính điểm tín hiệu
        buy_score, sell_score, signals = self.calculate_entry_signal_score(df_15m)
        
        latest = df_15m.iloc[-1]
        current_price = latest['close']
        
        # Dự đoán xác suất thành công
        success_prob, signal_type = self.predict_success_probability(
            buy_score, sell_score, trends, latest['RSI']
        )
        
        # Tính TP levels
        tp1, tp2, stop_loss = self.calculate_tp_levels(
            current_price, signal_type, latest['ATR']
        )
        
        result = {
            'symbol': symbol,
            'current_price': current_price,
            'signal_type': signal_type,
            'buy_score': buy_score,
            'sell_score': sell_score,
            'success_probability': success_prob,
            'trends': trends,
            'tp1': tp1,
            'tp2': tp2,
            'stop_loss': stop_loss,
            'rsi': latest['RSI'],
            'signals': signals,
            'entry_quality': 'HIGH' if success_prob > 0.7 else 'MEDIUM' if success_prob > 0.5 else 'LOW'
        }
        
        return result
    
    def run_analysis(self):
        """Chạy phân tích cho tất cả các cặp coin"""
        print("🚀 BẮT ĐẦU PHÂN TÍCH DỰ ĐOÁN CRYPTO...")
        print("=" * 60)
        
        results = []
        
        for pair in self.pairs:
            try:
                result = self.analyze_single_pair(pair)
                if result:
                    results.append(result)
                time.sleep(1)  # Tránh rate limit
            except Exception as e:
                print(f"❌ Lỗi khi phân tích {pair}: {e}")
        
        # Sắp xếp theo xác suất thành công
        results.sort(key=lambda x: x['success_probability'], reverse=True)
        
        # Hiển thị kết quả
        self.display_results(results)
        
        return results
    
    def display_results(self, results):
        """Hiển thị kết quả phân tích"""
        print("\n" + "=" * 80)
        print("📈 KẾT QUẢ PHÂN TÍCH VÀ DỰ ĐOÁN")
        print("=" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n🏆 #{i} - {result['symbol']}")
            print("-" * 50)
            print(f"💰 Giá hiện tại: {result['current_price']:.6f}")
            print(f"📊 Tín hiệu: {result['signal_type']}")
            print(f"🎯 Xác suất thành công: {result['success_probability']:.1%}")
            print(f"⭐ Chất lượng Entry: {result['entry_quality']}")
            print(f"📈 RSI: {result['rsi']:.1f}")
            
            # Hiển thị xu hướng đa khung thời gian
            trends_str = " | ".join([f"{tf}: {trend}" for tf, trend in result['trends'].items()])
            print(f"📊 Xu hướng: {trends_str}")
            
            # Hiển thị mức TP và SL với giá cụ thể - LOGIC ĐÚNG
            if result['signal_type'] == 'BUY':
                tp1_pct = ((result['tp1']/result['current_price']-1)*100)
                tp2_pct = ((result['tp2']/result['current_price']-1)*100)  
                sl_pct = ((1-result['stop_loss']/result['current_price'])*100)
                
                print(f"🎯 Take Profit 1: {result['tp1']:.6f} (+{tp1_pct:.2f}%)")
                print(f"🎯 Take Profit 2: {result['tp2']:.6f} (+{tp2_pct:.2f}%)")
                print(f"🛑 Stop Loss: {result['stop_loss']:.6f} (-{sl_pct:.2f}%)")
                print(f"📊 Entry Price: {result['current_price']:.6f} (Mua ngay)")
                
            else:  # SELL - Short position
                tp1_pct = ((result['current_price']/result['tp1']-1)*100)  # TP thấp hơn entry = lãi
                tp2_pct = ((result['current_price']/result['tp2']-1)*100)  
                sl_pct = ((result['stop_loss']/result['current_price']-1)*100)  # SL cao hơn entry = lỗ
                
                print(f"🎯 Take Profit 1: {result['tp1']:.6f} (+{tp1_pct:.2f}% lãi)")
                print(f"🎯 Take Profit 2: {result['tp2']:.6f} (+{tp2_pct:.2f}% lãi)")
                print(f"🛑 Stop Loss: {result['stop_loss']:.6f} (-{sl_pct:.2f}% lỗ)")
                print(f"📊 Entry Price: {result['current_price']:.6f} (Bán short)")
            
            # Hiển thị các tín hiệu kích hoạt
            if result['signals']:
                signals_list = [signal for signal in result['signals'].keys() if result['signals'][signal]]
                if signals_list:
                    print(f"🔔 Tín hiệu kích hoạt: {', '.join(signals_list)}")
        
        # Hiển thị khuyến nghị tốt nhất
        if results:
            best = results[0]
            print("\n" + "🌟" * 20)
            print("🏆 KHUYẾN NGHỊ GIAO DỊCH TỐT NHẤT")
            print("🌟" * 20)
            print(f"Coin: {best['symbol']}")
            print(f"💰 Giá hiện tại: {best['current_price']:.6f}")
            print(f"📊 Tín hiệu: {best['signal_type']}")
            print(f"🎯 Xác suất thành công: {best['success_probability']:.1%}")
            print(f"⭐ Chất lượng Entry: {best['entry_quality']}")
            
            # Hiển thị mức giá cụ thể cho TP và SL - LOGIC ĐÚNG
            if best['signal_type'] == 'BUY':
                tp1_pct = ((best['tp1']/best['current_price']-1)*100)
                tp2_pct = ((best['tp2']/best['current_price']-1)*100)
                sl_pct = ((1-best['stop_loss']/best['current_price'])*100)
                
                print(f"🔸 Entry: MUA tại {best['current_price']:.6f}")
                print(f"🎯 TP1: BÁN tại {best['tp1']:.6f} (+{tp1_pct:.2f}% lãi)")
                print(f"🎯 TP2: BÁN tại {best['tp2']:.6f} (+{tp2_pct:.2f}% lãi)")
                print(f"🛑 SL: BÁN tại {best['stop_loss']:.6f} (-{sl_pct:.2f}% lỗ)")
                
            else:  # SELL - Short position
                tp1_pct = ((best['current_price']/best['tp1']-1)*100)  # TP thấp hơn entry = lãi
                tp2_pct = ((best['current_price']/best['tp2']-1)*100)
                sl_pct = ((best['stop_loss']/best['current_price']-1)*100)  # SL cao hơn entry = lỗ
                
                print(f"🔸 Entry: BÁN SHORT tại {best['current_price']:.6f}")
                print(f"🎯 TP1: ĐÓNG SHORT tại {best['tp1']:.6f} (+{tp1_pct:.2f}% lãi)")
                print(f"🎯 TP2: ĐÓNG SHORT tại {best['tp2']:.6f} (+{tp2_pct:.2f}% lãi)")
                print(f"🛑 SL: ĐÓNG SHORT tại {best['stop_loss']:.6f} (-{sl_pct:.2f}% lỗ)")
            
            if best['success_probability'] > 0.7:
                print("✅ Tín hiệu mạnh - Khuyến nghị giao dịch")
            elif best['success_probability'] > 0.5:
                print("⚠️ Tín hiệu trung bình - Giao dịch thận trọng")
            else:
                print("❌ Tín hiệu yếu - Không khuyến nghị giao dịch")

def main():
    app = CryptoPredictionApp()
    results = app.run_analysis()
    
    # Có thể chạy lại sau một khoảng thời gian
    print(f"\n⏰ Phân tích hoàn thành lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💡 Khuyến nghị: Chạy lại phân tích mỗi 15-30 phút để cập nhật tín hiệu mới")

if __name__ == "__main__":
    main()