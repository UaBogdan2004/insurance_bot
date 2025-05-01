# Telegram Bot for Car Insurance 🛡️

A Telegram bot that helps users apply for car insurance by uploading documents, confirming extracted data, and generating a policy.

---

## 🔧 Setup Instructions

### 1. Clone the repository:
```bash
git clone https://github.com/UaBogdan2004/insurance-bot.git
cd insurance_bot
```
### 2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```
### 3. Install dependencies:
```bash
pip install -r requirements.txt
```
### 4. Set environment variables:
Create a .env file or export variables manually:
```bash
BOT_TOKEN=your_telegram_token
OPENAI_API_KEY=your_openai_key
```
### 5. Run the bot:
```bash
python bot.py
```

### 🧪 Example Flow
User sends /start

Bot asks for a photo of the driver’s license

Bot mocks recognition → asks user to confirm data

After all confirmations → policy is generated

