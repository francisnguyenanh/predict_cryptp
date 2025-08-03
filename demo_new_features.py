#!/usr/bin/env python3
"""
Demo script showcasing all new features
Crypto Prediction App - Multi-Timeframe Analysis
"""

from enhanced_app_v2 import EnhancedCryptoPredictionAppV2
from colorama import Fore, Style
import time

def demo_header():
    print(f"{Fore.CYAN}{Style.BRIGHT}")
    print("=" * 80)
    print("        🚀 CRYPTO PREDICTION APP - MULTI-TIMEFRAME ANALYSIS 🚀")
    print("=" * 80)
    print(f"{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✨ NEW FEATURES:{Style.RESET_ALL}")
    print(f"   • 3 kiểu đầu tư: 60m (Scalping), 4h (Swing), 1d (Position)")
    print(f"   • 3 cặp coin mới: LINKJPY, SOLJPY, ETHJPY")
    print(f"   • Tổng cộng 7 cặp: XRPJPY, XLMJPY, ADAJPY, SUIJPY, LINKJPY, SOLJPY, ETHJPY")
    print(f"   • TP/SL được điều chỉnh theo thời gian giữ lệnh")
    print(f"   • Phân tích đa khung thời gian tự động")
    print()

def demo_single_investment_types():
    """Demo từng kiểu đầu tư riêng biệt"""
    print(f"{Fore.YELLOW}{Style.BRIGHT}📊 DEMO: PHÂN TÍCH TỪNG KIỂU ĐẦU TƯ{Style.RESET_ALL}")
    print("-" * 60)
    
    app = EnhancedCryptoPredictionAppV2()
    
    investment_types = {
        '60m': '🔥 SCALPING (60 phút)',
        '4h': '📈 SWING (4 giờ)', 
        '1d': '🎯 POSITION (1 ngày)'
    }
    
    for inv_type, description in investment_types.items():
        print(f"\n{Fore.MAGENTA}{description}{Style.RESET_ALL}")
        print("=" * 40)
        
        # Phân tích SOLJPY cho mỗi kiểu
        result = app.analyze_single_pair_by_investment_type('SOLJPY', inv_type)
        
        if result:
            print(f"Coin: {Fore.CYAN}SOLJPY{Style.RESET_ALL}")
            print(f"Khung thời gian phân tích: {Fore.MAGENTA}{result['timeframe']}{Style.RESET_ALL}")
            print(f"Thời gian giữ lệnh: {Fore.YELLOW}{result['hold_duration']}{Style.RESET_ALL}")
            print(f"Tín hiệu: {Fore.GREEN if result['signal_type'] == 'BUY' else Fore.RED}{result['signal_type']}{Style.RESET_ALL}")
            print(f"Xác suất: {Fore.YELLOW}{result['success_probability']:.1%}{Style.RESET_ALL}")
            
            if result['signal_type'] == 'BUY':
                tp1_pct = ((result['tp1']/result['entry_price']-1)*100)
                tp2_pct = ((result['tp2']/result['entry_price']-1)*100)
                sl_pct = ((1-result['stop_loss']/result['entry_price'])*100)
                
                print(f"TP1: +{tp1_pct:.2f}% | TP2: +{tp2_pct:.2f}% | SL: -{sl_pct:.2f}%")
                
                # Advice based on investment type
                if inv_type == '60m':
                    print(f"{Fore.BLUE}💡 Lướt sóng nhanh, chốt lời/lỗ trong 1 giờ{Style.RESET_ALL}")
                elif inv_type == '4h':
                    print(f"{Fore.BLUE}💡 Swing trading, giữ 2-4 giờ{Style.RESET_ALL}")
                elif inv_type == '1d':
                    print(f"{Fore.BLUE}💡 Đầu tư vị thế, giữ 8-24 giờ{Style.RESET_ALL}")
        
        time.sleep(1)  # Pause để dễ theo dõi

def demo_new_pairs():
    """Demo các cặp coin mới"""
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}🆕 DEMO: CÁC CẶP COIN MỚI{Style.RESET_ALL}")
    print("-" * 60)
    
    app = EnhancedCryptoPredictionAppV2()
    new_pairs = ['LINKJPY', 'SOLJPY', 'ETHJPY']
    
    print(f"Phân tích nhanh 3 cặp coin mới cho kiểu đầu tư {Fore.CYAN}60m{Style.RESET_ALL}:")
    print()
    
    for i, pair in enumerate(new_pairs, 1):
        result = app.analyze_single_pair_by_investment_type(pair, '60m')
        
        if result:
            signal_color = Fore.GREEN if result['signal_type'] == 'BUY' else Fore.YELLOW
            quality_color = Fore.GREEN if result['entry_quality'] == 'HIGH' else Fore.YELLOW if result['entry_quality'] == 'MEDIUM' else Fore.RED
            
            print(f"{i}. {Fore.CYAN}{pair}{Style.RESET_ALL}")
            print(f"   Tín hiệu: {signal_color}{result['signal_type']}{Style.RESET_ALL}")
            print(f"   Xác suất: {Fore.YELLOW}{result['success_probability']:.1%}{Style.RESET_ALL}")
            print(f"   Chất lượng: {quality_color}{result['entry_quality']}{Style.RESET_ALL}")
            print(f"   Giá hiện tại: {Fore.YELLOW}{result['current_price']:,.0f}{Style.RESET_ALL}")
            
            if result['signal_type'] == 'BUY':
                tp1_pct = ((result['tp1']/result['entry_price']-1)*100)
                print(f"   Lãi dự kiến (TP1): {Fore.GREEN}+{tp1_pct:.2f}%{Style.RESET_ALL}")
            print()

def demo_usage_instructions():
    """Hướng dẫn sử dụng"""
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}📚 HƯỚNG DẪN SỬ DỤNG{Style.RESET_ALL}")
    print("-" * 60)
    
    print(f"{Fore.WHITE}🔹 Chạy phân tích cơ bản (60m):{Style.RESET_ALL}")
    print(f"   python3 enhanced_app_v2.py")
    print()
    
    print(f"{Fore.WHITE}🔹 Chạy phân tích tất cả khung thời gian:{Style.RESET_ALL}")
    print(f"   python3 enhanced_app_v2.py --multi")
    print()
    
    print(f"{Fore.WHITE}🔹 Chạy phân tích cho từng kiểu đầu tư:{Style.RESET_ALL}")
    print(f"   python3 enhanced_app_v2.py 60m    # Scalping")
    print(f"   python3 enhanced_app_v2.py 4h     # Swing")
    print(f"   python3 enhanced_app_v2.py 1d     # Position")
    print()
    
    print(f"{Fore.WHITE}🔹 Sử dụng Auto Runner:{Style.RESET_ALL}")
    print(f"   python3 auto_runner.py --once     # Chạy một lần")
    print(f"   python3 auto_runner.py --multi    # Tất cả khung thời gian")
    print(f"   python3 auto_runner.py --60m      # Chỉ scalping")
    print(f"   python3 auto_runner.py --4h       # Chỉ swing")
    print(f"   python3 auto_runner.py --1d       # Chỉ position")
    print()

def main():
    demo_header()
    
    print(f"🎬 {Fore.YELLOW}Bắt đầu demo các tính năng mới...{Style.RESET_ALL}\n")
    time.sleep(2)
    
    # Demo 1: Các kiểu đầu tư khác nhau
    demo_single_investment_types()
    
    # Demo 2: Các cặp coin mới
    demo_new_pairs()
    
    # Demo 3: Hướng dẫn sử dụng
    demo_usage_instructions()
    
    print(f"\n{Fore.GREEN}{Style.BRIGHT}✅ DEMO HOÀN THÀNH!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}🚀 App đã sẵn sàng với tất cả tính năng mới:{Style.RESET_ALL}")
    print(f"   • 3 kiểu đầu tư (60m, 4h, 1d)")
    print(f"   • 7 cặp coin JPY (bao gồm LINK, SOL, ETH)")
    print(f"   • TP/SL được tối ưu theo thời gian giữ lệnh")
    print(f"   • Phân tích đa khung thời gian")
    print()

if __name__ == "__main__":
    main()
