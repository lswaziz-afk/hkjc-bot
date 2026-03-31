import requests
import time

# --- 設定區域 ---
# 填入你剛才測試成功的 Token 和 Chat ID
TELEGRAM_TOKEN = '你的_BOT_TOKEN'
CHAT_ID = '你的_CHAT_ID'

# 馬會六合彩 JSON 來源 (這是目前最通用的路徑)
LOTTERY_URL = "https://bet.hkjc.com/contentserver/jcbw/cmc/last30draws.json"

def get_latest_result():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://bet.hkjc.com/marksix/',
        'Accept': 'application/json, text/javascript, */*; q=0.01'
    }
    
    try:
        print(f"[{time.strftime('%H:%M:%S')}] 正在從馬會抓取最新結果...")
        response = requests.get(LOTTERY_URL, headers=headers, timeout=15)
        
        # 檢查是否成功存取
        if response.status_code != 200:
            return f"❌ 官方 JSON 存取失敗 (Status Code: {response.status_code})"
        
        data = response.json()
        
        # 取得最新一期 (index 0)
        latest = data[0]
        draw_id = latest.get('drawId', '未知期數')
        draw_date = latest.get('date', '')
        # 結果通常是用半角逗號分隔的字串
        results = latest.get('result', '').replace(',', ', ')
        
        message = (
            f"🏮 【最新六合彩結果】 🏮\n"
            f"--------------------------\n"
            f"攪珠期數：{draw_id}\n"
            f"攪珠日期：{draw_date}\n"
            f"中獎號碼：{results}\n"
            f"--------------------------\n"
            f"更新時間：{time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return message

    except Exception as e:
        return f"⚠️ 程式執行出錯: {str(e)}"

def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown" # 讓訊息看起來整齊點
    }
    
    try:
        res = requests.post(url, data=payload)
        if res.json().get('ok'):
            print("✅ Telegram 訊息已送出！")
        else:
            print(f"❌ 發送失敗: {res.json()}")
    except Exception as e:
        print(f"❌ Telegram 連線異常: {e}")

if __name__ == "__main__":
    # 執行流程
    result_text = get_latest_result()
    send_telegram_msg(result_text)
