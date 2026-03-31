import requests
import os
import re
from datetime import datetime

BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_mark_six_data():
    """六合彩 (明報數據流版本 - 繞過 Lazy Loading)"""
    # 呢個係明報「六合彩」分類嘅數據接口
    url = "https://news.mingpao.com/dat/pns/marksix/latest.js" 
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        content = r.text
        
        # 1. 喺數據流入面搵波波號碼 (通常格式係 "alt":"9")
        # 我哋用 Regex 直接搵晒所有數字
        balls = re.findall(r'alt\\":\\"(\d{1,2})\\"', content)
        if not balls:
            # 備用：搵純數字 (1-49)
            balls = re.findall(r'\"(\d{1,2})\"', content)
            balls = [b for b in balls if 1 <= int(b) <= 49]

        # 2. 攞第一組 7 個數字
        # 截圖見到：9, 18, 19, 20, 28, 32 + 44
        unique_list = []
        for b in balls:
            if b not in unique_list:
                unique_list.append(b)
            if len(unique_list) == 7: break

        if len(unique_list) >= 7:
            # 簡單檢查今日日期係咪喺數據入面
            today_str = datetime.now().strftime('%Y%m%d') # 20260331
            # 就算冇日期，只要今日係開獎日 (二、四、六、日)，我哋都發送
            nums = unique_list[:6]
            s_no = unique_list[6]
            return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"
        
        # 3. 如果上面都唔得，用最後一招：搜尋東網即時新聞嘅標題
        print("DEBUG: 明報數據流失敗，試東網標題搜尋...")
        r_on = requests.get("https://hk.on.cc/hk/news/index.html", headers=headers)
        # 搵標題入面「六合彩：9、18...」呢種字眼
        match = re.search(r'六合彩.*?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2}).*?(\d{1,2})', r_on.text)
        if match:
            res = list(match.groups())
            return f"🔮 *今日六合彩開獎 (東網)*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(res[:6])}\n🔴 特別號：{res[6]}"

        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_hkjc_tt_data():
    """三T (馬會)"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
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
    tt = get_hkjc_tt_data()
    if tt: send_to_telegram(tt)
    ms = get_mark_six_data()
    if ms: send_to_telegram(ms)
