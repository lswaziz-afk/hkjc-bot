import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

# 讀取 GitHub Secrets
BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_hkjc_tt_data():
    """三T (馬會資訊網)"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        today = datetime.now().strftime('%d/%m/%Y')
        if today in r.text:
            soup = BeautifulSoup(r.text, 'html.parser')
            all_tds = soup.find_all('td')
            for i, td in enumerate(all_tds):
                if "三T" == td.get_text(strip=True):
                    return f"🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{all_tds[i+1].get_text(strip=True)}\n💰 派彩：HK$ {all_tds[i+2].get_text(strip=True)}"
    except: return None

def get_mark_six_data():
    """六合彩 (明報 - 暴力抓取版)"""
    url = "https://news.mingpao.com/pns/%E5%85%AD%E5%90%88%E5%BD%A9/marksix"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://news.mingpao.com/'
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. 放寬日期檢查：只要今日嘅「日」(31) 有出現喺網頁就繼續
        day_str = datetime.now().strftime('%d')
        if day_str not in soup.get_text():
            print(f"DEBUG: 網頁文字未見 '{day_str}' 號，可能未更新。")
            # 保底：如果真係搵唔到日期，但你想強行試吓執波，可以註解下面呢行
            # return None 

        # 2. 抓取所有 1-49 嘅波 (優先搵 alt 屬性)
        balls = []
        # 搵 <img> 嘅 alt
        for img in soup.find_all('img', alt=True):
            a = img['alt'].strip()
            if a.isdigit() and 1 <= int(a) <= 49:
                balls.append(a)
        
        # 搵 <span> 或 <li> 入面嘅純數字 (長度 1-2 位)
        for tag in soup.find_all(['span', 'li', 'div']):
            t = tag.get_text(strip=True)
            if t.isdigit() and 1 <= int(t) <= 49 and len(t) <= 2:
                balls.append(t)

        # 3. 執波邏輯：明報截圖係 9, 18, 19, 20, 28, 32 + 44
        # 我哋攞「第一組」連續出現嘅 7 個唔同數字
        res_list = []
        for b in balls:
            if b not in res_list:
                res_list.append(b)
            if len(res_list) == 7:
                break
        
        if len(res_list) >= 7:
            return f"🔮 *今日六合彩開獎 (明報)*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(res_list[:6])}\n🔴 特別號：{res_list[6]}"
        
        print(f"DEBUG: 執到嘅數字唔夠 7 個: {res_list}")
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
