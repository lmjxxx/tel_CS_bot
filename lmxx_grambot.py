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

# 텔레그램 메시지 길이 제한
TELEGRAM_MESSAGE_LIMIT = 4096

CS_TOPICS = (
    "Operating Systems and Process Management",
    "Data Structures",
    "Algorithm Design",
    "Computer Networks and Protocols",
    "Databases and SQL Optimization",
    "Software Engineering Principles",
    "Compiler Design and Programming Languages",
    "Cybersecurity Fundamentals",
    "Cloud Computing and Distributed Systems",
    "Artificial Intelligence",
    "Deep Learning",
    "Machine Learning",
    "Data Science",
    "Blockchain",
    "Decentralized Finance (DeFi)",
    "Quantum Computing",
    "Cryptography",
    "Big Data Analytics and Data Engineering",
    "IoT (Internet of Things)",
    "Edge Computing",
    "Augmented Reality (AR)",
    "Virtual Reality (VR)"
)

def split_message(text, limit=TELEGRAM_MESSAGE_LIMIT):
    """ 메시지를 Telegram 최대 길이 (4096자) 이하로 분할 """
    messages = []
    while len(text) > limit:
        split_index = text.rfind("\n", 0, limit)  # 최대 길이를 초과하지 않도록 줄바꿈 단위로 자름
        if split_index == -1:  # 줄바꿈 없으면 강제 자름
            split_index = limit
        messages.append(text[:split_index])
        text = text[split_index:].strip()
    messages.append(text)
    return messages

def generate_tech_content():
    selected_topic = random.choice(CS_TOPICS)

    prompt = (
        f"You are an expert in Computer Science. Choose a **key subtopic** related to the following major topic: {selected_topic}. "
        f"Ensure the subtopic is **highly relevant and commonly discussed** within this field.\n\n"
        f"Provide a structured explanation including the following sections:\n\n"
        
        f"1. **Introduction** - Briefly introduce {selected_topic} and its significance.\n"
        f"2. **Core Concepts** - Explain the fundamental principles and key areas of {selected_topic}.\n"
        f"3. **Key Subtopic** - Select and analyze a crucial subtopic within {selected_topic}. Provide a detailed explanation covering:\n"
        f"   - **Definition**: What it is and why it matters.\n"
        f"   - **Mechanism**: How it works, including key components and workflow.\n"
        f"   - **Challenges & Limitations**: Potential issues and drawbacks.\n"
        f"   - **Comparison**: If applicable, compare it with alternative approaches.\n"
        f"   - **Future Trends**: How this subtopic is evolving in modern computing.\n\n"
        
        f"4. **Real-World Applications** - List major fields where {selected_topic} and the selected subtopic are applied, with a one-line explanation for each:\n"
        f"   - **Industry/Technology 1**: [One-sentence explanation]\n"
        f"   - **Industry/Technology 2**: [One-sentence explanation]\n"
        f"   - **Industry/Technology 3**: [One-sentence explanation]\n\n"
        
        f"Ensure the explanation is clear, well-structured, and suitable for those with a basic understanding of Computer Science."
    )


    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500  # 최대 토큰을 줄여서 너무 긴 응답 방지
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
    topics_message = "**📌 Available CS & Tech Topics:**\n\n" + "\n".join(f"- {topic}" for topic in CS_TOPICS)
    
    welcome_message = (
        "👋 Welcome! Use the /tech command to get a detailed explanation on a trending technology topic.\n\n"
        "🔹 Here are the topics you can explore:\n\n"
        f"{topics_message}\n\n"
        "📝 A subtopic within these fields will be automatically selected for a detailed explanation."
    )

    await update.message.reply_text(welcome_message, parse_mode="Markdown")


# /tech 명령어로 기술 콘텐츠 제공 (메시지 길이 제한 적용)
async def tech_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Generating an in-depth tech explanation, please wait...")
    tech_content = generate_tech_content()

    messages = split_message(tech_content)
    for msg in messages:
        await update.message.reply_text(msg)  # 길이 제한을 준수하며 분할된 메시지 전송

# 매일 자동으로 기술 콘텐츠 전송 (메시지 길이 제한 적용)
async def daily_tech_update(context: ContextTypes.DEFAULT_TYPE):
    tech_content = generate_tech_content()
    messages = split_message(tech_content)

    for msg in messages:
        await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

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
