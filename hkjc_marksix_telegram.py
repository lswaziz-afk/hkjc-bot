#!/usr/bin/env python3
"""
香港六合彩（Mark Six）結果自動通知 Telegram
支援 GitHub Actions 定時執行

開彩時間：逢星期二、四、及非賽馬日嘅星期六或日，晚上 9:30
資料來源：lottery.hk（HTML table 結構固定，精準可靠）
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import json
import os

# ============================================================
# 設定（GitHub Actions 會從 Secrets 讀取環境變數）
# ============================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 號碼對應顏色（六合彩傳統色）
NUMBER_COLORS = [
    (range(1,  8),  "🔴"),  # 紅
    (range(8,  15), "🔵"),  # 藍
    (range(15, 24), "🟢"),  # 綠
    (range(24, 32), "🟠"),  # 橙
    (range(32, 40), "🟣"),  # 紫
    (range(40, 50), "⚪"),  # 白
]

def get_color(num: int) -> str:
    for r, color in NUMBER_COLORS:
        if num in r:
            return color
    return "⚫"

def fmt_num(num: int, is_extra: bool = False) -> str:
    color = get_color(num)
    n = f"{num:02d}"
    return f"✨{color}{n}" if is_extra else f"{color}{n}"


# ============================================================
# 抓取六合彩結果（lottery.hk）
# ============================================================

RESULTS_URL = "https://lottery.hk/en/mark-six/results/"

def fetch_latest_result() -> dict | None:
    """
    從 lottery.hk 抓取最新一期六合彩結果。

    頁面 HTML table 格式（每行一期）：
      <tr>
        <td>26/036</td>               ← 期數
        <td>04/04/2026</td>           ← 日期
        <td><ul><li>20</li>...<li>43</li></ul></td>  ← 7個號碼（前6正碼，第7特別）
        <td>...</td>
      </tr>
    """
    try:
        resp = requests.get(RESULTS_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"[lottery.hk] 連接失敗：{e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # 搵結果 table
    table = None
    for t in soup.find_all("table"):
        if t.find("li"):
            table = t
            break

    if not table:
        print("[lottery.hk] 搵唔到結果 table")
        return None

    # 搵第一行有效數據（跳過 header 行同月份分隔行）
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue

        draw_no_text   = cells[0].get_text(strip=True)   # 例如 "26/036"
        draw_date_text = cells[1].get_text(strip=True)   # 例如 "04/04/2026"
        balls_cell     = cells[2]

        # 確認期數格式係 YY/NNN
        if "/" not in draw_no_text or len(draw_no_text) < 5:
            continue

        # 從 <li> 精準提取號碼，完全唔用 regex
        ball_els = balls_cell.find_all("li")
        nums = []
        for li in ball_els:
            t = li.get_text(strip=True)
            if t.isdigit() and 1 <= int(t) <= 49:
                nums.append(int(t))

        if len(nums) != 7:
            print(f"[lottery.hk] 期數 {draw_no_text}：號碼唔係7個，得到 {nums}")
            continue

        # 解析日期格式 DD/MM/YYYY
        try:
            draw_date = datetime.strptime(draw_date_text, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            draw_date = draw_date_text

        print(f"[lottery.hk ✅] 期數：{draw_no_text}，日期：{draw_date}，號碼：{nums}")
        return {
            "draw_no":   draw_no_text,
            "draw_date": draw_date,
            "numbers":   nums[:6],   # 正碼（lottery.hk 已按升序排列）
            "extra":     nums[6],    # 特別號碼（最後一個）
            "source":    "lottery.hk",
        }

    print("[lottery.hk] 解析唔到任何有效結果行")
    return None


def is_draw_today(result: dict) -> bool:
    """確認結果係今日嘅開彩"""
    today = date.today().strftime("%Y-%m-%d")
    return result["draw_date"] == today


# ============================================================
# 重複發送防護
# ============================================================

SENT_FILE = "sent_marksix_results.json"

def load_sent() -> set:
    if not os.path.exists(SENT_FILE):
        return set()
    try:
        with open(SENT_FILE) as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_sent(key: str):
    records = load_sent()
    records.add(key)
    with open(SENT_FILE, "w") as f:
        json.dump(list(records), f)

def record_key(result: dict) -> str:
    nums_str = "-".join(str(n) for n in result["numbers"])
    return f"{result['draw_no']}_{nums_str}+{result['extra']}"


# ============================================================
# Telegram 發送
# ============================================================

def send_telegram(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[❌] 未設定 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       message,
            "parse_mode": "HTML",
        }, timeout=10)
        resp.raise_for_status()
        print("[✅] Telegram 訊息發送成功")
        return True
    except Exception as e:
        print(f"[❌] Telegram 發送失敗：{e}")
        return False


def format_message(result: dict) -> str:
    nums_str  = "  ".join(fmt_num(n) for n in result["numbers"])
    extra_str = fmt_num(result["extra"], is_extra=True)

    return "\n".join([
        "🎱 <b>香港六合彩開彩結果</b>",
        f"📋 <b>期數：</b>第 {result['draw_no']} 期",
        f"📅 <b>日期：</b>{result['draw_date']}",
        "━━━━━━━━━━━━━━━━━━",
        "<b>正碼：</b>",
        f"   {nums_str}",
        f"<b>特別號碼：</b>{extra_str}",
        "━━━━━━━━━━━━━━━━━━",
        "🔗 <a href='https://lottery.hk/en/mark-six/results/'>查看完整賽果</a>  |  "
        "<a href='https://bet.hkjc.com/marksix/'>HKJC 官網</a>",
    ])


# ============================================================
# 主程式
# ============================================================

def main():
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] 抓取最新六合彩結果...")

    result = fetch_latest_result()

    if not result:
        print("ℹ️  無法取得開彩結果")
        return

    # 只發送今日嘅結果
    if not is_draw_today(result):
        print(f"ℹ️  最新結果係 {result['draw_date']}，唔係今日，跳過。")
        return

    sent = load_sent()
    key  = record_key(result)

    if key in sent:
        print(f"ℹ️  第 {result['draw_no']} 期結果已發送過，跳過。")
        return

    msg = format_message(result)
    print(msg)

    if send_telegram(msg):
        save_sent(key)


if __name__ == "__main__":
    main()
