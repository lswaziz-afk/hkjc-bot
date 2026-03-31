import requests
from bs4 import BeautifulSoup
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
    """爬取六合彩 (針對明報截圖結構優化)"""
    url = "https://news.mingpao.com/pns/%E5%85%AD%E5%90%88%E5%BD%A9/marksix"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://news.mingpao.com/'
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. 檢查日期 (2026-03-31)
        today_dash = datetime.now().strftime('%Y-%m-%d')
        if today_dash not in soup.get_text():
            print(f"DEBUG: 網頁尚未更新日期 {today_dash}")
            return None

        # 2. 抓取號碼
        # 明報的號碼球通常在 <ul> <li> 裡面，或者帶有 ball 字眼的 class
        balls = []
        
        # 策略 1: 找所有 <img> 的 alt (最常見)
        for img in soup.find_all('img', alt=True):
            alt_val = img['alt'].strip()
            if alt_val.isdigit() and 1 <= int(alt_val) <= 49:
                balls.append(alt_val)
        
        # 策略 2: 如果 A 失敗，找帶有數字的 span (明報手機版結構)
        if len(balls) < 7:
            for el in soup.find_all(['span', 'div', 'li'], text=re.compile(r'^\d{1,2}$')):
                val = el.get_text(strip=True)
                if 1 <= int(val) <= 49:
                    balls.append(val)

        # 3. 處理結果
        # 截圖中號碼是 9, 18, 19, 20, 28, 32 + 44
        # 排除掉截圖中可能的總和數字 (例如 170)
        unique_balls = []
        for b in balls:
            if b not in unique_balls:
                unique_balls.append(b)
            if len(unique_balls) == 7: break

        if len(unique_balls) >= 7:
            return f"🔮 *今日六合彩開獎 (明報源)*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(unique_balls[:6])}\n🔴 特別號：{unique_balls[6]}"
            
        print(f"DEBUG: 抓到的數字不足 7 個: {unique_balls}")
        return None
    except Exception as e:
        print(f"明報爬蟲出錯: {e}")
        return None

def send_to_telegram(text):
    if not text: return
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'})

if __name__ == "__main__":
    print(f"--- 執行中 (香港: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    # 三T
    tt = get_hkjc_tt_data()
    if tt: send_to_telegram(tt)
    # 六合彩
    ms = get_mark_six_data()
    if ms: send_to_telegram(ms)
    print("--- 執行完畢 ---")
