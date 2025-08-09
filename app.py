#!/usr/bin/env python3
"""
Flask Web App cho Crypto Prediction
Giao diện web với Bootstrap với hệ thống xác thực
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import time
import os
import hashlib
from datetime import datetime
from enhanced_app_v2 import EnhancedCryptoPredictionAppV2

app = Flask(__name__)
app.secret_key = 'crypto_prediction_secret_key_2025'

AUTH_FILE = 'auth.json'

# Khởi tạo crypto app
crypto_app = EnhancedCryptoPredictionAppV2()

def load_users():
    """Load users from auth.json file"""
    if not os.path.exists(AUTH_FILE):
        # Create default admin user if file doesn't exist
        default_users = {
            "users": {
                "admin": {
                    "password": "123456",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "permissions": ["admin", "read", "write"],
                    "active": True
                }
            }
        }
        save_users(default_users)
        return default_users
    
    try:
        with open(AUTH_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading users: {e}")
        return {"users": {}}

def save_users(users_data):
    """Save users to auth.json file"""
    try:
        with open(AUTH_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verify password - supports both plain text and hashed passwords"""
    # Check if stored password is already hashed (64 characters)
    if len(stored_password) == 64:
        return stored_password == hash_password(provided_password)
    else:
        # Plain text comparison for backward compatibility
        return stored_password == provided_password

def authenticate_user(username, password):
    """Authenticate user with username and password"""
    users_data = load_users()
    users = users_data.get('users', {})
    
    if username not in users:
        return False, "Tên đăng nhập không tồn tại"
    
    user = users[username]
    if not user.get('active', True):
        return False, "Tài khoản đã bị vô hiệu hóa"
    
    if verify_password(user['password'], password):
        # Update last login
        user['last_login'] = datetime.now().isoformat()
        save_users(users_data)
        return True, "Đăng nhập thành công"
    else:
        return False, "Mật khẩu không chính xác"

def change_user_password(username, current_password, new_password):
    """Change user password"""
    users_data = load_users()
    users = users_data.get('users', {})
    
    if username not in users:
        return False, "Tên đăng nhập không tồn tại"
    
    user = users[username]
    
    # Verify current password
    if not verify_password(user['password'], current_password):
        return False, "Mật khẩu hiện tại không chính xác"
    
    # Update password (hash it for security)
    user['password'] = hash_password(new_password)
    user['password_changed_at'] = datetime.now().isoformat()
    
    if save_users(users_data):
        return True, "Đổi mật khẩu thành công"
    else:
        return False, "Lỗi khi lưu mật khẩu mới"

def require_auth(f):
    """Decorator to require authentication for routes"""
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/login')
def login():
    """Login page"""
    if 'username' in session:
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for login"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu'
            })
        
        success, message = authenticate_user(username, password)
        
        if success:
            session['username'] = username
            session['last_login'] = datetime.now().isoformat()
            return jsonify({
                'success': True,
                'message': message,
                'redirect_url': url_for('index')
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Lỗi hệ thống: {str(e)}'
        })

@app.route('/api/change_password', methods=['POST'])
def api_change_password():
    """API endpoint for changing password"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not all([username, current_password, new_password]):
            return jsonify({
                'success': False,
                'error': 'Vui lòng nhập đầy đủ thông tin'
            })
        
        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'error': 'Mật khẩu mới phải có ít nhất 6 ký tự'
            })
        
        success, message = change_user_password(username, current_password, new_password)
        
        return jsonify({
            'success': success,
            'message': message if success else None,
            'error': None if success else message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Lỗi hệ thống: {str(e)}'
        })

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@require_auth
def index():
    """Trang chủ"""
    # Get sample coins for display
    sample_coins = crypto_app.get_top_coins_by_base_currency('USDT', 8)
    base_currencies = crypto_app.get_available_base_currencies()
    return render_template('index.html', 
                         sample_coins=sample_coins, 
                         base_currencies=base_currencies)

@app.route('/predict_buy')
@require_auth
def predict_buy():
    """Trang dự đoán mua"""
    base_currencies = crypto_app.get_available_base_currencies()
    return render_template('predict_buy.html', base_currencies=base_currencies)

@app.route('/api/predict_buy', methods=['POST'])
@require_auth
def api_predict_buy():
    """API dự đoán mua - phân tích đa khung thời gian"""
    try:
        data = request.get_json()
        base_currency = data.get('base_currency', 'USDT')
        
        # Get top coins for the selected base currency
        top_coins = crypto_app.get_top_coins_by_base_currency(base_currency, limit=10)
        if not top_coins:
            return jsonify({
                'success': False,
                'error': f'Không thể lấy dữ liệu coin cho base currency {base_currency}'
            })
        
        # Run analysis on selected coins
        coin_pairs = [coin['symbol'] for coin in top_coins]
        results = crypto_app.run_multi_timeframe_analysis(coin_pairs)
        
        # Format kết quả cho frontend
        formatted_results = []
        if results:
            for timeframe, result_list in results.items():
                if result_list and len(result_list) > 0:
                    # Lấy kết quả tốt nhất từ mỗi timeframe
                    best_result = result_list[0]  # Đã được sort theo success_probability
                    formatted_results.append({
                        'timeframe': timeframe,
                        'timeframe_display': get_timeframe_display(timeframe),
                        'symbol': best_result['symbol'],
                        'current_price': f"{best_result['current_price']:.6f}",
                        'entry_price': f"{best_result['entry_price']:.6f}",
                        'tp1': f"{best_result['tp1']:.6f}",
                        'tp2': f"{best_result['tp2']:.6f}",
                        'stop_loss': f"{best_result['stop_loss']:.6f}",
                        'success_probability': f"{best_result['success_probability']:.1%}",
                        'signal_type': best_result['signal_type'],
                        'trend_strength': best_result['trend_strength'],
                        'entry_quality': best_result['entry_quality'],
                        'tp1_percent': f"{((best_result['tp1']/best_result['entry_price']-1)*100):.2f}",
                        'tp2_percent': f"{((best_result['tp2']/best_result['entry_price']-1)*100):.2f}",
                        'sl_percent': f"{((1-best_result['stop_loss']/best_result['entry_price'])*100):.2f}",
                        'analysis_time': datetime.now().strftime('%H:%M:%S')
                    })
        
        return jsonify({
            'success': True,
            'results': formatted_results,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/analyze_sell')
@require_auth
def analyze_sell():
    """Trang phân tích bán"""
    base_currencies = crypto_app.get_available_base_currencies()
    return render_template('analyze_sell.html', base_currencies=base_currencies)

@app.route('/backtest')
@require_auth
def backtest():
    """Trang backtest"""
    base_currencies = crypto_app.get_available_base_currencies()
    return render_template('backtest.html', base_currencies=base_currencies)

@app.route('/api/analyze_sell', methods=['POST'])
@require_auth
def api_analyze_sell():
    """API phân tích xu hướng để quyết định hold hay bán"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Vui lòng chọn coin để phân tích'
            }), 400
        
        timeframes = ['60m', '4h', '1d']
        trend_analysis = {}
        
        for tf in timeframes:
            # Chạy phân tích cho từng khung thời gian
            result = crypto_app.analyze_single_pair_by_investment_type(symbol, tf)
            
            if result:
                current_price = result['current_price']
                trend_strength = result['trend_strength']
                success_prob = result['success_probability']
                tp1 = result['tp1']
                tp2 = result['tp2']
                
                # Phân tích xu hướng và đưa ra khuyến nghị
                if trend_strength == "STRONG_UP":
                    trend_direction = "📈 TĂNG MẠNH"
                    recommendation = "🔒 HOLD"
                    recommendation_detail = "Tiếp tục nắm giữ"
                    rec_class = "success"
                    tp_price = tp2
                    tp_percent = ((tp2 / current_price - 1) * 100)
                elif "UP" in trend_strength:
                    trend_direction = "📈 TĂNG"
                    recommendation = "🔒 HOLD"
                    recommendation_detail = "Tiếp tục nắm giữ"
                    rec_class = "success"
                    tp_price = tp1
                    tp_percent = ((tp1 / current_price - 1) * 100)
                elif trend_strength == "STRONG_DOWN":
                    trend_direction = "📉 GIẢM MẠNH"
                    recommendation = "💸 BÁN"
                    recommendation_detail = "Nên bán để cắt lỗ"
                    rec_class = "danger"
                    tp_price = current_price * 0.95
                    tp_percent = -5.0
                elif "DOWN" in trend_strength:
                    trend_direction = "📉 GIẢM"
                    recommendation = "💸 BÁN"
                    recommendation_detail = "Cân nhắc bán"
                    rec_class = "warning"
                    tp_price = current_price * 0.97
                    tp_percent = -3.0
                else:
                    trend_direction = "📊 SIDEWAY"
                    recommendation = "⏳ CHỜ"
                    recommendation_detail = "Quan sát thêm"
                    rec_class = "info"
                    tp_price = tp1
                    tp_percent = ((tp1 / current_price - 1) * 100)
                
                trend_analysis[tf] = {
                    'timeframe_display': get_timeframe_display(tf),
                    'direction': trend_direction,
                    'recommendation': recommendation,
                    'recommendation_detail': recommendation_detail,
                    'rec_class': rec_class,
                    'tp_price': f"{tp_price:.6f}",
                    'tp_percent': f"{tp_percent:+.2f}",
                    'accuracy': f"{success_prob * 100:.1f}",
                    'current_price': f"{current_price:.6f}"
                }
            else:
                trend_analysis[tf] = {
                    'timeframe_display': get_timeframe_display(tf),
                    'direction': "❌ Lỗi dữ liệu",
                    'recommendation': "⏳ CHỜ",
                    'recommendation_detail': "Không thể phân tích",
                    'rec_class': "secondary",
                    'tp_price': "N/A",
                    'tp_percent': "N/A",
                    'accuracy': "N/A",
                    'current_price': "N/A"
                }
            
            time.sleep(1)  # Tránh spam API
        
        # Đưa ra khuyến nghị tổng hợp
        valid_analyses = [data for data in trend_analysis.values() if "Lỗi" not in data['direction']]
        up_count = sum(1 for data in valid_analyses if "TĂNG" in data['direction'])
        down_count = sum(1 for data in valid_analyses if "GIẢM" in data['direction'])
        
        if up_count >= 2:
            overall_recommendation = {
                'action': "🔒 HOLD",
                'detail': "Xu hướng tăng trên nhiều khung thời gian",
                'class': "success",
                'note': "📈 Có thể tăng thêm trong thời gian tới"
            }
        elif down_count >= 2:
            overall_recommendation = {
                'action': "💸 BÁN",
                'detail': "Xu hướng giảm trên nhiều khung thời gian",
                'class': "danger", 
                'note': "📉 Nên cân nhắc bán để bảo vệ lợi nhuận/cắt lỗ"
            }
        else:
            overall_recommendation = {
                'action': "⏳ CHỜ",
                'detail': "Xu hướng chưa rõ ràng, quan sát thêm",
                'class': "info",
                'note': "📊 Sideway, chờ tín hiệu rõ hơn"
            }
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'analysis': trend_analysis,
            'overall': overall_recommendation,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status')
@require_auth
def api_status():
    """API kiểm tra trạng thái hệ thống"""
    try:
        # Test kết nối đến crypto_app
        test_coins = crypto_app.get_top_coins_by_base_currency('USDT', 5)
        
        return jsonify({
            'success': True,
            'status': 'online',
            'base_currencies': crypto_app.get_available_base_currencies(),
            'sample_coins_count': len(test_coins),
            'data_available': len(test_coins) > 0,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e)
        }), 500

def format_volume(vol):
    if vol >= 1e9:
        return f"{vol/1e9:.2f}B"
    elif vol >= 1e6:
        return f"{vol/1e6:.2f}M"
    elif vol >= 1e3:
        return f"{vol/1e3:.2f}K"
    else:
        return f"{vol:.2f}"
    
@app.route('/api/coins/<base_currency>')
@require_auth
def api_get_coins(base_currency):
    """API lấy danh sách coins theo base currency"""
    try:
        limit = request.args.get('limit', 15, type=int)
        page_type = request.args.get('type', 'general')  # general, predict_buy, analyze_sell, backtest
        
        # Điều chỉnh limit theo loại trang
        if page_type == 'predict_buy':
            limit = 10  # Top 10 cho predict buy
        elif page_type in ['analyze_sell', 'backtest']:
            limit = 15  # Top 15 cho analyze sell và backtest
            
        coins = crypto_app.get_top_coins_by_base_currency(base_currency, limit)
        for coin in coins:
            coin['volume_display'] = format_volume(coin.get('volume', 0))
        
        return jsonify({
            'success': True,
            'base_currency': base_currency,
            'coins': coins,
            'count': len(coins),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/backtest', methods=['POST'])
@require_auth
def api_backtest():
    """API chạy backtest với pattern"""
    try:
        #print("🔍 Backtest API called")
        data = request.get_json()
        #print(f"🔍 Received data: {data}")
        
        symbol = data.get('symbol', 'BTCUSDT')
        timeframe = data.get('timeframe', '4h')
        days_back = int(data.get('days_back', 30))
        pattern_name = data.get('pattern', 'default')  # Changed from pattern_name to pattern
        
        #print(f"🔍 Parameters: symbol={symbol}, timeframe={timeframe}, days_back={days_back}, pattern={pattern_name}")
        
        # Chạy backtest với pattern
        backtest_results = crypto_app.run_backtest(symbol, timeframe, days_back, pattern_name)
        
        #print(f"🔍 Backtest results: {backtest_results}")
        
        if not backtest_results:
            #print("❌ No backtest results")
            return jsonify({
                'success': False,
                'error': 'Không thể thực hiện backtest'
            }), 400
        
        # Add symbol to results for frontend formatting
        backtest_results['symbol'] = symbol
        
        #print("✅ Returning successful response")
        return jsonify({
            'success': True,
            'results': backtest_results,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        #print(f"❌ Backtest API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/patterns')
@require_auth
def api_patterns():
    """API lấy danh sách patterns"""
    try:
        patterns = crypto_app.market_patterns
        return jsonify({
            'success': True,
            'patterns': patterns,
            'active_pattern': crypto_app.active_pattern,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/set_pattern', methods=['POST'])
@require_auth
def api_set_pattern():
    """API thiết lập pattern hiện tại"""
    try:
        data = request.get_json()
        pattern_name = data.get('pattern')  # Changed from pattern_name to pattern
        
        if not pattern_name:
            return jsonify({
                'success': False,
                'error': 'Vui lòng chọn pattern'
            }), 400
        
        if crypto_app.set_market_pattern(pattern_name):
            return jsonify({
                'success': True,
                'message': f'Đã chuyển sang pattern: {pattern_name}',
                'active_pattern': crypto_app.active_pattern,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Pattern không tồn tại'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pattern_comparison', methods=['POST'])
@require_auth
def api_pattern_comparison():
    """API so sánh nhiều patterns"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'BTCUSDT')
        timeframe = data.get('timeframe', '4h')
        days_back = int(data.get('days_back', 30))
        
        comparison_results = {}
        patterns_to_test = ['default', 'bull_market', 'bear_market', 'sideways', 'high_volatility', 'low_volatility', 'breakout', 'scalping']
        
        for pattern in patterns_to_test:
            result = crypto_app.run_backtest(symbol, timeframe, days_back, pattern)
            if result:
                result['symbol'] = symbol  # Add symbol to each result
                comparison_results[pattern] = result
            time.sleep(0.5)  # Small delay between tests
        
        return jsonify({
            'success': True,
            'results': comparison_results,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_timeframe_display(tf):
    """Chuyển đổi timeframe thành tên hiển thị"""
    display_map = {
        '60m': '60 phút',
        '4h': '4 giờ', 
        '1d': '1 ngày'
    }
    return display_map.get(tf, tf)

if __name__ == '__main__':
    app.run(debug=True)
