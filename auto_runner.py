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
            print(f"❌ Lỗi trong quá trình phân tích: {e}")
    
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

def main():
    import sys
    
    runner = AutoRunner(interval_minutes=35)  # Thay đổi từ 15 thành 35 phút
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--auto":
            runner.start_auto_mode()
        elif sys.argv[1] == "--once":
            runner.run_once()
        elif sys.argv[1] == "--interval" and len(sys.argv) > 2:
            try:
                interval = int(sys.argv[2])
                runner = AutoRunner(interval_minutes=interval)
                runner.start_auto_mode()
            except ValueError:
                print("❌ Interval phải là số nguyên (phút)")
        else:
            print("Usage:")
            # print("  python auto_runner.py --once           # Chạy một lần")
            # print("  python auto_runner.py --auto           # Chạy tự động mỗi 35 phút (tối ưu)")
            # print("  python auto_runner.py --interval 30    # Chạy tự động mỗi 30 phút")
            # print("  python auto_runner.py --interval 45    # Chạy tự động mỗi 45 phút")
    else:
        # Mặc định chạy một lần
        runner.run_once()

if __name__ == "__main__":
    main()
