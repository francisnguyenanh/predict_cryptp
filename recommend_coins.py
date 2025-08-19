#!/usr/bin/env python3
"""
Script đề xuất 2 coin tốt nhất cho mỗi khung thời                print(f"📊 Điểm mua: {result['buy_score']:.1f}")
                print(f"📈 Xu hướng: {result['trend_strength']}")
                print(f"🔍 Chất lượng entry: {result['entry_quality']}")n dự đoán
"""

from enhanced_app_v2 import EnhancedCryptoPredictionAppV2
from colorama import Fore, Style
import sys

def recommend_coins_by_timeframe():
    """Đề xuất 2 coin tốt nhất cho mỗi khung thời gian"""
    
    print(f"{Fore.CYAN}🎯 ĐỀNH XUẤT COIN THEO KHUNG THỜI GIAN{Style.RESET_ALL}")
    print("=" * 60)
    
    # Tạo app instance
    app = EnhancedCryptoPredictionAppV2()
    
    # Lấy top coins để phân tích
    print(f"{Fore.YELLOW}🔍 Đang lấy danh sách top coins...{Style.RESET_ALL}")
    top_coins = app.get_top_coins_by_base_currency('USDT', 30)
    
    # Dictionary để lưu kết quả theo khung thời gian
    timeframe_results = {
        '60m': [],
        '4h': [], 
        '1d': []
    }
    
    # Phân tích từng coin cho mỗi khung thời gian
    for coin_data in top_coins:
        symbol = coin_data['symbol']
        print(f"📊 Analyzing {symbol}...")
        
        try:
            # Phân tích cho mỗi khung thời gian
            for timeframe in ['60m', '4h', '1d']:
                result = app.analyze_single_pair_by_investment_type(symbol, timeframe)
                
                # CHỈ LẤY NHỮNG COIN CÓ TÍN HIỆU BUY CHO SPOT TRADING
                if result['signal_type'] == 'BUY':
                    # Tính điểm tổng hợp cho BUY signal
                    composite_score = (
                        result['success_probability'] * 0.4 +  # 40% weight
                        (result['buy_score'] / 20) * 0.3 +     # 30% weight (normalize to 0-1)
                        (result['rr_ratio'] / 5) * 0.2 +       # 20% weight (normalize to 0-1)
                        (0.1 if result['entry_quality'] == 'HIGH' else 0.05 if result['entry_quality'] == 'MEDIUM' else 0) * 0.1  # 10% weight
                    )
                    
                    result['composite_score'] = composite_score
                    timeframe_results[timeframe].append(result)
                    
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            continue
    
    # Hiển thị đề xuất cho mỗi khung thời gian
    for timeframe in ['60m', '4h', '1d']:
        results = timeframe_results[timeframe]
        
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}⏰ KHUNG THỜI GIAN: {timeframe.upper()}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Thời gian nắm giữ: {app.investment_types[timeframe]['hold_duration']}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        
        if len(results) >= 2:
            # Sort by composite score
            results.sort(key=lambda x: x['composite_score'], reverse=True)
            
            # Lấy top 2
            top_2 = results[:2]
            
            for i, result in enumerate(top_2, 1):
                print(f"\n{Fore.CYAN}🏆 #{i}. {result['symbol']}{Style.RESET_ALL}")
                print(f"📈 Giá hiện tại: ${result['current_price']:.6f}")
                print(f"🎯 Tín hiệu: {result['signal_type']}")
                print(f"⭐ Điểm tổng hợp: {result['composite_score']:.3f}")
                print(f"✅ Xác suất thành công: {result['success_probability']*100:.1f}%")
                print(f"📊 Điểm mua: {result['buy_score']:.1f}")
                print(f"� Điểm bán: {result['sell_score']:.1f}")
                print(f"�📈 Xu hướng: {result['trend_strength']}")
                print(f"🔍 Chất lượng entry: {result['entry_quality']}")
                
                # TP/SL Details CHỈ CHO BUY (SPOT TRADING)
                tp1_pct = ((result['tp1']/result['entry_price'])-1)*100
                tp2_pct = ((result['tp2']/result['entry_price'])-1)*100
                sl_pct = ((result['stop_loss']/result['entry_price'])-1)*100
                
                print(f"\n{Fore.YELLOW}💰 SPOT BUY - MỨC GIÁ MỤC TIÊU:{Style.RESET_ALL}")
                print(f"   Entry:     ${result['entry_price']:.6f}")
                print(f"   TP1:       ${result['tp1']:.6f} ({Fore.GREEN}+{tp1_pct:.2f}%{Style.RESET_ALL})")
                print(f"   TP2:       ${result['tp2']:.6f} ({Fore.GREEN}+{tp2_pct:.2f}%{Style.RESET_ALL})")
                print(f"   Stop Loss: ${result['stop_loss']:.6f} ({Fore.RED}{sl_pct:.2f}%{Style.RESET_ALL})")
                
                print(f"   R:R Ratio: {Fore.CYAN}{result['rr_ratio']:.2f}{Style.RESET_ALL}")
                
                print(f"\n{Fore.MAGENTA}🔬 CHỈ SỐ KỸ THUẬT:{Style.RESET_ALL}")
                print(f"   RSI: {result['rsi']:.1f}")
                print(f"   ATR: {result['atr']:.6f}")
                
                # Hiển thị các tín hiệu quan trọng CHỈ CHO BUY (SPOT TRADING)
                important_signals = []
                signals = result.get('signals', {})
                
                # CHỈ HIỂN THỊ TÍN HIỆU BUY CHO SPOT TRADING
                signal_names = {
                    'ichimoku_bullish_cross': 'Ichimoku Bullish Cross',
                    'perfect_bullish_alignment': 'Perfect Bullish Alignment', 
                    'RSI_oversold_recovery': 'RSI Oversold Recovery',
                    'MACD_strong_bullish': 'MACD Strong Bullish',
                    'support_bounce': 'Support Bounce',
                    'bullish_candlestick': 'Bullish Candlestick',
                    'strong_bullish_consensus': 'Strong Bullish Consensus'
                }
                
                for signal_key, signal_name in signal_names.items():
                    if signals.get(signal_key, False):
                        important_signals.append(signal_name)
                
                if important_signals:
                    print(f"\n{Fore.BLUE}🚀 TÍN HIỆU QUAN TRỌNG:{Style.RESET_ALL}")
                    for signal in important_signals[:3]:  # Hiển thị top 3
                        print(f"   • {signal}")
                
                # Prediction accuracy nếu có
                pred_results = result['prediction_results']
                if pred_results['total'] > 0:
                    print(f"\n{Fore.CYAN}📊 LỊCH SỬ DỰ ĐOÁN:{Style.RESET_ALL}")
                    print(f"   Tổng: {pred_results['total']}")
                    print(f"   Độ chính xác TB: {pred_results['average_accuracy']:.1f}%")
        
        elif len(results) == 1:
            result = results[0]
            print(f"\n{Fore.YELLOW}⚠️  Chỉ tìm thấy 1 coin phù hợp:{Style.RESET_ALL}")
            print(f"🏆 {result['symbol']} - {result['signal_type']} - Xác suất: {result['success_probability']*100:.1f}%")
            
        else:
            print(f"\n{Fore.RED}❌ Không tìm thấy coin nào có tín hiệu BUY/SELL phù hợp cho khung {timeframe}{Style.RESET_ALL}")
            print(f"   Thị trường có thể đang trong giai đoạn sideways")
            print(f"   Khuyến nghị: Chờ đợi tín hiệu tốt hơn")
    
    # Tóm tắt chung
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}📋 TÓM TẮT ĐNTH XUẤT{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    total_recommendations = sum(min(len(results), 2) for results in timeframe_results.values())
    print(f"🎯 Tổng số coin được đề xuất: {total_recommendations}")
    
    for timeframe, results in timeframe_results.items():
        count = min(len(results), 2)
        if count > 0:
            top_symbols = [r['symbol'] for r in sorted(results, key=lambda x: x['composite_score'], reverse=True)[:count]]
            print(f"⏰ {timeframe}: {', '.join(top_symbols)}")
    
    print(f"\n{Fore.GREEN}✅ Phân tích hoàn tất!{Style.RESET_ALL}")
    print(f"\n{Fore.BLUE}💡 LƯU Ý:{Style.RESET_ALL}")
    print(f"   • Đây chỉ là đề xuất dựa trên phân tích kỹ thuật")
    print(f"   • Luôn thực hiện quản lý rủi ro và đặt stop loss")
    print(f"   • Theo dõi thị trường và điều chỉnh chiến lược khi cần")
    print(f"   • Không đầu tư quá 2-5% tổng tài khoản cho mỗi lệnh")

if __name__ == "__main__":
    recommend_coins_by_timeframe()
