import os
import openai
import logging
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, AudioMessage, TextSendMessage
from tenacity import retry, stop_after_attempt, wait_exponential
import requests
from pydub import AudioSegment
import tempfile


# initialize flask
app = Flask(__name__)


# logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")
line_channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_channel_secret = os.getenv("LINE_CHANNEL_SECRET")


line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)


# OpenAI API retry
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_openai_api(question):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "你是一個專業的藥師，請依據資料庫內容回答"},
            {"role": "user", "content": question }
        ],
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()




# LINE Webhook 
@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        logger.error("Missing X-Line-Signature header")
        abort(400, description="Missing X-Line-Signature header")
   
    body = request.get_data(as_text=True)
    logger.info(f"Request body: {body}")
   
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        logger.error(f"Invalid signature: {e}")
        abort(400)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        abort(500)
   
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_message = event.message.text
    logger.info(f"Received text message: {user_message}")
   
    if "藥物查詢" in user_message:
        reply = "請提供藥品名稱，我會幫助您查找相關信息。"
    elif "使用方式" in user_message:
        reply = "藥物使用方式可以參考您的醫師指導，請說明藥品名稱以進一步查詢。"
    else:
        reply = call_openai_api(user_message + " 該服用什麼藥物")
   
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    logger.info("Received audio message")
    message_id = event.message.id
    audio_content = line_bot_api.get_message_content(message_id)
   
    # store 
    with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp_file:
        tmp_file.write(audio_content.content)
        m4a_path = tmp_file.name
   
    # comvert m4a to wav
    wav_path = m4a_path.replace(".m4a", ".wav")
    audio = AudioSegment.from_file(m4a_path, format="m4a")
    audio.export(wav_path, format="wav")
   
    # call LLM API
    recognized_text = recognize_taigi_audio(wav_path)
    logger.info(f"Recognized text from audio: {recognized_text}")
   
    # use OpenAI API to modify text
    try:
        reply = call_openai_api(recognized_text + " 該服用什麼藥物")
    except Exception as e:
        logger.error(f"AI response error: {str(e)}")
        reply = f"抱歉，AI 暫時無法回應，請稍後再試。錯誤：{str(e)}"
   
    # reply to LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


@app.before_first_request
def verify_credentials():
    if not openai.api_key:
        logger.error("OPENAI_API_KEY not set")
    if not line_channel_access_token:
        logger.error("LINE_CHANNEL_ACCESS_TOKEN not set")
    if not line_channel_secret:
        logger.error("LINE_CHANNEL_SECRET not set")


# main function
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
