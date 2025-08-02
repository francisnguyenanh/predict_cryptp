#!/usr/bin/env python3
"""
Detailed Report Generator cho Crypto Prediction App
Tạo báo cáo chi tiết với biểu đồ và phân tích sâu
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import os
from enhanced_app import EnhancedCryptoPredictionApp

class ReportGenerator:
    def __init__(self):
        self.app = EnhancedCryptoPredictionApp()
        self.report_dir = "reports"
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
    
    def generate_price_chart(self, symbol, df, signals, save_path):
        """Tạo biểu đồ giá với các tín hiệu"""
        plt.style.use('dark_background')
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), height_ratios=[3, 1, 1])
        
        # Price chart with EMAs
        ax1.plot(df.index, df['close'], label='Price', linewidth=2, color='white')
        ax1.plot(df.index, df['EMA_10'], label='EMA 10', alpha=0.8, color='yellow')
        ax1.plot(df.index, df['EMA_20'], label='EMA 20', alpha=0.8, color='orange')
        ax1.plot(df.index, df['EMA_50'], label='EMA 50', alpha=0.8, color='red')
        
        # Bollinger Bands
        if 'BB_upper' in df.columns:
            ax1.fill_between(df.index, df['BB_lower'], df['BB_upper'], 
                           alpha=0.2, color='blue', label='Bollinger Bands')
        
        # Support/Resistance
        ax1.plot(df.index, df['support'], '--', alpha=0.6, color='green', label='Support')
        ax1.plot(df.index, df['resistance'], '--', alpha=0.6, color='red', label='Resistance')
        
        ax1.set_title(f'{symbol} - Price Analysis', fontsize=16, fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # RSI
        ax2.plot(df.index, df['RSI'], color='purple', linewidth=2, label='RSI')
        ax2.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Overbought')
        ax2.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Oversold')
        ax2.fill_between(df.index, 30, 70, alpha=0.1, color='gray')
        ax2.set_ylabel('RSI')
        ax2.set_ylim(0, 100)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        # Volume
        colors = ['green' if close >= open else 'red' for close, open in zip(df['close'], df['open'])]
        ax3.bar(df.index, df['volume'], color=colors, alpha=0.7)
        ax3.plot(df.index, df['volume_sma'], color='yellow', linewidth=2, label='Volume SMA')
        ax3.set_ylabel('Volume')
        ax3.legend(loc='upper left')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='black')
        plt.close()
    
    def generate_signals_summary(self, results):
        """Tạo tóm tắt tín hiệu"""
        summary = {
            'total_pairs': len(results),
            'buy_signals': len([r for r in results if r['signal_type'] == 'BUY']),
            'sell_signals': len([r for r in results if r['signal_type'] == 'SELL']),
            'high_quality': len([r for r in results if r['entry_quality'] == 'HIGH']),
            'medium_quality': len([r for r in results if r['entry_quality'] == 'MEDIUM']),
            'low_quality': len([r for r in results if r['entry_quality'] == 'LOW']),
            'avg_probability': sum([r['success_probability'] for r in results]) / len(results) if results else 0,
            'avg_rr_ratio': sum([r['rr_ratio'] for r in results]) / len(results) if results else 0
        }
        return summary
    
    def create_detailed_html_report(self, results):
        """Tạo báo cáo HTML chi tiết"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.report_dir, f'crypto_report_{timestamp}.html')
        
        summary = self.generate_signals_summary(results)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .summary-card {{
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #FFD700;
        }}
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #00FF88;
        }}
        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            overflow: hidden;
        }}
        .results-table th, .results-table td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .results-table th {{
            background: rgba(255, 255, 255, 0.1);
            font-weight: bold;
            color: #FFD700;
        }}
        .buy-signal {{ color: #00FF88; font-weight: bold; }}
        .sell-signal {{ color: #FF6B6B; font-weight: bold; }}
        .high-quality {{ color: #00FF88; }}
        .medium-quality {{ color: #FFD700; }}
        .low-quality {{ color: #FF6B6B; }}
        .detail-section {{
            margin: 30px 0;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }}
        .signal-badge {{
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
            margin: 2px;
            display: inline-block;
        }}
        .trend-up {{ background: #00FF88; color: black; }}
        .trend-down {{ background: #FF6B6B; color: white; }}
        .trend-side {{ background: #FFD700; color: black; }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            color: #ccc;
        }}
        .recommendation {{
            background: linear-gradient(135deg, #FFD700, #FFA500);
            color: black;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            font-weight: bold;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 CRYPTO PREDICTION REPORT</h1>
            <h2>Advanced Technical Analysis</h2>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>📊 Total Pairs</h3>
                <div class="value">{summary['total_pairs']}</div>
            </div>
            <div class="summary-card">
                <h3>📈 Buy Signals</h3>
                <div class="value">{summary['buy_signals']}</div>
            </div>
            <div class="summary-card">
                <h3>📉 Sell Signals</h3>
                <div class="value">{summary['sell_signals']}</div>
            </div>
            <div class="summary-card">
                <h3>⭐ High Quality</h3>
                <div class="value">{summary['high_quality']}</div>
            </div>
            <div class="summary-card">
                <h3>🎯 Avg Probability</h3>
                <div class="value">{summary['avg_probability']:.1%}</div>
            </div>
            <div class="summary-card">
                <h3>💰 Avg R/R Ratio</h3>
                <div class="value">{summary['avg_rr_ratio']:.2f}</div>
            </div>
        </div>
        
        <div class="detail-section">
            <h2>📊 DETAILED ANALYSIS RESULTS</h2>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Symbol</th>
                        <th>Price</th>
                        <th>Signal</th>
                        <th>Probability</th>
                        <th>Quality</th>
                        <th>RSI</th>
                        <th>Trends</th>
                        <th>TP1 %</th>
                        <th>SL %</th>
                        <th>R/R Ratio</th>
                        <th>Active Signals</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for i, result in enumerate(results, 1):
            # Calculate percentages
            if result['signal_type'] == 'BUY':
                tp1_pct = ((result['tp1']/result['current_price']-1)*100)
                sl_pct = -((1-result['stop_loss']/result['current_price'])*100)
            else:
                tp1_pct = -((1-result['tp1']/result['current_price'])*100)
                sl_pct = ((result['stop_loss']/result['current_price']-1)*100)
            
            signal_class = 'buy-signal' if result['signal_type'] == 'BUY' else 'sell-signal'
            quality_class = f"{result['entry_quality'].lower()}-quality"
            
            # Trend analysis
            trends_html = ""
            for tf, trend in result['trends'].items():
                trend_class = 'trend-up' if trend == 'UPTREND' else 'trend-down' if trend == 'DOWNTREND' else 'trend-side'
                trends_html += f'<span class="signal-badge {trend_class}">{tf}: {trend}</span>'
            
            # Active signals
            active_signals = [k for k, v in result['signals'].items() if v]
            signals_html = ', '.join(active_signals[:3]) + ('...' if len(active_signals) > 3 else '')
            
            html_content += f"""
                    <tr>
                        <td>#{i}</td>
                        <td><strong>{result['symbol']}</strong></td>
                        <td>{result['current_price']:.6f}</td>
                        <td class="{signal_class}">{result['signal_type']}</td>
                        <td>{result['success_probability']:.1%}</td>
                        <td class="{quality_class}">{result['entry_quality']}</td>
                        <td>{result['rsi']:.1f}</td>
                        <td>{trends_html}</td>
                        <td>{tp1_pct:+.2f}%</td>
                        <td>{sl_pct:+.2f}%</td>
                        <td>{result['rr_ratio']:.2f}</td>
                        <td><small>{signals_html}</small></td>
                    </tr>
            """
        
        # Top recommendation
        if results:
            best = results[0]
            recommendation_color = "#00FF88" if best['success_probability'] > 0.75 else "#FFD700" if best['success_probability'] > 0.6 else "#FF6B6B"
            
            html_content += f"""
                </tbody>
            </table>
        </div>
        
        <div class="recommendation" style="background: linear-gradient(135deg, {recommendation_color}, {recommendation_color}aa);">
            <h2>🏆 TOP RECOMMENDATION</h2>
            <h3>{best['symbol']} - {best['signal_type']}</h3>
            <p>Success Probability: {best['success_probability']:.1%} | Quality: {best['entry_quality']} | R/R: {best['rr_ratio']:.2f}</p>
            <p>{"✅ STRONG SIGNAL - Recommended" if best['success_probability'] > 0.75 else "⚠️ MODERATE SIGNAL - Trade with caution" if best['success_probability'] > 0.6 else "❌ WEAK SIGNAL - Not recommended"}</p>
        </div>
        
        <div class="detail-section">
            <h2>📋 ANALYSIS METHODOLOGY</h2>
            <ul>
                <li><strong>Multi-timeframe Analysis:</strong> 15m (primary), 1h, 4h trend confirmation</li>
                <li><strong>Technical Indicators:</strong> EMA, RSI, MACD, Bollinger Bands, ATR, Volume</li>
                <li><strong>Signal Scoring:</strong> Weighted scoring system based on indicator strength</li>
                <li><strong>Risk Management:</strong> ATR-based TP/SL calculation with R/R optimization</li>
                <li><strong>Pattern Recognition:</strong> Candlestick patterns and support/resistance levels</li>
            </ul>
        </div>
        
        <div class="detail-section">
            <h2>⚠️ DISCLAIMER</h2>
            <p><strong>This analysis is for educational purposes only and does not constitute financial advice.</strong></p>
            <ul>
                <li>Cryptocurrency trading involves significant risk of loss</li>
                <li>Past performance does not guarantee future results</li>
                <li>Always conduct your own research (DYOR)</li>
                <li>Only invest what you can afford to lose</li>
                <li>Consider consulting with a financial advisor</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Generated by Crypto Prediction Suite v1.0</p>
            <p>Next analysis recommended in 15-30 minutes</p>
        </div>
    </div>
</body>
</html>
            """
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_file
    
    def generate_full_report(self):
        """Tạo báo cáo đầy đủ"""
        print("📊 Generating comprehensive report...")
        
        # Run analysis
        results = self.app.run_enhanced_analysis()
        
        if not results:
            print("❌ No results to generate report")
            return
        
        # Generate HTML report
        html_file = self.create_detailed_html_report(results)
        
        # Generate charts for each pair
        print("\n📈 Generating price charts...")
        for result in results:
            try:
                symbol = result['symbol']
                df = self.app.get_kline_data(symbol, '15m', 100)
                if df is not None:
                    df = self.app.calculate_advanced_indicators(df)
                    if df is not None:
                        chart_path = os.path.join(self.report_dir, f'{symbol}_chart_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
                        self.generate_price_chart(symbol, df, result['signals'], chart_path)
                        print(f"✅ Chart saved: {chart_path}")
            except Exception as e:
                print(f"❌ Error generating chart for {symbol}: {e}")
        
        print(f"\n✅ Report generated successfully!")
        print(f"📁 HTML Report: {html_file}")
        print(f"📁 Charts saved in: {self.report_dir}/")
        
        # Try to open the HTML report
        try:
            import webbrowser
            webbrowser.open(f'file://{os.path.abspath(html_file)}')
            print(f"🌐 Report opened in browser")
        except:
            print(f"💡 Open the HTML file manually: {html_file}")

def main():
    generator = ReportGenerator()
    generator.generate_full_report()

if __name__ == "__main__":
    main()
