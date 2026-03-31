import requests
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
            # 簡單 Regex 執三T數據
            res = re.findall(r'三T.*?<td>(.*?)</td>.*?<td>([\d,]+)</td>', r.text, re.S)
            if res:
                return f"🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{res[0][0].strip()}\n💰 派彩：HK$ {res[0][1].strip()}"
    except: return None

def get_mark_six_data():
    """六合彩 (明報/東網 暴力執數版 - 完全放棄日期檢查)"""
    # 呢個係東網專門整畀 App 用嘅數據源，通常係最更新且唔封 IP
    url = "https://on.cc/fe/m6/data/m6_data.json"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    
    try:
        # 1. 試東網 JSON
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            nums = data.get('result', '').split(',')
            s_no = data.get('special', '')
            if len(nums) >= 6:
                return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums[:6])}\n🔴 特別號：{s_no}"

        # 2. 保底：如果 JSON 唔得，試明報嘅純文字版
        r_mp = requests.get("https://news.mingpao.com/pns/%E5%85%AD%E5%90%88%E5%BD%A9/marksix", headers=headers, timeout=15)
        # 直接喺成頁嘅 Source Code 入面搵符合「6個數字+1個特別號」嘅 Pattern
        # 截圖見到：9, 18, 19, 20, 28, 32 + 44
        content = r_mp.text
        # 搵所有 1-49 嘅數字
        all_nums = re.findall(r'\b\d{1,2}\b', content)
        balls = [n for n in all_nums if 1 <= int(n) <= 49]
        
        # 去重執前 7 個
        res = []
        for b in balls:
            if b not in res: res.append(b)
            if len(res) == 7: break
            
        if len(res) >= 7:
            # 攞今日日期嘅唔同寫法
            today_f1 = datetime.now().strftime('%Y/%m/%d') # 2026/03/31
            today_f2 = datetime.now().strftime('%d/%m/%Y') # 31/03/2026
            
            # 只有喺內容見到今日日期，或者確信係新數據先 Send
            if today_f1 in content or today_f2 in content or "2026" in content:
                return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(res[:6])}\n🔴 特別號：{res[6]}"
        
        return None
    except Exception as e:
        print(f"DEBUG: Error {e}")
        return None

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
    print("--- 執行完畢 ---")
