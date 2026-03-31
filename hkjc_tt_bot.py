import requests
import os
import re
from datetime import datetime

BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_mark_six_data():
    """六合彩 (直接執馬會官方後台 JSON)"""
    # 呢個係馬會官方顯示最近 30 期結果嘅接口，最準確
    url = "https://bet.hkjc.com/contentserver/jcbw/cmc/last30draw.json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://bet.hkjc.com/'
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            # 攞第一筆 (最新)
            latest = data[0]
            draw_date = latest.get('date', '') # 格式通常係 31/03/2026
            
            # 只要今日日期 (31/03) 有出現，就係最新一期
            today_short = datetime.now().strftime('%d/%m')
            if today_short in draw_date:
                nums = latest.get('no', '').split('+') # 9+18+19+20+28+32
                s_no = latest.get('sno', '')
                balls = nums[0].replace('+', ', ')
                print(f"DEBUG: 馬會官方執到號碼: {balls} + {s_no}")
                return f"🔮 *今日六合彩開獎 (官方)*\n━━━━━━━━━━━━\n📅 日期：{draw_date}\n⚪️ 號碼：{balls}\n🔴 特別號：{s_no}"
        
        # 備援方案：如果馬會封 IP，試一個唔理結構嘅「數字大搜捕」
        print("DEBUG: 官方 JSON 失敗，啟動備援掃描...")
        r_backup = requests.get("https://hk.on.cc/hk/news/index.html", headers={'User-Agent': 'Mozilla/5.0'})
        # 搵所有標點分隔嘅 1-49 數字組合
        nums = re.findall(r'(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2})[、,]\s?(\d{1,2}).*?(\d{1,2})', r_backup.text)
        if nums:
            res = nums[0]
            return f"🔮 *今日六合彩開獎 (掃描)*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(res[:6])}\n🔴 特別號：{res[6]}"
            
    except Exception as e:
        print(f"DEBUG: 六合彩出錯: {e}")
    return None

def get_hkjc_tt_data():
    """三T (維持現有成功邏輯)"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        # 搵「三T」後面嘅 td 數據
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
    
    # 執行
    tt = get_hkjc_tt_data()
    if tt: send_to_telegram(tt)
    
    ms = get_mark_six_data()
    if ms: send_to_telegram(ms)
    
    print("--- 執行完畢 ---")
