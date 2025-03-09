import os
import logging
import datetime
import pytz
import random
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# .env 파일 로드
load_dotenv()

# 환경 변수에서 API 키 가져오기
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

# OpenAI 클라이언트 초기화
ai_client = OpenAI(api_key=OPENAI_API_KEY)

# 한국 시간대 설정
KST = pytz.timezone("Asia/Seoul")

# 로그 디렉터리 설정 (CS & 최신 IT 주제 포함)
LOG_DIR = "tech_logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 로깅 설정
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def generate_tech_content():
    cs_topics = [
        # 전통적인 CS 개념
        "Operating Systems and Process Management",
        "Data Structures and Algorithm Design",
        "Computer Networks and Protocols",
        "Databases and SQL Optimization",
        "Software Engineering Principles",
        "Compiler Design and Programming Languages",
        "Cybersecurity Fundamentals",
        "Cloud Computing and Distributed Systems",

        # 최신 IT 트렌드
        "Artificial Intelligence and Deep Learning",
        "Machine Learning and Data Science",
        "Blockchain and Decentralized Finance (DeFi)",
        "Quantum Computing and Cryptography",
        "Big Data Analytics and Data Engineering",
        "IoT (Internet of Things) and Edge Computing",
        "Augmented Reality (AR) and Virtual Reality (VR)"
    ]

    # 랜덤으로 대주제 선택
    selected_topic = random.choice(cs_topics)

    # 프롬프트에서 세부 주제도 자동 선택하도록 요청
    prompt = (
        f"You are an expert in Computer Science. Select a key subtopic related to the following major topic: {selected_topic}. "
        f"Provide a structured explanation focusing on both the major topic and the selected subtopic. "
        f"The explanation should include the following sections:\n\n"
        f"1. **Introduction** - Briefly introduce {selected_topic} and its significance.\n"
        f"2. **Core Concepts** - Explain the fundamental principles and key areas of {selected_topic}.\n"
        f"3. **Key Subtopic** - Automatically select and analyze a crucial subtopic related to {selected_topic}. "
        f"Explain its importance, challenges, and how it fits into the broader field.\n"
        f"4. **Real-World Applications** - Discuss where {selected_topic} and the selected subtopic are applied in industry or technology.\n\n"
        f"Keep the explanation clear and concise, making it accessible for those with a basic understanding of Computer Science."
    )

    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        tech_content = response.choices[0].message.content.strip()

        # 오늘 날짜 기반 파일 저장
        today_date = datetime.datetime.now(KST).strftime("%Y-%m-%d")
        file_path = os.path.join(LOG_DIR, f"{today_date}_tech_content.txt")

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(tech_content)

        logging.info(f"Tech content saved to {file_path}.")
        return f"📘 [Topic: {selected_topic}]\n\n{tech_content}"

    except Exception as e:
        logging.error(f"OpenAI API 호출 중 오류 발생: {e}")
        return "⚠️ An error occurred while generating the technology content."

# /start 명령어 처리
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Use the /tech command to get a detailed explanation on a trending technology topic.")

# /tech 명령어로 기술 콘텐츠 제공
async def tech_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Generating an in-depth tech explanation, please wait...")
    tech_content = generate_tech_content()
    await update.message.reply_text(f"📚 Today's Tech Topic:\n\n{tech_content}")

# 매일 자동으로 기술 콘텐츠 전송
async def daily_tech_update(context: ContextTypes.DEFAULT_TYPE):
    tech_content = generate_tech_content()
    message = f"📚 Today's Tech Topic:\n\n{tech_content}"
    await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# JobQueue 설정
async def setup_job_queue(application):
    job_queue = application.job_queue
    kst_time = datetime.time(hour=9, minute=0, second=0, tzinfo=KST)
    job_queue.run_daily(daily_tech_update, time=kst_time)

# 메인 함수
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(setup_job_queue).build()

    # 명령어 핸들러 등록
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("tech", tech_command))

    # 봇 실행
    app.run_polling()

if __name__ == '__main__':
    main()
