#!/usr/bin/env python3
"""
Auto Runner cho Crypto Prediction App
Chạy phân tích tự động theo chu kỳ
"""

import time
import schedule
from datetime import datetime
from enhanced_app_v2 import EnhancedCryptoPredictionAppV2

class AutoRunner:
    def __init__(self, interval_minutes=35):  # Thay đổi từ 15 thành 35 phút
        self.app = EnhancedCryptoPredictionAppV2()
        self.interval_minutes = interval_minutes
        
    def run_analysis_job(self):
        """Chạy phân tích và lưu kết quả"""
        try:
            # print(f"\n{'='*60}")
            # print(f"🔄 AUTO RUN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            # print(f"{'='*60}")
            
            results = self.app.run_enhanced_analysis()
            
            # Lưu kết quả vào file log
            #self.save_results_to_log(results)
            
            #print(f"\n✅ Phân tích hoàn thành - Chờ {self.interval_minutes} phút cho lần tiếp theo...")
            
        except Exception as e:
            print(f"❌ Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    main()
    
    def run_multi_timeframe_analysis_job(self):
        """Chạy phân tích đa khung thời gian"""
        try:
            all_results = self.app.run_multi_timeframe_analysis()
            return all_results
        except Exception as e:
            print(f"❌ Lỗi trong quá trình phân tích đa khung thời gian: {e}")
            return None
    
    def run_single_investment_type_job(self, investment_type):
        """Chạy phân tích cho một kiểu đầu tư cụ thể"""
        try:
            results = []
            for pair in self.app.pairs:
                result = self.app.analyze_single_pair_by_investment_type(pair, investment_type)
                if result:
                    results.append(result)
                time.sleep(1)
            
            results.sort(key=lambda x: x['success_probability'], reverse=True)
            return results
        except Exception as e:
            print(f"❌ Lỗi phân tích {investment_type}: {e}")
            return None
    
    def save_results_to_log(self, results):
        """Lưu kết quả vào file log"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"analysis_log_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Crypto Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*80 + "\n\n")
                
                for i, result in enumerate(results, 1):
                    f.write(f"#{i} - {result['symbol']}\n")
                    f.write(f"Giá: {result['current_price']:.6f}\n")
                    f.write(f"Tín hiệu: {result['signal_type']}\n")
                    f.write(f"Xác suất: {result['success_probability']:.1%}\n")
                    f.write(f"Chất lượng: {result['entry_quality']}\n")
                    f.write(f"RSI: {result['rsi']:.1f}\n")
                    
                    trends_str = " | ".join([f"{tf}: {trend}" for tf, trend in result['trends'].items()])
                    f.write(f"Xu hướng: {trends_str}\n")
                    
                    if result['signal_type'] == 'BUY':
                        f.write(f"Entry: {result['entry_price']:.6f}\n")
                        f.write(f"TP1: {result['tp1']:.6f} (+{((result['tp1']/result['entry_price']-1)*100):.2f}%)\n")
                        f.write(f"TP2: {result['tp2']:.6f} (+{((result['tp2']/result['entry_price']-1)*100):.2f}%)\n")
                        f.write(f"SL: {result['stop_loss']:.6f} (-{((1-result['stop_loss']/result['entry_price'])*100):.2f}%)\n")
                    elif result['signal_type'] == 'WAIT':
                        f.write(f"Khuyến nghị: Chờ thời điểm tốt hơn\n")
                        f.write(f"Target Entry: {result['entry_price']:.6f}\n")
                    
                    # Thêm thông tin accuracy mới
                    pred_results = result['prediction_results']
                    if pred_results['total'] > 0:
                        f.write(f"Latest Accuracy: {pred_results['latest_accuracy']:.0f}%\n")
                        f.write(f"Average Accuracy: {pred_results['average_accuracy']:.0f}%\n")
                    else:
                        f.write(f"Accuracy: NEW (chưa có dữ liệu)\n")
                    
                    f.write("-" * 50 + "\n\n")
                
                if results:
                    best = results[0]
                    f.write("KHUYẾN NGHỊ TỐT NHẤT:\n")
                    f.write(f"Coin: {best['symbol']}\n")
                    f.write(f"Signal: {best['signal_type']}\n")
                    f.write(f"Probability: {best['success_probability']:.1%}\n")
                    f.write(f"Quality: {best['entry_quality']}\n")
            
            print(f"📝 Kết quả đã được lưu vào: {filename}")
            
        except Exception as e:
            print(f"❌ Lỗi khi lưu log: {e}")
    
    # Đã loại bỏ chức năng chạy tự động theo interval
    pass
    
    def run_once(self):
        self.run_analysis_job()

def show_menu():
    """Hiển thị menu lựa chọn"""
    print("\n" + "="*60)
    print("🚀 CRYPTO PREDICTION APP - MENU CHÍNH")
    print("="*60)
    print("1. 📈 Dự đoán MUA - Tìm coin tốt để mua vào")
    print("2. 📉 Dự đoán BÁN - Phân tích xu hướng coin đang hold")
    print("3. 🚪 Thoát")
    print("="*60)

def show_coin_selection_menu(runner):
    """Hiển thị menu chọn coin để phân tích bán"""
    print("\n" + "="*50)
    print("💰 CHỌN COIN ĐỂ PHÂN TÍCH XU HƯỚNG")
    print("="*50)
    
    for i, pair in enumerate(runner.app.pairs, 1):
        print(f"{i}. {pair}")
    
    print(f"{len(runner.app.pairs) + 1}. 🔙 Quay lại menu chính")
    print("="*50)

def analyze_sell_trend(runner, symbol):
    """Phân tích xu hướng để quyết định hold hay bán"""
    print(f"\n🔍 PHÂN TÍCH XU HƯỚNG: {symbol}")
    print("="*60)
    
    timeframes = ['60m', '1h', '4h']
    trend_analysis = {}
    
    for tf in timeframes:
        print(f"📊 Đang phân tích khung {tf}...")
        
        if tf == '1h':
            # Sử dụng khung 4h cho phân tích
            result = runner.app.analyze_single_pair_by_investment_type(symbol, '4h')
        else:
            result = runner.app.analyze_single_pair_by_investment_type(symbol, tf)
        
        if result:
            current_price = result['current_price']
            trend_strength = result['trend_strength']
            success_prob = result['success_probability']
            tp1 = result['tp1']
            tp2 = result['tp2']
            
            # Phân tích xu hướng
            if trend_strength == "STRONG_UP":
                trend_direction = "📈 TĂNG MẠNH"
                recommendation = "🔒 HOLD - Tiếp tục nắm giữ"
                tp_price = tp2
                tp_percent = ((tp2 / current_price - 1) * 100)
            elif "UP" in trend_strength:
                trend_direction = "📈 TĂNG"
                recommendation = "🔒 HOLD - Tiếp tục nắm giữ"
                tp_price = tp1
                tp_percent = ((tp1 / current_price - 1) * 100)
            elif trend_strength == "STRONG_DOWN":
                trend_direction = "📉 GIẢM MẠNH"
                recommendation = "💸 BÁN - Nên bán để cắt lỗ"
                tp_price = current_price * 0.95  # Giảm 5%
                tp_percent = -5.0
            elif "DOWN" in trend_strength:
                trend_direction = "📉 GIẢM"
                recommendation = "💸 BÁN - Cân nhắc bán"
                tp_price = current_price * 0.97  # Giảm 3%
                tp_percent = -3.0
            else:  # MIXED, WAIT
                trend_direction = "📊 SIDEWAY"
                recommendation = "⏳ CHỜ - Quan sát thêm"
                tp_price = tp1
                tp_percent = ((tp1 / current_price - 1) * 100)
            
            trend_analysis[tf] = {
                'direction': trend_direction,
                'recommendation': recommendation,
                'tp_price': tp_price,
                'tp_percent': tp_percent,
                'accuracy': success_prob * 100,
                'current_price': current_price
            }
        else:
            trend_analysis[tf] = {
                'direction': "❌ Lỗi dữ liệu",
                'recommendation': "⏳ CHỜ",
                'tp_price': 0,
                'tp_percent': 0,
                'accuracy': 0,
                'current_price': 0
            }
        
        time.sleep(1)
    
    # Hiển thị kết quả
    print(f"\n📋 KẾT QUẢ PHÂN TÍCH: {symbol}")
    print("="*60)
    
    if trend_analysis['60m']['current_price'] > 0:
        print(f"💰 Giá hiện tại: {trend_analysis['60m']['current_price']:.6f}")
    
    print(f"\n{'Khung':<8} {'Xu hướng':<15} {'Khuyến nghị':<20} {'Mục tiêu':<12} {'Tỷ lệ':<8} {'Độ chính xác'}")
    print("-" * 75)
    
    for tf in timeframes:
        data = trend_analysis[tf]
        if data['tp_price'] > 0:
            print(f"{tf:<8} {data['direction']:<15} {data['recommendation']:<20} {data['tp_price']:<12.6f} {data['tp_percent']:>+6.2f}% {data['accuracy']:>8.1f}%")
        else:
            print(f"{tf:<8} {data['direction']:<15} {data['recommendation']:<20} {'N/A':<12} {'N/A':<8} {'N/A':>8}")
    
    # Đưa ra khuyến nghị tổng hợp
    print(f"\n🎯 KHUYẾN NGHỊ TỔNG HỢP:")
    print("-" * 30)
    
    up_count = sum(1 for data in trend_analysis.values() if "TĂNG" in data['direction'])
    down_count = sum(1 for data in trend_analysis.values() if "GIẢM" in data['direction'])
    
    if up_count >= 2:
        print("🔒 HOLD - Xu hướng tăng trên nhiều khung thời gian")
        print("📈 Có thể tăng thêm trong thời gian tới")
    elif down_count >= 2:
        print("💸 BÁN - Xu hướng giảm trên nhiều khung thời gian")
        print("📉 Nên cân nhắc bán để bảo vệ lợi nhuận/cắt lỗ")
    else:
        print("⏳ CHỜ - Xu hướng chưa rõ ràng, quan sát thêm")
        print("📊 Sideway, chờ tín hiệu rõ hơn")

def main():
    import sys
    
    runner = AutoRunner(interval_minutes=35)
    
    # Nếu có tham số dòng lệnh, chạy như cũ
    if len(sys.argv) > 1:
        if sys.argv[1] == "--auto":
            runner.start_auto_mode()
        elif sys.argv[1] == "--once":
            runner.run_once()
        elif sys.argv[1] == "--multi":
            runner.run_multi_timeframe_analysis_job()
        elif sys.argv[1] in ["--60m", "--4h", "--1d"]:
            investment_type = sys.argv[1][2:]
            runner.run_single_investment_type_job(investment_type)
        else:
            runner.run_multi_timeframe_analysis_job()
        return
    
    # Menu tương tác
    while True:
        show_menu()
        try:
            choice = input("\n👉 Nhập lựa chọn của bạn (1-3): ").strip()
            
            if choice == '1':
                print("\n🔄 Đang chạy phân tích dự đoán MUA...")
                runner.run_multi_timeframe_analysis_job()
                
            elif choice == '2':
                while True:
                    show_coin_selection_menu(runner)
                    try:
                        coin_choice = input(f"\n👉 Chọn coin (1-{len(runner.app.pairs) + 1}): ").strip()
                        
                        if coin_choice == str(len(runner.app.pairs) + 1):
                            break  # Quay lại menu chính
                        
                        coin_index = int(coin_choice) - 1
                        if 0 <= coin_index < len(runner.app.pairs):
                            selected_coin = runner.app.pairs[coin_index]
                            analyze_sell_trend(runner, selected_coin)
                            
                            input("\n📌 Nhấn Enter để tiếp tục...")
                        else:
                            print("❌ Lựa chọn không hợp lệ!")
                            
                    except ValueError:
                        print("❌ Vui lòng nhập số!")
                    except KeyboardInterrupt:
                        print("\n👋 Tạm biệt!")
                        return
                        
            elif choice == '3':
                print("👋 Cảm ơn bạn đã sử dụng Crypto Prediction App!")
                break
                
            else:
                print("❌ Lựa chọn không hợp lệ! Vui lòng chọn 1, 2 hoặc 3.")
                
        except KeyboardInterrupt:
            print("\n👋 Tạm biệt!")
            break
        except Exception as e:
            print(f"❌ Có lỗi xảy ra: {e}")
    
    # if len(sys.argv) > 1:
    #     if sys.argv[1] == "--auto":
    #         runner.start_auto_mode()
    #     elif sys.argv[1] == "--once":
    #         runner.run_once()
    #     elif sys.argv[1] == "--multi":
    #         # Chạy phân tích đa khung thời gian
    #         runner.run_multi_timeframe_analysis_job()
    #     elif sys.argv[1] in ["--60m", "--4h", "--1d"]:
    #         # Chạy phân tích cho một kiểu đầu tư cụ thể
    #         investment_type = sys.argv[1][2:]  # Bỏ "--"
    #         runner.run_single_investment_type_job(investment_type)
    #     elif sys.argv[1] == "--interval" and len(sys.argv) > 2:
    #         try:
    #             interval = int(sys.argv[2])
    #             runner = AutoRunner(interval_minutes=interval)
    #             runner.start_auto_mode()
    #         except ValueError:
    #             print("❌ Interval phải là số nguyên (phút)")
    #     else:
    #         print("Usage:")
    #         print("  python auto_runner.py --once           # Chạy một lần (60m)")
    #         print("  python auto_runner.py --multi          # Chạy tất cả các kiểu đầu tư (60m, 4h, 1d)")
    #         print("  python auto_runner.py --60m            # Chạy phân tích 60 phút")
    #         print("  python auto_runner.py --4h             # Chạy phân tích 4 giờ")
    #         print("  python auto_runner.py --1d             # Chạy phân tích 1 ngày")
    #         print("  python auto_runner.py --interval 30    # Chạy tự động mỗi 30 phút")
    # else:
    #     # Mặc định chạy một lần (60m)
    #     runner.run_once()

if __name__ == "__main__":
    main()
    
