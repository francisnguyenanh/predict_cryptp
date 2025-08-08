#!/usr/bin/env python3
"""
Test script để kiểm tra trực tiếp hàm backtest
"""

import sys
import traceback
from enhanced_app_v2 import EnhancedCryptoPredictionAppV2

def test_backtest():
    print("🧪 Testing backtest function directly...")
    
    try:
        # Khởi tạo predictor
        predictor = EnhancedCryptoPredictionAppV2()
        print("✅ Predictor initialized successfully")
        
        # Test parameters
        symbol = "BTCUSDT"
        timeframe = "1h"
        days_back = 30
        pattern = "default"
        
        print(f"📊 Testing backtest with:")
        print(f"   - Symbol: {symbol}")
        print(f"   - Timeframe: {timeframe}")
        print(f"   - Days back: {days_back}")
        print(f"   - Pattern: {pattern}")
        
        # Run backtest
        result = predictor.run_backtest(symbol, timeframe, days_back, pattern)
        
        print("✅ Backtest completed successfully!")
        print(f"📈 Result type: {type(result)}")
        print(f"📈 Result: {result}")
        
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"   - {key}: {value}")
                
    except Exception as e:
        print(f"❌ Error during backtest:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        print(f"   Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_backtest()
