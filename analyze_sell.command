#!/bin/zsh
# Script để chạy menu phân tích bán nhanh
cd "$(dirname "$0")"
source .venv/bin/activate

echo "🔍 PHÂN TÍCH XU HƯỚNG COIN - QUYẾT ĐỊNH HOLD HAY BÁN"
echo "=================================================="
echo "Danh sách coin có sẵn:"
echo "1. XRPJPY    2. XLMJPY    3. ADAJPY    4. SUIJPY"
echo "5. LINKJPY   6. SOLJPY    7. ETHJPY"
echo ""
read -p "👉 Nhập số thứ tự coin muốn phân tích (1-7): " choice

case $choice in
    1) symbol="XRPJPY" ;;
    2) symbol="XLMJPY" ;;
    3) symbol="ADAJPY" ;;
    4) symbol="SUIJPY" ;;
    5) symbol="LINKJPY" ;;
    6) symbol="SOLJPY" ;;
    7) symbol="ETHJPY" ;;
    *) echo "❌ Lựa chọn không hợp lệ!"; exit 1 ;;
esac

echo ""
echo "🔄 Đang phân tích $symbol..."
python3 -c "
from auto_runner import AutoRunner, analyze_sell_trend
runner = AutoRunner()
analyze_sell_trend(runner, '$symbol')
"

echo ""
read -n 1 -s -r -p "📌 Nhấn phím bất kỳ để thoát..."
