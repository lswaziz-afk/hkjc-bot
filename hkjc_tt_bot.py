import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_hkjc_tt_data():
    """爬取三T結果"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 檢查日期 (確保係今日賽事)
        date_tag = soup.find(lambda tag: tag.name == "span" and "賽事日期" in tag.text)
        if date_tag:
            race_date = date_tag.get_text().split(":")[-1].strip()
            if race_date != datetime.now().strftime('%d/%m/%Y'):
                return None # 唔係今日，跳過

        all_tds = soup.find_all('td')
        for i, td in enumerate(all_tds):
            if "三T" == td.get_text(strip=True):
                nums = all_tds[i+1].get_text(strip=True)
                div = all_tds[i+2].get_text(strip=True)
                if div == "-": return "⏳ 三T派彩計算中..."
                return f"🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{nums}\n💰 派彩：HK$ {div}"
        return None
    except: return None

def get_mark_six_data():
    """爬取六合彩結果"""
    url = "https://bet.hkjc.com/contentserver/jcbw/cmc/last30draws.json" # 用 JSON API 更準確
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        latest = data[0] # 拎最近一期
        
        # 檢查開獎日期係咪今日
        draw_date_ts = int(latest['date']) / 1000
        draw_date = datetime.fromtimestamp(draw_date_ts).strftime('%d/%m/%Y')
        
        if draw_date == datetime.now().strftime('%d/%m/%Y'):
            nums = latest['no'] # 中獎號碼
            s_no = latest['sno'] # 特別號碼
            return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"
        return None
    except: return None

def send_to_telegram(text):
    if not text: return
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    requests.post(api_url, data=payload)

if __name__ == "__main__":
    # 兩樣都 check
    tt_msg = get_hkjc_tt_data()
    ms_msg = get_mark_six_data()
    
    if tt_msg: send_to_telegram(tt_msg)
    if ms_msg: send_to_telegram(ms_msg)
