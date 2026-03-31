import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_hkjc_tt_data():
    """爬取三T (維持馬會資訊網，通常賽馬資訊封鎖較鬆)"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        today_str = datetime.now().strftime('%d/%m/%Y')
        
        date_tag = soup.find(lambda tag: tag.name == "span" and "賽事日期" in tag.text)
        if date_tag:
            if today_str not in date_tag.get_text(): return None
        else: return None

        all_tds = soup.find_all('td')
        for i, td in enumerate(all_tds):
            if "三T" == td.get_text(strip=True):
                nums = all_tds[i+1].get_text(strip=True).replace(' ', '')
                div = all_tds[i+2].get_text(strip=True)
                if div == "-": return "⏳ 三T派彩計算中..."
                return f"🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{nums}\n💰 派彩：HK$ {div}"
    except: return None

def get_mark_six_data():
    """爬取六合彩 (改用第三方 852.com 數據源，防止 GitHub 被封)"""
    url = "https://www.852.com/mark6/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        # 1. 搵日期
        today_str = datetime.now().strftime('%d/%m/%Y')
        # 搜尋包含 DD/MM/YYYY 格式嘅文字
        page_text = soup.get_text()
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', page_text)
        draw_date = date_match.group(1) if date_match else ""
        print(f"第三方網頁日期: {draw_date}")

        if today_str != draw_date:
            print(f"今日 ({today_str}) 非開獎日或第三方網頁未更新。")
            return None

        # 2. 搵號碼
        # 第三方網頁通常用唔同嘅 class 顯示波色，我哋搵連續 7 個數字
        balls = []
        # 搵所有標記為號碼嘅標籤 (通常係 ball 或 no class)
        all_spans = soup.find_all(['span', 'div'])
        for s in all_spans:
            txt = s.get_text(strip=True)
            if txt.isdigit() and 1 <= int(txt) <= 49:
                balls.append(txt)
        
        # 排除重複號碼
        unique_balls = []
        for b in balls:
            if b not in unique_balls: unique_balls.append(b)
        
        if len(unique_balls) >= 7:
            nums = unique_balls[:6]
            s_no = unique_balls[6]
            return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"
        
        return None
    except Exception as e:
        print(f"第三方數據出錯: {e}")
        return None

def send_to_telegram(text):
    if not text: return
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    requests.post(api_url, data=payload, timeout=15)

if __name__ == "__main__":
    print(f"--- 執行中 (香港: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    
    tt = get_hkjc_tt_data()
    if tt: send_to_telegram(tt)
    
    ms = get_mark_six_data()
    if ms: send_to_telegram(ms)
    
    print("--- 執行完畢 ---")
