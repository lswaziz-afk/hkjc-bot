import os
import requests
import time
from dotenv import load_dotenv

# 載入 .env 檔案中的變數
load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# 2026 年建議使用的動態 URL (有時馬會會檢查 timestamp)
LOTTERY_URL = f"https://bet.hkjc.com/contentserver/jcbw/cmc/last30draws.json?t={int(time.time())}"

def get_latest_result():
    # 更加完整的 Headers，模擬真正的 Chrome 瀏覽器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-HK,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://bet.hkjc.com/marksix/index.aspx?lang=ch',
        'Connection': 'keep-alive',
    }
    
    try:
        session = requests.Session() # 使用 Session 維持連線狀態
        response = session.get(LOTTERY_URL, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            latest = data[0]
            
            # 格式化訊息
            msg = (
                f"🏮 *六合彩最新結果* 🏮\n"
                f"━━━━━━━━━━━━━━\n"
                f"📅 攪珠日期：{latest.get('date')}\n"
                f"🔢 攪珠期數：{latest.get('drawId')}\n"
                f"🔮 中獎號碼：`{latest.get('result').replace(',', ' , ')}` \n"
                f"━━━━━━━━━━━━━━"
            )
            return msg
        else:
            return f"❌ 存取失敗：馬會伺服器回傳狀態碼 {response.status_code}\n(可能需要檢查 IP 或代理設定)"

    except Exception as e:
        return f"⚠️ 程式出錯：{str(e)}"

def send_to_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("錯誤：找不到 Token 或 Chat ID，請檢查 .env 檔案")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            print("✅ 訊息已成功發送至 Telegram")
        else:
            print(f"❌ Telegram 發送失敗：{r.text}")
    except Exception as e:
        print(f"❌ 連線至 Telegram 失敗：{e}")

if __name__ == "__main__":
    result = get_latest_result()
    send_to_telegram(result)
