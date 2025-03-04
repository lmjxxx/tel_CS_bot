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

# 로그 디렉터리 설정 (기존 'word_logs' → 'story_logs'로 변경)
LOG_DIR = "story_logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 로깅 설정
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

import random
def generate_story():
    themes = [
        "adventure", "mystery", "fantasy", "science fiction", "historical fiction", 
        "romance", "thriller", "slice of life", "supernatural", "coming-of-age"
    ]
    chosen_theme = random.choice(themes)

    # 확실한 결말 or 열린 결말을 랜덤 적용
    ending_type = random.choice(["closed ending", "open-ended story"])

    prompt = (
        f"You are a creative storyteller. Write a short narrative story in English that feels like a small storybook. "
        f"The story should be based on the following theme: {chosen_theme}. "
        f"The story must not be a TextbookReading or Journalistic Reading. "
        f"It should only contain the content of the story itself—no additional explanations, notes, or disclaimers. "
        f"Use imaginative elements, descriptive language, and leave a bit of mystery or room for speculation. "
        f"Ensure the story has a clear structure: Introduction, Conflict, Climax, and Resolution. "
        f"The story must conclude with a {ending_type}."
        f" If it's a closed ending, all conflicts should be resolved neatly. "
        f"If it's an open-ended story, leave an element of ambiguity or mystery, making the reader think about what happens next."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=600
        )
        story_content = response.choices[0].message.content.strip()

        # 오늘 날짜 기반 파일 저장
        today = datetime.datetime.now(KST).strftime("%Y-%m-%d")
        file_path = os.path.join(LOG_DIR, f"{today}_story.txt")

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(story_content)

        logging.info(f"이야기가 {file_path}에 성공적으로 저장되었습니다.")
        return f"📖 [Theme: {chosen_theme.capitalize()} | Ending: {ending_type.capitalize()}]\n\n{story_content}"

    except Exception as e:
        logging.error(f"OpenAI API 호출 중 오류 발생: {e}")
        return "⚠️ 이야기를 생성하는 동안 오류가 발생했습니다."

# /start 명령어 처리
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("안녕하세요! /story 명령어를 사용해 오늘의 이야기를 받을 수 있습니다.")

# /story 명령어로 이야기 제공
async def story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("GPT API를 통해 이야기를 생성 중입니다. 잠시만 기다려주세요.")
    story_content = generate_story()

    await update.message.reply_text(f"📚 오늘의 이야기:\n\n{story_content}")

# 매일 자동으로 이야기 전송
async def daily_story(context: ContextTypes.DEFAULT_TYPE):
    story_content = generate_story()

    message = f"📚 오늘의 이야기:\n\n{story_content}"
    await context.bot.send_message(chat_id=CHAT_ID, text=message)


# JobQueue 설정
async def post_init(application):
    job_queue = application.job_queue
    kst_time = datetime.time(hour=9, minute=0, second=0, tzinfo=KST)
    job_queue.run_daily(daily_story, time=kst_time)

# 메인 함수
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    # 명령어 핸들러 등록
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("story", story))

    # 봇 실행
    app.run_polling()

if __name__ == '__main__':
    main()
