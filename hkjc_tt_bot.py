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
    """爬取六合彩 (明報專頁 - 深度掃描版)"""
    url = "https://news.mingpao.com/pns/%E5%85%AD%E5%90%88%E5%BD%A9/marksix"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://news.mingpao.com/'
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. 檢查日期 (截圖顯示 2026-03-31)
        today_dash = datetime.now().strftime('%Y-%m-%d')
        content = soup.get_text()
        print(f"DEBUG: 檢查網頁是否有日期 {today_dash}")
        
        # 2. 抓取號碼球
        balls = []
        
        # 策略 A: 尋找所有 <img> 標籤的 alt 屬性 (明報常把波號放在 alt)
        for img in soup.find_all('img', alt=True):
            alt_txt = img['alt']
            if alt_txt.isdigit() and 1 <= int(alt_txt) <= 49:
                balls.append(alt_txt)
        
        # 策略 B: 尋找特定 class 的 div (例如 class="ball_num")
        if len(balls) < 7:
            for div in soup.find_all(['div', 'span', 'li']):
                txt = div.get_text(strip=True)
                # 只拿 1-2 位的純數字
                if txt.isdigit() and 1 <= int(txt) <= 49 and len(txt) <= 2:
                    balls.append(txt)

        # 3. 過濾與排序
        # 根據明報排版，號碼是 9, 18, 19, 20, 28, 32 + 44
        # 我們排除掉總和「170」之類的雜訊 (剛才 balls 已經限制 1-49)
        # 移除重複
        unique_balls = []
        for b in balls:
            if b not in unique_balls:
                unique_balls.append(b)
        
        # 截圖顯示今期號碼是 9, 18, 19, 20, 28, 32 加上特別號 44
        # 如果抓到的數字太多，我們取日期之後出現的第一組 7 個數字
        if len(unique_balls) >= 7:
            res_nums = unique_balls[:6]
            s_no = unique_balls[6]
            return f"🔮 *今日六合彩開獎 (明報源)*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(res_nums)}\n🔴 特別號：{s_no}"
            
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
    tt = get_hkjc_tt_data()
    if tt: send_to_telegram(tt)
    ms = get_mark_six_data()
    if ms: send_to_telegram(ms)
    print("--- 執行完畢 ---")
