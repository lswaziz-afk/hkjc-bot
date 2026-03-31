import requests
import os
import re
from datetime import datetime

# 讀取 GitHub Secrets
BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def is_marksix_day():
    """檢查今日係咪開獎日 (0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun)"""
    weekday = datetime.now().weekday()
    return weekday in [1, 3, 5, 6] # 暫定二、四、六、日

def get_mark_six_data():
    """六合彩 (明報專頁 - 暴力圖片 alt 執數版)"""
    url = "https://news.mingpao.com/pns/%E5%85%AD%E5%90%88%E5%BD%A9/marksix"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://news.mingpao.com/'
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        html = r.text
        
        # 1. 搵所有 <img> 嘅 alt 屬性數字 (明報波波波專用)
        # Regex 搵 alt="9" 呢種格式
        img_balls = re.findall(r'alt="(\d{1,2})"', html)
        
        # 2. 搵所有 1-49 嘅數字並保持順序
        balls = []
        for b in img_balls:
            num = int(b)
            if 1 <= num <= 49:
                balls.append(b)
        
        # 3. 邏輯判斷
        # 根據你張截圖，最新一期會排喺最前面
        # 號碼係 9, 18, 19, 20, 28, 32 + 44
        if len(balls) >= 7:
            # 攞第一組 7 個數字
            final_7 = balls[:7]
            
            # 保底：檢查網頁係咪真係有今日個「日」(31)
            today_day = datetime.now().strftime('%d')
            if today_day in html or is_marksix_day():
                nums = final_7[:6]
                s_no = final_7[6]
                return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"
        
        print(f"DEBUG: 搵到嘅數字: {balls}")
        return None
    except Exception as e:
        print(f"DEBUG: Error {e}")
        return None

def get_hkjc_tt_data():
    """三T (馬會)"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        if datetime.now().strftime('%d/%m/%Y') in r.text:
            res = re.findall(r'三T.*?<td>(.*?)</td>.*?<td>([\d,]+)</td>', r.text, re.S)
            if res:
                return f"🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{res[0][0].strip()}\n💰 派彩：HK$ {res[0][1].strip()}"
    except: return None

def send_to_telegram(text):
    if not text: return
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'})

if __name__ == "__main__":
    print(f"--- 執行中 (香港: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    # 先行三T
    tt = get_hkjc_tt_data()
    if tt: send_to_telegram(tt)
    # 再行六合彩
    ms = get_mark_six_data()
    if ms: send_to_telegram(ms)
    print("--- 執行完畢 ---")
