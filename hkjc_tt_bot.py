import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_hkjc_tt_data():
    """三T (馬會資訊網)"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        today = datetime.now().strftime('%d/%m/%Y')
        if today in soup.get_text():
            all_tds = soup.find_all('td')
            for i, td in enumerate(all_tds):
                if "三T" == td.get_text(strip=True):
                    return f"🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{all_tds[i+1].get_text(strip=True)}\n💰 派彩：HK$ {all_tds[i+2].get_text(strip=True)}"
    except: return None

def get_mark_six_data():
    """六合彩 (Google 搜尋東網結果版)"""
    # 模擬 Google 搜尋「東網 六合彩 今日日期」
    today_query = datetime.now().strftime('%Y/%m/%d')
    url = f"https://www.google.com/search?q=on.cc+六合彩+攪珠結果+{today_query}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        r = requests.get(url, headers=headers, timeout=20)
        # Google 搜尋結果嘅摘要通常喺 <span> 埋面
        soup = BeautifulSoup(r.text, 'html.parser')
        page_text = soup.get_text()
        
        # 喺全頁搵連續或者散開嘅數字
        # 六合彩新聞通常格式：9、18、19、20、28、32及特別號碼44
        # 我哋搵出所有 1-49 嘅數字
        all_nums = re.findall(r'\b\d{1,2}\b', page_text)
        balls = [n for n in all_nums if 1 <= int(n) <= 49]
        
        # 排除重複，攞前 7 個
        unique_balls = []
        for b in balls:
            if b not in unique_balls:
                unique_balls.append(b)
        
        if len(unique_balls) >= 7:
            # 根據 Google 摘要，通常最新結果會排最前
            return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(unique_balls[:6])}\n🔴 特別號：{unique_balls[6]}"
        
        # 如果 Google 唔得，試多次東網另一個 JSON 接口
        print("DEBUG: Google 搜尋未果，試最後一個接口...")
        r_api = requests.get("https://hk.on.cc/hk/bkn/cnt/news/index.html", headers=headers)
        # 暴力執數
        res = re.findall(r'(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2}).*?(\d{1,2})', r_api.text)
        if res:
            return f"🔮 *今日六合彩開獎 (API)*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(res[0][:6])}\n🔴 特別號：{res[0][6]}"
            
        return None
    except Exception as e:
        print(f"Error: {e}")
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
