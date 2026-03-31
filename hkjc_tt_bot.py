import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

# 讀取 GitHub Secrets
BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_hkjc_tt_data():
    """爬取三T結果"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        today_str = datetime.now().strftime('%d/%m/%Y')
        
        date_tag = soup.find(lambda tag: tag.name == "span" and "賽事日期" in tag.text)
        if date_tag:
            web_date_text = date_tag.get_text()
            if today_str not in web_date_text:
                print(f"賽馬：今日 ({today_str}) 唔係賽馬日。")
                return None
        else: return None

        all_tds = soup.find_all('td')
        for i, td in enumerate(all_tds):
            if "三T" == td.get_text(strip=True):
                nums = all_tds[i+1].get_text(strip=True).replace(' ', '')
                div = all_tds[i+2].get_text(strip=True)
                if div == "-": return "⏳ 今日有賽馬，但三T派彩計算中..."
                return f"🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{nums}\n💰 派彩：HK$ {div}"
        return None
    except Exception as e:
        print(f"三T爬蟲出錯: {e}")
        return None

def get_mark_six_data():
    """爬取六合彩結果 (使用另一個結果網址以繞過封鎖)"""
    # 呢個網址係馬會嘅結果記錄頁，通常比投注頁更容易爬取
    url = "https://racing.hkjc.com/racing/information/chinese/Lottery/Results.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        today_str = datetime.now().strftime('%d/%m/%Y')
        
        # 1. 搵日期 (通常喺 class="f_fs13" 或者 table 入面)
        # 直接搜尋網頁內所有 DD/MM/YYYY 格式嘅字
        dates = re.findall(r'\d{2}/\d{2}/\d{4}', soup.get_text())
        draw_date = dates[0] if dates else ""
        print(f"六合彩偵測到網頁日期: {draw_date}")

        if today_str not in draw_date:
            print(f"六合彩：今日 ({today_str}) 唔係開獎日。")
            return None

        # 2. 搵號碼
        # 喺呢個頁面，號碼通常喺 <img> 嘅 alt 入面或者特定格仔
        ball_list = []
        # 試吓搵所有包含號碼嘅 <td> 或 <span>
        for img in soup.find_all('img', alt=True):
            alt_text = img['alt']
            if alt_text.isdigit() and 1 <= int(alt_text) <= 49:
                ball_list.append(alt_text)
        
        # 如果 img 唔得，試吓直接搵文字
        if not ball_list:
            tds = soup.find_all('td', class_='bg_light_yellow')
            for td in tds:
                txt = td.get_text(strip=True)
                if txt.isdigit(): ball_list.append(txt)

        if len(ball_list) >= 7:
            nums = ball_list[:6]
            s_no = ball_list[6]
            return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"
        
        return None
    except Exception as e:
        print(f"六合彩爬蟲出錯: {e}")
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
