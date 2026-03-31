import requests
import os
import re
from datetime import datetime

BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_mark_six_data():
    """六合彩 (東網接口 - 只要有數就執)"""
    url = "https://on.cc/fe/m6/data/m6_data.json"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            nums = data.get('result', '').split(',')
            s_no = data.get('special', '')
            draw_date = data.get('drawDate', '未知日期')
            
            if len(nums) >= 6:
                print(f"DEBUG: 成功從 JSON 執到號碼 (日期: {draw_date})")
                return f"🔮 *最新六合彩開獎*\n━━━━━━━━━━━━\n📅 日期：{draw_date}\n⚪️ 號碼：{', '.join(nums[:6])}\n🔴 特別號：{s_no}"
        
        # 備援：掃描網頁
        print("DEBUG: JSON 失敗，掃描網頁中...")
        r_web = requests.get("https://hk.on.cc/hk/news/index.html", headers=headers, timeout=15)
        match = re.search(r'(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2}).*?(\d{1,2})', r_web.text)
        if match:
            res = list(match.groups())
            print("DEBUG: 成功從網頁掃描到號碼")
            return f"🔮 *最新六合彩開獎 (掃描)*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(res[:6])}\n🔴 特別號：{res[6]}"
            
    except Exception as e:
        print(f"DEBUG: Error {e}")
    return None

def get_hkjc_tt_data():
    """三T (直接執，唔理日期)"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        # 搵「三T」後面嘅 <td> 內容
        res = re.findall(r'三T.*?<td>(.*?)</td>.*?<td>([\d,]+)</td>', r.text, re.S)
        if res:
            print("DEBUG: 成功執到三T數據")
            return f"🏇 *最新三T結果*\n━━━━━━━━━━━━\n✅ 組合：{res[0][0].strip()}\n💰 派彩：HK$ {res[0][1].strip()}"
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
    print("--- 執行完畢 ---")
