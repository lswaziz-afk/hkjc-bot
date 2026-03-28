import requests
from bs4 import BeautifulSoup

# --- 請填寫你的資料 ---
import os
BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')
# ----------------------

from datetime import datetime

def get_hkjc_tt_data():
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. 檢查網頁顯示嘅賽馬日期
        # 馬會網頁通常有個位寫住 "賽事日期: DD/MM/YYYY"
        date_info = soup.find('span', text=lambda t: t and '賽事日期' in t)
        if date_info:
            race_date_str = date_info.get_text(strip=True).split(':')[-1].strip()
            today_str = datetime.now().strftime('%d/%m/%Y')
            
            # 如果網頁日期唔係今日，代表今日無馬跑
            if race_date_str != today_str:
                print(f"今日 ({today_str}) 非賽馬日，跳過發送。")
                return None

        # 2. 搵三T數據 (原本嘅邏輯)
        all_tds = soup.find_all('td')
        for i, td in enumerate(all_tds):
            text = td.get_text(strip=True)
            if "三T" == text:
                numbers = all_tds[i+1].get_text(strip=True)
                dividend = all_tds[i+2].get_text(strip=True)
                
                # 如果未出派彩 (顯示 "-")
                if dividend == "-":
                    return "⏳ 三T派彩仲計算緊，請稍後再手動檢查。"

                return (f"🏇 【今日三T派彩結果】\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"✅ 中獎組合：\n{numbers}\n\n"
                        f"💰 每 $10 派彩：\nHK$ {dividend}\n"
                        f"━━━━━━━━━━━━━━")
        
        return None # 搵唔到三T，可能今日無呢項彩池

    except Exception as e:
        return f"❌ 爬蟲出錯：{e}"

if __name__ == "__main__":
    msg = get_hkjc_tt_data()
    if msg: # 只有當 msg 有內容（唔係 None）先發送
        send_to_telegram(msg)
def send_to_telegram(text):
    # 1. 檢查變數有無讀到 (GitHub 會自動將內容打星號，所以安全)
    print(f"DEBUG: BOT_TOKEN is {'Set' if BOT_TOKEN else 'None'}")
    print(f"DEBUG: CHAT_ID is {'Set' if CHAT_ID else 'None'}")

    # 2. 確保 URL 格式完全正確
    # 注意：bot 呢個字必須喺變數前面
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }

    try:
        # 3. 增加 timeout 同埋直接印出 Response
        r = requests.post(api_url, data=payload, timeout=15)
        print(f"DEBUG: Status Code = {r.status_code}")
        print(f"DEBUG: Response = {r.text}")
        
        if r.status_code == 200:
            print("✅ 成功發送短訊去 Telegram！")
        else:
            print(f"❌ 發送失敗，請檢查 Token 格式。")
    except Exception as e:
        print(f"❌ 連線出錯：{e}")
if __name__ == "__main__":
    print("正在檢查馬會賽果...")
    tt_msg = get_hkjc_tt_data()  # 攞返馬會數據
    send_to_telegram(tt_msg)

