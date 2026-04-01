#!/usr/bin/env python3
"""
香港六合彩（Mark Six）結果自動通知 Telegram
支援 GitHub Actions 定時執行

開彩時間：逢星期二、四、及非賽馬日嘅星期六或日，晚上 9:30
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import re

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
    "Referer": "https://bet.hkjc.com/",
    "Accept-Language": "zh-HK,zh;q=0.9",
}

# 號碼對應顏色（六合彩傳統色）
NUMBER_COLORS = {
    range(1, 8):   "🔴",  # 紅
    range(8, 15):  "🔵",  # 藍
    range(15, 24): "🟢",  # 綠
    range(24, 32): "🟠",  # 橙
    range(32, 40): "🟣",  # 紫
    range(40, 50): "⚪",  # 白
}

def get_color(num: int) -> str:
    for r, color in NUMBER_COLORS.items():
        if num in r:
            return color
    return "⚫"

def format_number(num: int, is_extra: bool = False) -> str:
    color = get_color(num)
    n = f"{num:02d}"
    return f"{color}{n}" if not is_extra else f"✨{color}{n}"


# ============================================================
# 抓取六合彩結果
# ============================================================

def fetch_marksix_result() -> dict | None:
    """
    嘗試多個來源抓取最新六合彩結果。
    回傳 dict 或 None。
    """
    result = fetch_via_hkjc_api()
    if result:
        return result

    result = fetch_via_hkjc_html()
    if result:
        return result

    return None


def fetch_via_hkjc_api() -> dict | None:
    """
    方法一：HKJC 官方 API（最可靠）
    """
    url = "https://bet.hkjc.com/marksix/getResults.aspx?lang=ch"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # 解析最新一期
        draw = data[0] if isinstance(data, list) and data else data
        draw_no    = draw.get("drawNo", "?")
        draw_date  = draw.get("drawDate", "?")
        numbers    = draw.get("drawResults", [])      # 正碼 list
        extra      = draw.get("extraNumber", None)    # 特別號碼
        jackpot    = draw.get("jackpot", None)
        prize_1    = draw.get("unitPrize1", None)

        if not numbers:
            return None

        return {
            "draw_no":   draw_no,
            "draw_date": draw_date,
            "numbers":   [int(n) for n in numbers],
            "extra":     int(extra) if extra else None,
            "jackpot":   jackpot,
            "prize_1":   prize_1,
            "source":    "HKJC API",
        }
    except Exception as e:
        print(f"[API] 失敗：{e}")
        return None


def fetch_via_hkjc_html() -> dict | None:
    """
    方法二：抓 HKJC 六合彩結果頁面
    """
    url = "https://bet.hkjc.com/marksix/Results.aspx?lang=ch"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[HTML] 連接失敗：{e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # 搵開彩號碼
    number_els = soup.select(".ball-red, .ball-blue, .ball-green, .ball-number, [class*='ball']")
    numbers = []
    extra = None

    for i, el in enumerate(number_els):
        txt = el.get_text(strip=True)
        if txt.isdigit():
            num = int(txt)
            if i < 6:
                numbers.append(num)
            elif i == 6:
                extra = num

    if not numbers:
        # 嘗試用 regex 搵號碼
        text = soup.get_text()
        matches = re.findall(r'\b([0-4]?\d)\b', text)
        nums = [int(m) for m in matches if 1 <= int(m) <= 49]
        numbers = nums[:6] if len(nums) >= 6 else []
        extra = nums[6] if len(nums) > 6 else None

    # 搵期數
    draw_no_el = soup.select_one("[class*='drawNo'], [class*='draw-no']")
    draw_no = draw_no_el.get_text(strip=True) if draw_no_el else "?"

    if not numbers:
        return None

    return {
        "draw_no":   draw_no,
        "draw_date": datetime.now().strftime("%Y-%m-%d"),
        "numbers":   numbers,
        "extra":     extra,
        "jackpot":   None,
        "prize_1":   None,
        "source":    "HKJC HTML",
    }


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
    return f"{result['draw_no']}_{'-'.join(str(n) for n in result['numbers'])}"


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
    nums_str = "  ".join(format_number(n) for n in result["numbers"])
    extra_str = format_number(result["extra"], is_extra=True) if result["extra"] else "未知"

    lines = [
        "🎱 <b>香港六合彩開彩結果</b>",
        f"📋 <b>期數：</b>第 {result['draw_no']} 期",
        f"📅 <b>日期：</b>{result['draw_date']}",
        "━━━━━━━━━━━━━━━━━━",
        f"🔢 <b>正碼：</b>",
        f"   {nums_str}",
        f"✨ <b>特別號碼：</b>{extra_str}",
    ]

    if result.get("jackpot"):
        lines.append(f"💰 <b>頭獎獎池：</b>HK${result['jackpot']:,}")
    if result.get("prize_1"):
        lines.append(f"🥇 <b>頭獎單注：</b>HK${result['prize_1']:,}")

    lines += [
        "━━━━━━━━━━━━━━━━━━",
        "🔗 <a href='https://bet.hkjc.com/marksix/Results.aspx?lang=ch'>HKJC 六合彩官網</a>",
    ]

    return "\n".join(lines)


# ============================================================
# 主程式
# ============================================================

def main():
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] 抓取最新六合彩結果...")

    result = fetch_marksix_result()

    if not result:
        print("ℹ️  暫時未有開彩結果（今晚可能未開彩或非開彩日）")
        return

    sent = load_sent()
    key = record_key(result)

    if key in sent:
        print(f"ℹ️  第 {result['draw_no']} 期結果已發送過，跳過。")
        return

    msg = format_message(result)
    print(msg)

    if send_telegram(msg):
        save_sent(key)


if __name__ == "__main__":
    main()
