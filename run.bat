@echo off
REM Tắt TensorFlow messages
set TF_CPP_MIN_LOG_LEVEL=3
set TF_ENABLE_ONEDNN_OPTS=0

REM Chạy ứng dụng
python auto_runner.py

pause
