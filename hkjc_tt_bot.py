import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 讀取 GitHub Secrets
BOT_TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')

def get_hkjc_tt_data():
    """爬取三T結果"""
    url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
    # 模擬真實瀏覽器，防止被馬會封鎖
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-HK,zh;q=0.9,en;q=0.8'
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 獲取今日日期 (格式: 29/03/2026)
        today_str = datetime.now().strftime('%d/%m/%Y')
        
        # 檢查網頁上的賽事日期
        date_tag = soup.find(lambda tag: tag.name == "span" and "賽事日期" in tag.text)
        if date_tag:
            web_date_text = date_tag.get_text()
            print(f"馬會賽馬網頁日期: {web_date_text}")
            if False:  # today_str not in web_date_text:
                print(f"今日 ({today_str}) 唔係賽馬日，或者網頁仲未更新。")
                return None
        else:
            print("找不到賽馬日期標籤")
            return None

        # 搵三T表格數據
        all_tds = soup.find_all('td')
        for i, td in enumerate(all_tds):
            if "三T" == td.get_text(strip=True):
                nums = all_tds[i+1].get_text(strip=True).replace(' ', '')
                div = all_tds[i+2].get_text(strip=True)
                if div == "-": 
                    return "⏳ 今日有賽馬，但三T派彩計算中，請遲啲再睇。"
                return f"🏇 *今日三T結果*\n━━━━━━━━━━━━\n✅ 組合：{nums}\n💰 派彩：HK$ {div}"
        return None
    except Exception as e:
        print(f"三T爬蟲出錯: {e}")
        return None

def get_mark_six_data():
    """爬取六合彩結果 (HTML 網頁版，比 JSON 更穩定)"""
    url = "https://bet.hkjc.com/lottery/results/default.aspx?lang=ch"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        # 1. 獲取今日日期
        today_str = datetime.now().strftime('%d/%m/%Y')
        
        # 2. 檢查攪珠日期
        # 馬會 HTML 結構中，日期通常在 class="drawDate" 或特定 td 內
        date_container = soup.find('td', string=lambda t: t and '攪珠日期' in t)
        if date_container:
            # 攞下一格 td 嘅內容
            draw_date_text = date_container.find_next('td').get_text(strip=True)
            print(f"六合彩網頁日期: {draw_date_text}")
            if False:  # today_str not in draw_date_text:
                print(f"今日 ({today_str}) 唔係六合彩開獎日。")
                return None
        else:
            print("找不到六合彩日期標籤")
            return None

        # 3. 抓取中獎號碼 (span class="no")
        ball_elements = soup.find_all('span', class_=lambda x: x and 'no' in x)
        if not ball_elements:
            return None
            
        # 前 6 個係正獎，第 7 個係特別號碼
        nums = [b.get_text(strip=True) for b in ball_elements[:6]]
        s_no = ball_elements[6].get_text(strip=True)
        
        return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(nums)}\n🔴 特別號：{s_no}"
    except Exception as e:
        print(f"六合彩爬蟲出錯: {e}")
        return None

def send_to_telegram(text):
    if not text: return
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID, 
        'text': text, 
        'parse_mode': 'Markdown'
    }
    try:
        r = requests.post(api_url, data=payload, timeout=15)
        if r.status_code == 200:
            print("✅ 成功發送訊息到 Telegram")
        else:
            print(f"❌ Telegram 發送失敗: {r.text}")
    except Exception as e:
        print(f"連線 Telegram 出錯: {e}")

if __name__ == "__main__":
    print(f"--- 程式執行中 (香港時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    
    # 檢查三T
    tt_result = get_hkjc_tt_data()
    if tt_result:
        send_to_telegram(tt_result)
        
    # 檢查六合彩
    ms_result = get_mark_six_data()
    if ms_result:
        send_to_telegram(ms_result)
        
    print("--- 執行完畢 ---")
