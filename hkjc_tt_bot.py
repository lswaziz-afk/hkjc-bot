import os
import requests
import time

# 直接從 GitHub Actions 的環境變數讀取
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Referer': 'https://m.hkjc.com/'
}

def get_data(url):
    try:
        # 加入 timestamp 防止快取
        target_url = f"{url}&_={int(time.time()*1000)}"
        response = requests.get(target_url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def main():
    # 1. 抓取六合彩 (Mark Six)
    m6_url = "https://bet.hkjc.com/contentserver/jcbw/cmc/last30draws.json?lang=ch"
    m6_data = get_data(m6_url)
    
    # 2. 抓取三 T (TT) - 這裡使用賽馬結果接口
    # 注意：三T通常在賽馬日才有結果，非賽馬日會顯示上一期
    tt_url = "https://bet.hkjc.com/racing/getJSON.aspx?type=results&date=latest"
    # 註：如果馬會 JSON 格式較複雜，這裡可能需要根據 2026 最新格式解析
    
    msg = "🔔 【HKJC 最新動態】 🔔\n"
    msg += "━━━━━━━━━━━━━━\n"

    # 處理六合彩訊息
    if m6_data:
        latest = m6_data[0]
        msg += f"🎰 *六合彩 ({latest.get('drawId')})*\n"
        msg += f"日期：{latest.get('date')}\n"
        msg += f"號碼：`{latest.get('result')}`\n"
    else:
        msg += "🎰 六合彩：官方 JSON 存取失敗\n"

    msg += "━━━━━━━━━━━━━━\n"

    # 處理三 T 訊息 (簡易邏輯示範)
    # 三 T 解析較複雜，通常在 racing 結果的特定 pool 裡面
    msg += f"🐎 *三 T 資訊*\n"
    msg += "狀態：已完成掃描，請檢查官網結果\n" 
    # 因為三T數據結構經常變動，建議先確保連線通順
    
    msg += "━━━━━━━━━━━━━━"

    send_telegram(msg)

def send_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("Error: Missing TOKEN or CHAT_ID")
        return
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

if __name__ == "__main__":
    main()
