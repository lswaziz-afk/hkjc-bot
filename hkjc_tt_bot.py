import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

# 讀取 GitHub Secrets
BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_hkjc_tt_data():
    """爬取三T (維持馬會資訊網，通常賽馬數據封鎖較鬆)"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        today = datetime.now().strftime('%d/%m/%Y')
        if today in r.text:
            soup = BeautifulSoup(r.text, 'html.parser')
            all_tds = soup.find_all('td')
            for i, td in enumerate(all_tds):
                if "三T" == td.get_text(strip=True):
                    nums = all_tds[i+1].get_text(strip=True).replace(' ', '')
                    div = all_tds[i+2].get_text(strip=True)
                    return f"🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{nums}\n💰 派彩：HK$ {div}"
    except: return None

def get_mark_six_data():
    """爬取六合彩 (明報專頁版 - 穩定且直接)"""
    url = "https://news.mingpao.com/pns/%E5%85%AD%E5%90%88%E5%BD%A9/marksix"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. 檢查日期 (明報格式通常係 2026年3月31日)
        today = datetime.now()
        date_str = today.strftime('%Y年%#m月%#d日').replace('年0', '年').replace('月0', '月') 
        # 註：#m喺Windows用，如果喺Linux (GitHub) 要用 %-m
        date_str_linux = today.strftime('%Y年%-m月%-d日')
        
        page_text = soup.get_text()
        print(f"DEBUG: 檢查明報日期: {date_str_linux}")
        
        # 2. 搵號碼
        # 明報嘅號碼通常放喺 class="list1" 或者 <ul> <li> 入面
        balls = []
        # 直接搵所有 digit
        all_items = soup.find_all(['li', 'span', 'td'])
        for item in all_items:
            txt = item.get_text(strip=True)
            if txt.isdigit() and 1 <= int(txt) <= 49 and len(txt) <= 2:
                balls.append(txt)
        
        # 明報通常會列出最近幾期，我哋攞最頂（最新）嗰 7 個
        # 先去重（保持順序）
        unique_balls = []
        for b in balls:
            if b not in unique_balls:
                unique_balls.append(b)
                if len(unique_balls) == 7: break

        if len(unique_balls) >= 7:
            # 驗證一下係咪真係今日嘅（保底機制：如果搵唔到日期字眼但有波，都Send咗先）
            nums = unique_balls[:6]
            s_no = unique_balls[6]
            return f"🔮 *今日六合彩開獎 (明報源)*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"
            
        print("DEBUG: 明報頁面搵唔到足夠號碼。")
        return None
    except Exception as e:
        print(f"明報爬蟲出錯: {e}")
        return None

def send_to_telegram(text):
    if not text: return
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    requests.post(api_url, data=payload, timeout=15)

if __name__ == "__main__":
    print(f"--- 執行中 (香港: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    
    # 執行檢查
    tt = get_hkjc_tt_data()
    if tt: send_to_telegram(tt)
    
    ms = get_mark_six_data()
    if ms: send_to_telegram(ms)
    
    print("--- 執行完畢 ---")
