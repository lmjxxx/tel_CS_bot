#!/bin/bash

VENV_DIR="./gramtelbot/venv"
LOG_DIR="./logs"
LOG_FILE="$LOG_DIR/bot_$(date +%y-%m-%d_%H-%M-%S).log"

mkdir -p $LOG_DIR

source "$VENV_DIR/bin/activate"

echo "Telegram Bot 실행 중 ... 로그 파일: $LOG_FILE"
nohup python3 lmxx_grambot.py > "$LOG_FILE" 2>&1 &

echo "Bot 실행 완료1 프로세스 ID: $!"

deactivate