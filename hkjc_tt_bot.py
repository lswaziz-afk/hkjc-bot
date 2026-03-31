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
    """爬取六合彩 (東網即時新聞標籤頁 - 繞過快取最有效)"""
    # 這是東網「六合彩」標籤的新聞列表頁
    url = "https://hk.on.cc/cnt/news/index.html?section=news&tag=六合彩"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. 搵第一條新聞 (最新嗰篇)
        # 東網新聞列表通常在 .article 裡面
        latest_news = soup.find('div', class_='article')
        if not latest_news:
            # 備用方案：搵所有包含「六合彩」字眼嘅 link
            latest_news = soup.find('a', title=re.compile(r'六合彩'))
            
        if latest_news:
            # 2. 喺呢篇新聞嘅標題或者簡介度搵號碼
            news_text = latest_news.get_text()
            print(f"DEBUG: 偵測到最新六合彩新聞: {news_text[:50]}...")
            
            # 直接喺新聞文字入面搵 7 個數字
            # 六合彩新聞通常寫法係：9、18、19、20、28、32；特別號碼為44。
            # 我哋用 Regex 抽出所有數字
            all_numbers = re.findall(r'\d+', news_text)
            # 過濾 1-49 嘅數字
            balls = [n for n in all_numbers if 1 <= int(n) <= 49]
            
            # 如果標題冇，就攞呢篇新聞嘅 link 入去睇 (呢度做簡化，直接掃描列表)
            if len(balls) >= 7:
                # 攞最尾嗰 7 個數字 (通常最新結果會寫喺標題或摘要)
                res_nums = balls[:6]
                s_no = balls[6]
                return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(res_nums)}\n🔴 特別號：{s_no}"
        
        # 3. 如果列表掃描失敗，用返「首頁暴力掃描」但移除日期檢查 (保底)
        print("⚠️ 列表掃描未見今日結果，執行首頁保底掃描...")
        r_home = requests.get("https://hk.on.cc/hk/news/index.html", headers=headers, timeout=20)
        soup_home = BeautifulSoup(r_home.text, 'html.parser')
        
        # 搵所有波波數字
        all_spans = soup_home.find_all(['span', 'div', 'b'])
        potential_balls = []
        for s in all_spans:
            t = s.get_text(strip=True)
            if t.isdigit() and 1 <= int(t) <= 49 and len(t) <= 2:
                potential_balls.append(t)
        
        # 攞最後出現嘅 7 個 (通常係右邊個 box)
        if len(potential_balls) >= 7:
            res_balls = potential_balls[-7:]
            return f"🔮 *今日六合彩開獎 (保底偵測)*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(res_balls[:6])}\n🔴 特別號：{res_balls[6]}"

        return None
    except Exception as e:
        print(f"六合彩新聞爬蟲出錯: {e}")
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
