import os
import logging
import datetime
import pytz
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# .env 파일 로드
load_dotenv()

# 환경 변수에서 API 키 가져오기
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_ID = os.getenv("CHAT_ID")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)

# 한국 시간대 설정
KST = pytz.timezone("Asia/Seoul")

# 로그 디렉터리 설정
LOG_DIR = "word_logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 로깅 설정
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# GPT API를 통해 단어 목록 생성 및 로그 저장
def generate_word_list():
    prompt = (
        "Generate a list of 50 English words suitable for university undergraduate and conversation level with their Korean translations. "
        "Output should be in the format 'English word - Korean meaning' with one word per line. "
        "No additional explanation, just the word list."
    )    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        word_list = response.choices[0].message.content.strip()

        # 오늘 날짜 기반 파일 경로 설정
        today = datetime.datetime.now(KST).strftime("%Y-%m-%d")
        file_path = os.path.join(LOG_DIR, f"{today}_words.txt")

        # 단어 목록 로그 파일에 저장
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(word_list)

        logging.info(f"단어 목록이 {file_path}에 성공적으로 저장되었습니다.")
        return word_list

    except Exception as e:
        logging.error(f"OpenAI API 호출 중 오류 발생: {e}")
        return "⚠️ 단어 목록을 생성하는 동안 오류가 발생했습니다."

# 이전 단어 병합
def get_previous_words():
    files = sorted(f for f in os.listdir(LOG_DIR) if f.endswith("_words.txt"))
    merged_text = []

    for file in files:
        file_path = os.path.join(LOG_DIR, file)
        with open(file_path, "r", encoding="utf-8") as f:
            date = file.split("_")[0]
            merged_text.append(f"\n📅 {date} 단어 목록:\n" + f.read())

    return "\n".join(merged_text) if merged_text else "이전 단어 목록이 없습니다."

# /start 명령어 처리
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("안녕하세요! /words 명령어를 사용해 단어 리스트를 받을 수 있습니다.")

# /words 명령어로 단어 목록 제공
async def words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("GPT API를 통해 단어 목록을 생성 중입니다. 잠시만 기다려주세요.")
    word_list = generate_word_list()
    previous_words = get_previous_words()

    await update.message.reply_text(f"📚 오늘의 단어 목록:\n\n{word_list} \n\n 이전 단어 목록:\n{previous_words}")

# 매일 단어 자동 전송
async def daily_word(context: ContextTypes.DEFAULT_TYPE):
    word_list = generate_word_list()
    previous_words = get_previous_words()

    message = f"📚 오늘의 단어 목록:\n\n{word_list}\n\n📖 이전 단어 목록:\n{previous_words}"
    await context.bot.send_message(chat_id=CHAT_ID, text=message)

# JobQueue 설정
async def post_init(application):
    job_queue = application.job_queue
    kst_time = datetime.time(hour=9, minute=0, second=0, tzinfo=KST)
    job_queue.run_daily(daily_word, time=kst_time)

# 메인 함수
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    # 명령어 핸들러 등록
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("words", words))

    # 봇 실행
    app.run_polling()

if __name__ == '__main__':
    main()
