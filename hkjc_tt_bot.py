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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 準備今日日期格式
        today_str = datetime.now().strftime('%d/%m/%Y')
        
        date_tag = soup.find(lambda tag: tag.name == "span" and "賽事日期" in tag.text)
        if date_tag:
            web_date_text = date_tag.get_text()
            print(f"馬會賽馬日期: {web_date_text}")
            if today_str not in web_date_text:
                return None
        else:
            return None

        all_tds = soup.find_all('td')
        for i, td in enumerate(all_tds):
            if "三T" == td.get_text(strip=True):
                nums = all_tds[i+1].get_text(strip=True).replace(' ', '')
                div = all_tds[i+2].get_text(strip=True)
                if div == "-": 
                    return "⏳ 今日有賽馬，但三T派彩計算中..."
                return f"🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{nums}\n💰 派彩：HK$ {div}"
        return None
    except Exception as e:
        print(f"三T爬蟲出錯: {e}")
        return None

def get_mark_six_data():
    """爬取六合彩 (東網即時新聞源 - 最速更新版)"""
    # 呢個網址係東網六合彩專頁，更新最快
    url = "https://hk.on.cc/fe/m6/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. 攞今日日期格式
        today_f1 = datetime.now().strftime('%Y/%m/%d') # 2026/03/31
        today_f2 = datetime.now().strftime('%d/%m/%Y') # 31/03/2026
        
        content = soup.get_text()
        
        # 2. 搵號碼 (1-49 嘅數字)
        # 喺呢個頁面，波波通常喺 <span class="ball_red"> 等標籤
        balls = []
        # 搵所有標籤入面係 1-49 嘅純數字
        for tag in soup.find_all(['span', 'div', 'b', 'td']):
            txt = tag.get_text(strip=True)
            if txt.isdigit() and 1 <= int(txt) <= 49 and len(txt) <= 2:
                balls.append(txt)

        # 3. 邏輯判斷
        if (today_f1 in content) or (today_f2 in content):
            print(f"✅ 偵測到今日日期 {today_f1}，準備發送結果。")
        else:
            # 保底機制：如果搵唔到今日日期，但搵到至少 7 個波，我哋都試吓發送
            # (因為有時東網更新咗個波，但忘記改個日期字眼)
            if len(balls) >= 7:
                print("⚠️ 未見今日日期，但偵測到號碼球，嘗試發送最新結果。")
            else:
                print("❌ 網頁內容完全未更新，跳過。")
                return None

        # 攞最新出現嗰 7 個波 (通常喺最頂)
        # 去重但保持順序
        unique_balls = []
        for b in balls:
            if b not in unique_balls:
                unique_balls.append(b)
                if len(unique_balls) == 7: break # 攞夠 7 個就停
        
        if len(unique_balls) >= 7:
            nums = unique_balls[:6]
            s_no = unique_balls[6]
            return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"
        
        return None
    except Exception as e:
        print(f"六合彩爬蟲出錯: {e}")
        return None
def send_to_telegram(text):
    if not text: return
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    try:
        requests.post(api_url, data=payload, timeout=15)
        print("✅ 訊息已發送")
    except:
        print("❌ 發送失敗")

if __name__ == "__main__":
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"--- 執行中 (香港: {now_str}) ---")
    
    # 賽馬
    tt_msg = get_hkjc_tt_data()
    if tt_msg: send_to_telegram(tt_msg)
    
    # 六合彩
    ms_msg = get_mark_six_data()
    if ms_msg: send_to_telegram(ms_msg)
    
    print("--- 執行完畢 ---")
