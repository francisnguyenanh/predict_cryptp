#!/bin/zsh
# Script để chạy auto_runner.py và hiển thị kết quả phân tích đa khung thời gian
cd "$(dirname "$0")"
source .venv/bin/activate
python3 auto_runner.py
read -n 1 -s -r -p "\nNhấn phím bất kỳ để thoát..."
