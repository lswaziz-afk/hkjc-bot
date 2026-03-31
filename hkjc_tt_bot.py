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
    """爬取六合彩 (改用東網 on.cc 數據源)"""
    # 東網嘅六合彩結果頁面非常穩定
    url = "https://hk.on.cc/hk/bkn/cnt/news/20210105/bkn-20210105000041285-0105_00822_001.html" 
    # 註：東網通常用一個固定 ID 頁面顯示即時結果
    # 如果上面唔得，我哋改用佢嘅即時新聞列表搜尋
    url = "https://hk.on.cc/fe/m6/" 
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        # 1. 檢查日期
        today_str = datetime.now().strftime('%d/%m/%Y')
        page_text = soup.get_text()
        
        # 東網日期格式有時係 2026年03月31日
        today_c = datetime.now().strftime('%Y年%m月%d日')
        
        if (today_str not in page_text) and (today_c not in page_text):
            print(f"東網未偵測到今日 ({today_str}) 嘅結果。")
            return None

        # 2. 搵號碼 (東網通常會標記球號)
        balls = []
        # 東網嘅波色球 class 通常好明顯
        ball_elements = soup.find_all(class_=re.compile(r'ball|number|markSix', re.I))
        for b in ball_elements:
            t = b.get_text(strip=True)
            if t.isdigit() and 1 <= int(t) <= 49:
                balls.append(t)
        
        # 如果搵唔到 class，直接用 Regex 喺文字入面搵連續數字
        if not balls:
            # 搵類似「開獎號碼為：1, 2, 3...」嘅字眼
            nums_match = re.findall(r'\b\d{1,2}\b', page_text)
            balls = [n for n in nums_match if 1 <= int(n) <= 49]

        if len(balls) >= 7:
            # 攞最後一次出現嘅 7 個波 (通常最新結果喺最頂)
            nums = balls[:6]
            s_no = balls[6]
            return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"
        
        return None
    except Exception as e:
        print(f"東網數據出錯: {e}")
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
