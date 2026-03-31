import os
import requests
import time

# 這裡括號內的字串，必須跟 YAML 檔中 env: 下面的左邊名稱一模一樣
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# 調試用：如果真的抓不到，GitHub Log 會印出這句
if not TOKEN or not CHAT_ID:
    print("❌ 錯誤：GitHub 環境變數讀取失敗，請檢查 YAML 檔的 env 設定")

def get_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Referer': 'https://bet.hkjc.com/'
    }
    try:
        # 加個 timestamp 防止被馬會 Cache 舊數據
        res = requests.get(f"{url}&_={int(time.time())}", headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json()
        return None
    except:
        return None

def main():
    # 1. 抓取六合彩 (Mark Six)
    m6_url = "https://bet.hkjc.com/contentserver/jcbw/cmc/last30draws.json?lang=ch"
    m6_data = get_data(m6_url)
    
    # 2. 抓取賽馬派彩 (包含三 T)
    tt_url = "https://bet.hkjc.com/racing/getJSON.aspx?type=dividend&date=latest"
    tt_data = get_data(tt_url)

    msg = "🔔 【HKJC 賽果通知】 🔔\n"
    msg += "━━━━━━━━━━━━━━\n"

    # --- 處理六合彩 ---
    if m6_data and len(m6_data) > 0:
        d = m6_data[0]
        msg += f"🎰 *六合彩 ({d.get('drawId')})*\n"
        msg += f"📅 日期：{d.get('date')}\n"
        msg += f"🔢 號碼：`{d.get('result')}`\n"
    else:
        msg += "🎰 六合彩：暫時抓取失敗\n"

    msg += "━━━━━━━━━━━━━━\n"

    # --- 處理三 T (TT) ---
    if tt_data and 'out' in tt_data:
        tt_found = False
        for div in tt_data['out']:
            pool_name = div.get('pool', '')
            # 尋找三T相關的關鍵字
            if "Triple Trio" in pool_name or "三T" in pool_name:
                dividend = div.get('dividend', '0')
                msg += f"🐎 *三 T 派彩*\n💰 派彩：`${dividend}`\n"
                tt_found = True
                break
        if not tt_found:
            msg += "🐎 三 T：今日無三T或尚未派彩\n"
    else:
        msg += "🐎 三 T：暫無最新賽馬數據\n"

    msg += "━━━━━━━━━━━━━━"

    # 發送到 Telegram
    if TOKEN and CHAT_ID:
        send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(send_url, data=payload)
        print("✅ 訊息已發送")
    else:
        print("❌ 缺少 Token 或 Chat ID")

if __name__ == "__main__":
    main()
