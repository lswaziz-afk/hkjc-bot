import requests
from bs4 import BeautifulSoup

# --- 請填寫你的資料 ---
import os
BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')
# ----------------------

def get_hkjc_tt_data():
    """爬取馬會三T結果"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 搜尋包含「三T」字眼的表格單元格
        all_tds = soup.find_all('td')
        
        for i, td in enumerate(all_tds):
            text = td.get_text(strip=True)
            if "三T" == text:
                # 根據馬會網頁結構，中獎號碼通常在下一格，派彩在再下一格
                numbers = all_tds[i+1].get_text(strip=True)
                dividend = all_tds[i+2].get_text(strip=True)
                
                msg = (f"🏇 【今日三T派彩結果】\n"
                       f"━━━━━━━━━━━━━━\n"
                       f"✅ 中獎組合：\n{numbers}\n\n"
                       f"💰 每 $10 派彩：\nHK$ {dividend}\n"
                       f"━━━━━━━━━━━━━━")
                return msg
        
        return "⚠️ 馬會網頁仲未更新三T派彩，請稍後再試。"

    except Exception as e:
        return f"❌ 爬蟲出錯：{e}"

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
    tt_msg = get_hkjc_tt_data()
    send_to_telegram(tt_msg)
