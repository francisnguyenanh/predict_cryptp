#!/usr/bin/env python3
"""
Test script để kiểm tra logic SPOT BUY
"""

from enhanced_app_v2 import EnhancedCryptoPredictionAppV2
from colorama import Fore, Style
import colorama

colorama.init()

def test_spot_buy_logic():
    """Test logic SPOT BUY cho một coin cụ thể"""
    
    print(f"{Fore.CYAN}🧪 KIỂM TRA LOGIC SPOT BUY{Style.RESET_ALL}")
    print("=" * 50)
    
    # Tạo app instance
    app = EnhancedCryptoPredictionAppV2()
    
    # Test với một coin cụ thể
    symbol = "BTCUSDT"
    investment_type = "60m"
    
    print(f"📊 Đang phân tích {symbol} cho {investment_type}...")
    
    result = app.analyze_single_pair_by_investment_type(symbol, investment_type)
    
    if result:
        print(f"\n{Fore.GREEN}✅ KẾT QUẢ PHÂN TÍCH:{Style.RESET_ALL}")
        print(f"Symbol: {result['symbol']}")
        print(f"Tín hiệu: {result['signal_type']}")
        print(f"Giá vào lệnh: {result['entry_price']:.6f}")
        
        if result['signal_type'] == 'BUY':
            print(f"\n{Fore.YELLOW}💰 SPOT BUY - THÔNG TIN CHI TIẾT:{Style.RESET_ALL}")
            print(f"Entry Price: {result['entry_price']:.6f}")
            print(f"TP1: {result['tp1']:.6f}")
            print(f"TP2: {result['tp2']:.6f}")
            print(f"Stop Loss: {result['stop_loss']:.6f}")
            
            # Kiểm tra logic đúng cho BUY
            print(f"\n{Fore.BLUE}🔍 KIỂM TRA LOGIC:{Style.RESET_ALL}")
            tp1_check = result['tp1'] > result['entry_price']
            tp2_check = result['tp2'] > result['entry_price'] 
            sl_check = result['stop_loss'] < result['entry_price']
            
            print(f"TP1 > Entry: {tp1_check} ✅" if tp1_check else f"TP1 > Entry: {tp1_check} ❌")
            print(f"TP2 > Entry: {tp2_check} ✅" if tp2_check else f"TP2 > Entry: {tp2_check} ❌")
            print(f"SL < Entry: {sl_check} ✅" if sl_check else f"SL < Entry: {sl_check} ❌")
            
            # Tính phần trăm
            tp1_pct = ((result['tp1']/result['entry_price'])-1)*100
            tp2_pct = ((result['tp2']/result['entry_price'])-1)*100
            sl_pct = ((result['stop_loss']/result['entry_price'])-1)*100
            
            print(f"\n{Fore.CYAN}📊 PHẦN TRĂM:{Style.RESET_ALL}")
            print(f"TP1: +{tp1_pct:.2f}%")
            print(f"TP2: +{tp2_pct:.2f}%")
            print(f"Stop Loss: {sl_pct:.2f}%")
            
            print(f"R/R Ratio: {result['rr_ratio']:.2f}")
            print(f"Xác suất thành công: {result['success_probability']*100:.1f}%")
            
        elif result['signal_type'] == 'SELL':
            print(f"\n{Fore.RED}❌ LỖI: Hệ thống đã tạo tín hiệu SELL trong SPOT TRADING!{Style.RESET_ALL}")
            print("Spot trading chỉ nên có BUY hoặc WAIT signals.")
            
        else:  # WAIT
            print(f"\n{Fore.YELLOW}⏳ TÍN HIỆU WAIT - KHÔNG MUA VÀO{Style.RESET_ALL}")
            print("Hệ thống khuyến nghị chờ đợi.")
            
    else:
        print(f"{Fore.RED}❌ Không thể phân tích {symbol}{Style.RESET_ALL}")

if __name__ == "__main__":
    test_spot_buy_logic()
