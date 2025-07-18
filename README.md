# LINE 藥師智慧問答機器人 (AI Pharmacist LINE Bot)

這是一個基於 Flask、LINE Messaging API 和 OpenAI GPT-4 的智慧問答 LINE 機器人。此專案將機器人設定為一名專業藥師，能夠接收並回覆使用者的文字和語音訊息，提供藥物相關的諮詢。

## ✨ 功能特色

* **智慧問答**：整合 OpenAI GPT-4 模型，以專業藥師的角色回答使用者關於藥物、症狀等問題。
* **多媒體訊息處理**：
    * **文字訊息**：可處理關鍵字（如 "藥物查詢", "使用方式"）以提供預設回覆，或將一般問題發送至 OpenAI 進行分析。
    * **語音訊息**：支援接收 LINE 的 M4A 格式語音訊息，自動轉換為 WAV 格式，並進行語音辨識（需自行實現辨識模型）。
* **穩健的 API 請求**：使用 `tenacity` 套件實作 API 請求重試機制，提昇與 OpenAI API 互動的成功率。
* **環境變數管理**：透過 `.env` 檔案管理 API 金鑰與敏感資訊，確保程式碼的安全性與可攜性。
* **完整的伺服器架構**：使用 Flask 框架搭建 Webhook 伺服器，並包含日誌紀錄 (Logging) 功能，方便開發與除錯。

## ⚙️ 系統架構

整個服務的運作流程如下：

1.  **使用者**：在 LINE App 中向機器人傳送文字或語音訊息。
2.  **LINE Platform**：接收到訊息後，透過 Webhook 將訊息內容轉發到我們的 Flask 應用程式。
3.  **Flask Application (`/callback`)**：
    * 驗證收到的請求是否來自 LINE。
    * **文字訊息**：判斷訊息內容，若為一般問題，則加上「該服用什麼藥物」的後綴，發送給 OpenAI API。
    * **語音訊息**：
        * 下載 M4A 音檔。
        * 使用 `pydub` 和 `FFmpeg` 將 M4A 轉檔為 WAV。
        * 呼叫 `recognize_taigi_audio` 函式進行語音轉文字（**注意：此函式需由開發者自行實現**）。
        * 將辨識後的文字發送給 OpenAI API。
4.  **OpenAI API**：接收到問題後，以 `gpt-4` 模型生成回覆。
5.  **Flask Application**：接收到 OpenAI 的回覆後，打包成 LINE 的訊息格式。
6.  **LINE Platform**：透過 `Reply Message API` 將最終的回覆傳送給使用者。

## 🛠️ 安裝與設定

### 前置需求

在開始之前，請確保您的開發環境已安裝以下軟體：

* Python 3.8+
* [FFmpeg](https://ffmpeg.org/download.html)：一個處理多媒體檔案的開源工具。`pydub` 套件需要它來進行音檔轉檔。請確保已將其安裝並設定在系統的 PATH 環境變數中。
* LINE Developers 帳號
* OpenAI API 金鑰

### 安裝步驟

1.  **Clone 專案**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2.  **安裝 Python 依賴套件**
    此專案的依賴套件都記錄在 `requirements.txt` 中。
    ```bash
    pip install -r requirements.txt
    ```

3.  **設定環境變數**
    複製 `.env.sample` 檔案並重新命名為 `.env`。
    ```bash
    cp .env.sample .env
    ```
    接著，在 `.env` 檔案中填入您的金鑰與憑證：
    ```env
    # .env

    # OpenAI API Key
    OPENAI_API_KEY="sk-..."

    # LINE Bot Channel Credentials
    LINE_CHANNEL_ACCESS_TOKEN="your_line_channel_access_token"
    LINE_CHANNEL_SECRET="your_line_channel_secret"
    ```

4.  **🚨【重要】實現語音辨識函式**
    在 `app1.py` 中，`handle_audio_message` 函式呼叫了一個名為 `recognize_taigi_audio` 的函式，但該函式並未在程式碼中定義。您需要自行實現此功能，例如串接第三方的語音轉文字 (Speech-to-Text) API。

    **範例（偽代碼）：**
    ```python
    def recognize_taigi_audio(wav_path):
        # 這是一個範例，您需要替換成真實的 API 服務
        # 例如：使用 Google Speech-to-Text, Azure Speech, 或其他支援台語的服務
        # import your_speech_recognition_library as sr
        
        # with open(wav_path, 'rb') as audio_file:
        #     transcript = sr.recognize(audio_file, language="zh-TW-Taigi") # 假設的語言代碼
        # return transcript.text
        
        # 暫時返回一個假資料以供測試
        return "我頭殼疼，規身軀攏無力 (我頭痛，全身都沒力氣)"
    ```

## 🚀 執行與部署

1.  **在本機執行**
    直接執行 `app1.py` 即可啟動 Flask 伺服器。
    ```bash
    python app1.py
    ```
    伺服器預設會在 `http://0.0.0.0:8080` 上運行。

2.  **設定 Webhook**
    LINE 的 Webhook 需要一個公開的 HTTPS 網址。在開發階段，您可以使用 `ngrok` 這類的工具來建立一個安全的通道，將您本機的伺服器暴露在公網上。
    ```bash
    ngrok http 8080
    ```
    `ngrok` 會提供一個 `https://...ngrok.io` 格式的網址。

3.  **設定 LINE Developer Console**
    * 前往 [LINE Developers Console](https://developers.line.biz/)。
    * 選擇您的 Provider 及對應的 Channel。
    * 在 "Messaging API" 頁籤中，找到 "Webhook URL"，點擊 "Edit"。
    * 將 `ngrok` 提供的網址貼上，並在結尾加上 `/callback`，例如：`https://your-ngrok-id.ngrok.io/callback`。
    * 啟用 "Use webhook"。

現在，您可以開始在 LINE 上與您的藥師機器人互動了！

## 📦 依賴套件

本專案主要使用了以下 Python 套件：

* `flask>=2.0.0`：輕量級的 Web 框架，用於建立 Webhook 伺服器。
* `line-bot-sdk>=2.4.2`：LINE 官方提供的 Python SDK，用於處理 Messaging API。
* `openai>=1.0.0`：OpenAI 官方 SDK，用於與 GPT-4 模型互動。
* `python-dotenv>=0.19.0`：用於讀取 `.env` 檔案中的環境變數。
* `tenacity>=8.0.0`：一個通用的重試函式庫。
* `requests`：強大的 HTTP 請求函式庫。
* `pydub`：一個高階的音訊處理函式庫，用於音檔轉檔。
* `ffmpeg-python`：FFmpeg 的 Python 封裝。
