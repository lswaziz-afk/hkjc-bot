import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

# 讀取 GitHub Secrets
BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_hkjc_tt_data():
    """爬取三T (馬會資訊網)"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        today_str = datetime.now().strftime('%d/%m/%Y')
        
        date_tag = soup.find(lambda tag: tag.name == "span" and "賽事日期" in tag.text)
        if date_tag and today_str in date_tag.get_text():
            all_tds = soup.find_all('td')
            for i, td in enumerate(all_tds):
                if "三T" == td.get_text(strip=True):
                    nums = all_tds[i+1].get_text(strip=True).replace(' ', '')
                    div = all_tds[i+2].get_text(strip=True)
                    if div == "-": return "⏳ 三T派彩計算中..."
                    return f"🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{nums}\n💰 派彩：HK$ {div}"
        return None
    except: return None

def get_mark_six_data():
    """爬取六合彩 (東網首頁暴力掃描版 - 唔理日期直接搵波)"""
    # 呢個係東網最核心、最唔會死嘅網址
    url = "https://hk.on.cc/hk/news/index.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. 搵所有 1-49 嘅數字
        # 我哋唔再 check 日期，費事因為 2026/03/31 vs 31/03/2026 卡死
        potential_balls = []
        # 搵所有 <span>, <b>, <div> 入面嘅純數字
        for tag in soup.find_all(['span', 'b', 'div']):
            txt = tag.get_text(strip=True)
            if txt.isdigit() and 1 <= int(txt) <= 49 and len(txt) <= 2:
                potential_balls.append(txt)
        
        # 2. 過濾號碼
        # 東網首頁右邊嗰個「六合彩」box，號碼通常係連續出現嘅
        # 我哋攞最後出現嗰 7 個數字 (通常最新結果喺最底或右邊資訊欄)
        if len(potential_balls) >= 7:
            # 攞最後 7 個波
            res_balls = potential_balls[-7:]
            
            # 檢查係咪真係號碼 (簡單去重，六合彩唔會重複)
            if len(set(res_balls)) == 7:
                nums = res_balls[:6]
                s_no = res_balls[6]
                return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"
        
        print("DEBUG: 喺東網首頁搵唔到足夠嘅號碼球。")
        return None
    except Exception as e:
        print(f"六合彩出錯: {e}")
        return None

def send_to_telegram(text):
    if not text: return
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    requests.post(api_url, data=payload, timeout=15)

if __name__ == "__main__":
    print(f"--- 執行中 (香港: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    
    # 三T
    tt = get_hkjc_tt_data()
    if tt: send_to_telegram(tt)
    
    # 六合彩
    ms = get_mark_six_data()
    if ms: send_to_telegram(ms)
    
    print("--- 執行完畢 ---")
