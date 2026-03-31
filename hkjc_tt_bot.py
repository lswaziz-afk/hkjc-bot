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
    """爬取六合彩 (針對東網新聞首頁格式優化)"""
    url = "https://hk.on.cc/hk/news/index.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 兼容多種日期格式：2026/03/31 或 31/03/2026
        today_fmt1 = datetime.now().strftime('%Y/%m/%d')
        today_fmt2 = datetime.now().strftime('%d/%m/%Y')
        
        content = soup.get_text()
        if today_fmt1 not in content and today_fmt2 not in content:
            print(f"六合彩：網頁未見今日日期 ({today_fmt1})，跳過。")
            return None

        # 暴力抓取所有 1-49 的數字球
        balls = []
        # 搵所有標籤入面純數字且長度 <= 2 的
        for tag in soup.find_all(['span', 'div', 'b']):
            txt = tag.get_text(strip=True)
            if txt.isdigit() and 1 <= int(txt) <= 49 and len(txt) <= 2:
                balls.append(txt)
        
        # 根據東網排版，六合彩通常連續出現 7 個數字
        # 我哋攞最後出現嗰 7 個數字（通常係右側資訊欄）
        if len(balls) >= 7:
            # 攞最後 7 個波
            latest_balls = balls[-7:]
            # 去重但保持順序 (防止重複抓取)
            final_balls = []
            for b in latest_balls:
                final_balls.append(b)
            
            nums = final_balls[:6]
            s_no = final_balls[6]
            return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"
        
        print("DEBUG: 找不到足夠的號碼球")
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
