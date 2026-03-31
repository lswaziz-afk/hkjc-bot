import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

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
    """爬取六合彩 (東網通用掃描版)"""
    # 呢個網址係東網專門擺放六合彩資訊嘅地方
    url = "https://hk.on.cc/fe/m6/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        content = r.text
        
        # 1. 檢查日期 (搵 2026-03-31 或 31/03/2026 或 31-03-2026)
        today = datetime.now()
        date_patterns = [
            today.strftime('%d/%m/%Y'),
            today.strftime('%Y-%m-%d'),
            today.strftime('%Y年%m月%d日').replace('年0', '年').replace('月0', '月') # 處理 2026年3月31日
        ]
        
        found_date = False
        for p in date_patterns:
            if p in content:
                print(f"DEBUG: 搵到日期匹配: {p}")
                found_date = True
                break
        
        if not found_date:
            print(f"DEBUG: 東網網頁內容尚未更新今日日期。")
            # 為了測試，如果日期不符但你想看結果，可以把下面 return None 註解掉
            return None

        # 2. 搵號碼 (暴力掃描所有 1-49 嘅數字)
        # 喺東網 m6 頁面，號碼通常被包喺 <span class="ball_red"> 等標籤
        soup = BeautifulSoup(content, 'html.parser')
        ball_elements = soup.find_all(lambda tag: tag.name in ['span', 'div', 'td'] and tag.get_text(strip=True).isdigit())
        
        potential_numbers = []
        for b in ball_elements:
            val = b.get_text(strip=True)
            if val.isdigit() and 1 <= int(val) <= 49:
                potential_numbers.append(val)
        
        # 排除重複並保持順序
        balls = []
        for n in potential_numbers:
            if n not in balls:
                balls.append(n)
        
        if len(balls) >= 7:
            # 通常最新一期嘅 7 個波會最先出現
            res_nums = balls[:6]
            s_no = balls[6]
            return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(res_nums)}\n🔴 特別號：{s_no}"
        
        return None
    except Exception as e:
        print(f"東網掃描出錯: {e}")
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
