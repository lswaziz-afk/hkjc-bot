import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 讀取 GitHub Secrets
BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_hkjc_tt_data():
    """爬取三T結果"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 獲取今日日期 (格式: 29/03/2026)
        today_str = datetime.now().strftime('%d/%m/%Y')
        
        # 檢查網頁日期
        date_tag = soup.find(lambda tag: tag.name == "span" and "賽事日期" in tag.text)
        if date_tag:
            web_date_text = date_tag.get_text()
            # 只要今日日期有喺個標籤入面出現就 OK
            if today_str not in web_date_text:
                print(f"今日 ({today_str}) 非賽馬日或網頁未更新。")
                return None
        else:
            return None

        all_tds = soup.find_all('td')
        for i, td in enumerate(all_tds):
            if "三T" == td.get_text(strip=True):
                nums = all_tds[i+1].get_text(strip=True)
                div = all_tds[i+2].get_text(strip=True)
                if div == "-": 
                    return "⏳ 今日有賽馬，但三T派彩計算中..."
                return f"🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{nums}\n💰 派彩：HK$ {div}"
        return None
    except Exception as e:
        print(f"三T爬蟲出錯: {e}")
        return None

def get_mark_six_data():
    """爬取六合彩結果"""
    url = "https://bet.hkjc.com/contentserver/jcbw/cmc/last30draws.json"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        latest = data[0]
        
        # 檢查開獎日期
        draw_date_ts = int(latest['date']) / 1000
        draw_date = datetime.fromtimestamp(draw_date_ts).strftime('%d/%m/%Y')
        today_str = datetime.now().strftime('%d/%m/%Y')
        
        if draw_date == today_str:
            nums = latest['no']
            s_no = latest['sno']
            return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"
        return None
    except Exception as e:
        print(f"六合彩爬蟲出錯: {e}")
        return None

def send_to_telegram(text):
    if not text: return
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID, 
        'text': text, 
        'parse_mode': 'Markdown'
    }
    try:
        r = requests.post(api_url, data=payload, timeout=10)
        if r.status_code == 200:
            print("✅ 訊息發送成功")
        else:
            print(f"❌ 發送失敗: {r.text}")
    except Exception as e:
        print(f"Telegram 連線出錯: {e}")

if __name__ == "__main__":
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    tt_msg = get_hkjc_tt_data()
    ms_msg = get_mark_six_data()
    
    if tt_msg: send_to_telegram(tt_msg)
    if ms_msg: send_to_telegram(ms_msg)
