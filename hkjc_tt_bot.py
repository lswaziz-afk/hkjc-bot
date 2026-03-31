import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

# 讀取 GitHub Secrets
BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_hkjc_tt_data():
    """爬取三T結果 (Racing 頁面)"""
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
    """爬取六合彩結果 (使用官方數據 API)"""
    # 呢個係馬會官方數據來源，回傳 JSON，最穩定且唔易被封
    url = "https://is.hkjc.com/jcbw/static/statistics/mark6/mark6_result_ch.js"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        # 由於呢個係 .js 檔案，內容格式係 "var ... = {...};"
        # 我哋需要用正則表達式抽取出裡面嘅 JSON 部分
        content = r.text
        
        # 搜尋日期
        draw_date_match = re.search(r'"date":"(\d{2}/\d{2}/\d{4})"', content)
        draw_date = draw_date_match.group(1) if draw_date_match else ""
        print(f"六合彩偵測到日期: {draw_date}")

        today_str = datetime.now().strftime('%d/%m/%Y')
        if today_str != draw_date:
            print(f"六合彩：今日 ({today_str}) 唔係開獎日。")
            return None

        # 搜尋號碼 (no1, no2... no6 + sno)
        no1 = re.search(r'"no1":"(\d+)"', content).group(1)
        no2 = re.search(r'"no2":"(\d+)"', content).group(1)
        no3 = re.search(r'"no3":"(\d+)"', content).group(1)
        no4 = re.search(r'"no4":"(\d+)"', content).group(1)
        no5 = re.search(r'"no5":"(\d+)"', content).group(1)
        no6 = re.search(r'"no6":"(\d+)"', content).group(1)
        sno = re.search(r'"sno":"(\d+)"', content).group(1)
        
        nums = [no1, no2, no3, no4, no5, no6]
        return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{sno}"
    except Exception as e:
        print(f"六合彩 API 出錯: {e}")
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
