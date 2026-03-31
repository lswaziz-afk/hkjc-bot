def get_mark_six_data():
    """爬取六合彩 (針對東網新聞首頁格式)"""
    url = "https://hk.on.cc/hk/news/index.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. 搵今日日期 (對應截圖見到嘅 2026/03/31)
        today_fmt1 = datetime.now().strftime('%Y/%m/%d') # 2026/03/31
        today_fmt2 = datetime.now().strftime('%d/%m/%Y') # 31/03/2026
        
        content = soup.get_text()
        if today_fmt1 not in content and today_fmt2 not in content:
            print(f"DEBUG: 網頁未見今日日期 ({today_fmt1})")
            return None

        # 2. 定位六合彩資訊框 (根據截圖，搵包含「攪珠結果」嘅 div)
        # 搵所有包含數字嘅波波 (截圖見到係圓圈入面有數字)
        balls = []
        
        # 搵所有標籤入面純數字 1-49 嘅
        for span in soup.find_all(['span', 'div', 'td']):
            txt = span.get_text(strip=True)
            if txt.isdigit() and 1 <= int(txt) <= 49:
                # 排除一啲無關嘅細字 (例如 2.1M 觀看次數)
                if len(txt) <= 2: 
                    balls.append(txt)
        
        # 東網首頁通常會將號碼放埋一齊
        # 根據你截圖：9, 18, 19, 20, 28, 32 + 44
        # 我哋搵出最後出現（或者最頻繁）嘅一組 7 個數字
        if len(balls) >= 7:
            # 攞最後嗰 7 個數字 (通常係右邊個 box)
            res_nums = balls[-7:-1] # 前 6 個
            s_no = balls[-1]        # 最後一個係特別號
            return f"🔮 *今日六合彩開獎*\n━━━━━━━━━━━━\n⚪️ 號碼：{', '.join(res_nums)}\n🔴 特別號：{s_no}"
        
        return None
    except Exception as e:
        print(f"六合彩爬蟲出錯: {e}")
        return None
