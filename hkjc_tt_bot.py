import requests
import os
import re
from datetime import datetime

# 讀取 GitHub Secrets
BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_hkjc_tt_data():
    """爬取三T結果 (馬會資訊網)"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        today = datetime.now().strftime('%d/%m/%Y')
        # 檢查網頁是否有今日日期
        if today in r.text:
            # 提取三T組合同派彩
            res = re.findall(r'三T.*?<td>(.*?)</td>.*?<td>([\d,]+)</td>', r.text, re.S)
            if res:
                return f"🏇 *今日三T結果 ({today})*\n━━━━━━━━━━━━\n✅ 組合：{res[0][0].strip()}\n💰 派彩：HK$ {res[0][1].strip()}"
    except: return None

def get_mark_six_data():
    """爬取六合彩 (東網數據接口 + 暴力掃描)"""
    # 接口 A: 東網 App 專用 JSON (最準確)
    api_url = "https://on.cc/fe/m6/data/m6_data.json"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    
    try:
        # 1. 嘗試 JSON 接口
        r = requests.get(api_url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            draw_date = data.get('drawDate', '') # 2026/03/31
            today = datetime.now().strftime('%Y/%m/%d')
            if today in draw_date:
                nums = data.get('result', '').split(',')
                s_no = data.get('special', '')
                return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"

        # 2. 備援：暴力掃描東網新聞頁面 (不理會網頁結構)
        r_web = requests.get("https://hk.on.cc/hk/news/index.html", headers=headers, timeout=15)
        # 尋找類似 "9,18,19,20,28,32" 加上一個號碼的格式
        # Regex 說明: 搵 6 個數字中間有分隔符，最後跟住一個號碼
        match = re.search(r'(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2}).*?(\d{1,2})', r_web.text)
        if match:
            res = list(match.groups())
            # 簡單檢查，確保不是舊數據 (今日日期 31 號有出現喺附近)
            if datetime.now().strftime('%d') in r_web.text:
                return f"🔮 *今日六合彩開獎 (掃描版)*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(res[:6])}\n🔴 特別號：{res[6]}"
                
    except Exception as e:
        print(f"DEBUG: Error {e}")
    return None

def send_to_telegram(text):
    if not text: return
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    try:
        requests.post(api_url, data=payload, timeout=15)
    except: pass

if __name__ == "__main__":
    print(f"--- 執行中 (香港時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    
    # 執行三T抓取
    tt_msg = get_hkjc_tt_data()
    if tt_msg: send_to_telegram(tt_msg)
    
    # 執行六合彩抓取
    ms_msg = get_mark_six_data()
    if ms_msg: send_to_telegram(ms_msg)
    
    print("--- 執行完畢 ---")
