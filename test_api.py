#!/usr/bin/env python3
"""
Test API endpoint sau khi fix backtest function
"""

import requests
import json

def test_api():
    print("🧪 Testing API endpoint...")
    
    # Test API endpoint
    data = {
        'symbol': 'BTCUSDT',
        'timeframe': '1h', 
        'days_back': 30,
        'pattern': 'default'
    }

    try:
        print(f"📤 Sending request to API...")
        response = requests.post('http://localhost:5000/api/backtest', json=data, timeout=60)
        print(f'📨 Status Code: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Success: {result["success"]}')
            if result["success"] and "results" in result:
                data = result["results"]
                print(f'📊 Total trades: {data["total_trades"]}')
                print(f'📈 Win rate: {data["win_rate"]}%')
                print(f'💰 Total PnL: {data["total_pnl"]}%')
                print(f'⚖️ Profit Factor: {data["profit_factor"]}')
                print(f'🎯 Performance Score: {data["performance_score"]}/100')
                print(f'✅ Winning trades: {data["winning_trades"]}')
                print(f'❌ Losing trades: {data["losing_trades"]}')
                print(f'🎯 TP1 hits: {data["tp1_hits"]}')
                print(f'🛑 SL hits: {data["sl_hits"]}')
                print(f'⏰ Timeouts: {data["timeouts"]}')
            else:
                print(f'❌ Error or missing data: {result.get("error", "Unknown error")}')
                print(f'📋 Available keys: {list(result.keys())}')
        else:
            print(f'❌ HTTP Error: {response.status_code}')
            print(f'📝 Response: {response.text}')
    except requests.exceptions.Timeout:
        print(f'⏰ Request timeout after 60 seconds')
    except requests.exceptions.ConnectionError:
        print(f'🔌 Connection error - make sure server is running')
    except Exception as e:
        print(f'💥 Unexpected error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()
