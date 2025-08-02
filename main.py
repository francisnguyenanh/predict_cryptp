#!/usr/bin/env python3
"""
Main runner cho Crypto Prediction App
Hỗ trợ nhiều chế độ chạy khác nhau
"""

import sys
import argparse
from datetime import datetime
import json
import os

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  Config file not found, using default settings")
        return {}
    except json.JSONDecodeError:
        print("❌ Error reading config file, using default settings")
        return {}

def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                          🚀 CRYPTO PREDICTION SUITE                         ║
    ║                     Advanced Technical Analysis Platform                     ║
    ║                                                                              ║
    ║  📊 Multi-timeframe Analysis    🎯 Advanced Signal Scoring                  ║
    ║  📈 Risk/Reward Optimization    🤖 Automated Trading Signals                ║
    ║  📱 Real-time Dashboard         💰 JPY Pairs Specialist                     ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def run_basic_analysis():
    """Run basic analysis"""
    print("🔍 Running Basic Analysis...")
    from app import CryptoPredictionApp
    app = CryptoPredictionApp()
    return app.run_analysis()

def run_enhanced_analysis():
    """Run enhanced analysis with better visualization"""
    print("🚀 Running Enhanced Analysis V2...")
    from enhanced_app_v2 import EnhancedCryptoPredictionAppV2
    app = EnhancedCryptoPredictionAppV2()
    return app.run_enhanced_analysis()

def run_auto_mode(interval=15):
    """Run in automatic mode"""
    print(f"🤖 Starting Auto Mode (Every {interval} minutes)...")
    from auto_runner import AutoRunner
    runner = AutoRunner(interval_minutes=interval)
    runner.start_auto_mode()

def show_help():
    """Show detailed help"""
    help_text = """
🚀 CRYPTO PREDICTION APP - USAGE GUIDE

BASIC COMMANDS:
  python main.py                    # Run basic analysis once
  python main.py --enhanced         # Run enhanced analysis with better UI
  python main.py --auto             # Run auto mode (every 15 minutes)
  python main.py --auto --interval 30  # Run auto mode (custom interval)

ANALYSIS MODES:
  --basic          Basic technical analysis
  --enhanced       Advanced analysis with beautiful dashboard
  --compare        Compare all analysis methods

AUTOMATION:
  --auto           Start automatic monitoring
  --interval N     Set custom interval (minutes)
  --once           Run analysis only once

CONFIGURATION:
  --config FILE    Use custom config file
  --pairs A,B,C    Override trading pairs
  --timeframe TF   Set primary timeframe (15m, 1h, 4h)

EXAMPLES:
  python main.py --enhanced
  python main.py --auto --interval 30
  python main.py --pairs XRPJPY,ADAJPY --enhanced
  python main.py --compare

SUPPORTED PAIRS:
  - XRP/JPY (Ripple)
  - XLM/JPY (Stellar Lumens)  
  - ADA/JPY (Cardano)
  - SUI/JPY (Sui Network)

TECHNICAL INDICATORS:
  📊 Trend: EMA 10/20/50, Price Alignment
  📈 Momentum: RSI, MACD, Stochastic
  📊 Volatility: Bollinger Bands, ATR, Keltner Channels
  📊 Volume: OBV, Volume Ratio, A/D Line
  📊 Patterns: Hammer, Engulfing, Support/Resistance

RISK MANAGEMENT:
  🎯 Take Profit: 1.5x & 2.5x ATR
  🛑 Stop Loss: 1.0x ATR
  📊 Risk/Reward: Minimum 1:1 ratio
  📈 Position Sizing: Based on volatility

OUTPUT EXPLANATION:
  📊 Signal: BUY/SELL recommendation
  🎯 Probability: Success rate prediction (0-95%)
  ⭐ Quality: HIGH (>75%), MEDIUM (60-75%), LOW (<60%)
  📈 R/R Ratio: Risk/Reward ratio
  📊 Trends: Multi-timeframe trend analysis

For more information, visit: https://github.com/yourusername/crypto-prediction
    """
    print(help_text)

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description='Crypto Prediction App')
    parser.add_argument('--basic', action='store_true', help='Run basic analysis')
    parser.add_argument('--enhanced', action='store_true', help='Run enhanced analysis')
    parser.add_argument('--auto', action='store_true', help='Run in auto mode')
    parser.add_argument('--interval', type=int, default=15, help='Auto mode interval (minutes)')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--config', type=str, help='Custom config file')
    parser.add_argument('--pairs', type=str, help='Trading pairs (comma separated)')
    parser.add_argument('--timeframe', type=str, help='Primary timeframe')
    parser.add_argument('--compare', action='store_true', help='Compare analysis methods')
    parser.add_argument('--help-detailed', action='store_true', help='Show detailed help')
    
    # If no arguments provided, run enhanced analysis by default
    if len(sys.argv) == 1:
        run_enhanced_analysis()
        return
    
    args = parser.parse_args()
    
    if args.help_detailed:
        show_help()
        return
    
    # Load configuration
    config = load_config()
    
    try:
        if args.compare:
            print("📊 COMPARISON MODE")
            print("=" * 50)
            print("\n1️⃣  BASIC ANALYSIS:")
            run_basic_analysis()
            print("\n" + "="*80 + "\n")
            print("2️⃣  ENHANCED ANALYSIS:")
            run_enhanced_analysis()
            
        elif args.auto:
            run_auto_mode(args.interval)
            
        elif args.enhanced:
            run_enhanced_analysis()
            
        elif args.basic:
            run_basic_analysis()
            
        elif args.once:
            print("🔍 Single Analysis Run")
            run_enhanced_analysis()
            
        else:
            # Default to enhanced analysis
            run_enhanced_analysis()
            
    except KeyboardInterrupt:
        print(f"\n🛑 Application stopped by user at {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        print("💡 Try running with --basic flag or check your configuration")

if __name__ == "__main__":
    main()
