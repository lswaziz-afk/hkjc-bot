import requests
import os
import re
from datetime import datetime

# 讀取 GitHub Secrets
BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_hkjc_tt_data():
    """三T (馬會資訊網)"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        today = datetime.now().strftime('%d/%m/%Y')
        if today in r.text:
            res = re.findall(r'三T.*?<td>(.*?)</td>.*?<td>([\d,]+)</td>', r.text, re.S)
            if res:
                return f"賽馬 🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{res[0][0].strip()}\n💰 派彩：HK$ {res[0][1].strip()}"
    except: return None

def get_mark_six_data():
    """六合彩 (精準校對版)"""
    # 優先使用東網 JSON 數據
    api_url = "https://on.cc/fe/m6/data/m6_data.json"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    
    try:
        r = requests.get(api_url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            # 必須檢查日期係咪今日 (2026/03/31)
            draw_date = data.get('drawDate', '')
            today = datetime.now().strftime('%Y/%m/%d')
            
            if today in draw_date:
                nums = data.get('result', '').split(',')
                s_no = data.get('special', '')
                if len(nums) >= 6:
                    return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums[:6])}\n🔴 特別號：{s_no}"

        # 如果 JSON 唔 match 今日日期，去明報專頁搵「圖片標籤」 (最準確)
        r_mp = requests.get("https://news.mingpao.com/pns/%E5%85%AD%E5%90%88%E5%BD%A9/marksix", headers=headers, timeout=15)
        r_mp.encoding = 'utf-8'
        
        # 只搵 <img> 標籤入面嘅 alt 屬性，呢個係明報放號碼嘅地方
        # 截圖見到號碼係 9, 18, 19, 20, 28, 32 + 44
        img_balls = re.findall(r'<img [^>]*alt="(\d{1,2})"', r_mp.text)
        
        # 過濾 1-49 並去重
        balls = []
        for b in img_balls:
            if 1 <= int(b) <= 49 and b not in balls:
                balls.append(b)
        
        # 明報通常會列出幾期，我哋攞第一組 7 個
        if len(balls) >= 7:
            # 再次確保今日日期喺頁面出現過
            today_dash = datetime.now().strftime('%Y-%m-%d')
            if today_dash in r_mp.text:
                return f"🔮 *今日六合彩開獎 (明報)*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(balls[:6])}\n🔴 特別號：{balls[6]}"
            
        print("DEBUG: 未偵測到今日日期或有效號碼。")
        return None
    except Exception as e:
        print(f"DEBUG: Error {e}")
        return None

def send_to_telegram(text):
    if not text: return
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'})

if __name__ == "__main__":
    tt = get_hkjc_tt_data()
    if tt: send_to_telegram(tt)
    ms = get_mark_six_data()
    if ms: send_to_telegram(ms)
