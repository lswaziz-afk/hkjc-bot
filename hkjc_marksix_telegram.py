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
    依次嘗試三個來源抓取最新六合彩結果。
    回傳 dict 或 None。
    """
    # 方法一：kclm.site 第三方 JSON API（最穩定，有真實 JSON 回應）
    result = fetch_via_kclm_api()
    if result:
        return result

    # 方法二：HKJC 官方靜態 HTML 結果頁
    result = fetch_via_hkjc_static_html()
    if result:
        return result

    # 方法三：yelo.hk 備用抓取
    result = fetch_via_yelo()
    if result:
        return result

    return None


def fetch_via_kclm_api() -> dict | None:
    """
    方法一：kclm.site 第三方 JSON API
    回傳格式：{"issue":"24032","drawResult":"20,06,34,39,42,19,44",
               "drawTime":"2024-03-21 21:35:20","code":"hk6"}
    """
    url = "https://kclm.site/api/trial/drawResult?code=hk6&format=json&rows=1"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        # 確認有真正嘅 JSON 內容
        text = resp.text.strip()
        if not text or text[0] not in ('{', '['):
            print(f"[kclm API] 回應唔係 JSON：{text[:80]}")
            return None

        data = resp.json()

        # 支援回傳 list 或 dict
        item = data[0] if isinstance(data, list) and data else data
        if not item:
            return None

        draw_result = item.get("drawResult", "") or item.get("openCode", "")
        if not draw_result:
            return None

        nums = [int(n.strip()) for n in draw_result.split(",") if n.strip().isdigit()]
        if len(nums) < 7:
            print(f"[kclm API] 號碼不足：{nums}")
            return None

        draw_time = item.get("drawTime", "") or item.get("openTime", "")
        draw_date = draw_time[:10] if draw_time else datetime.now().strftime("%Y-%m-%d")
        draw_no   = str(item.get("issue", "?"))

        print(f"[kclm API ✅] 第 {draw_no} 期，號碼：{nums}")
        return {
            "draw_no":   draw_no,
            "draw_date": draw_date,
            "numbers":   nums[:6],
            "extra":     nums[6],
            "jackpot":   None,
            "prize_1":   None,
            "source":    "kclm API",
        }
    except Exception as e:
        print(f"[kclm API] 失敗：{e}")
        return None


def fetch_via_hkjc_static_html() -> dict | None:
    """
    方法二：抓 HKJC 官方靜態賽果頁面（非 SPA 版本）
    """
    url = "https://special.hkjc.com/marksix/result/last2draw.aspx?lang=ch"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[HKJC HTML] 連接失敗：{e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator=" ")

    # 搵七個 1-49 之間嘅號碼（六正碼 + 一特別）
    # 用 regex 搵連續嘅數字，過濾雜訊
    candidates = re.findall(r'\b([0-4]?\d)\b', text)
    nums = []
    for c in candidates:
        n = int(c)
        if 1 <= n <= 49 and n not in nums:
            nums.append(n)
        if len(nums) == 7:
            break

    if len(nums) < 7:
        print(f"[HKJC HTML] 搵唔夠 7 個號碼，只搵到：{nums}")
        return None

    # 搵期數：格式通常係 XX/XXX 或純數字
    draw_no_match = re.search(r'\b(\d{2}/\d{3}|\d{5,6})\b', text)
    draw_no = draw_no_match.group(1) if draw_no_match else "?"

    print(f"[HKJC HTML ✅] 期數：{draw_no}，號碼：{nums}")
    return {
        "draw_no":   draw_no,
        "draw_date": datetime.now().strftime("%Y-%m-%d"),
        "numbers":   nums[:6],
        "extra":     nums[6],
        "jackpot":   None,
        "prize_1":   None,
        "source":    "HKJC HTML",
    }


def fetch_via_yelo() -> dict | None:
    """
    方法三：yelo.hk 備用抓取（有清晰 HTML 結構）
    """
    url = "https://www.yelo.hk/lottery/mark-six-result-today"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[yelo] 連接失敗：{e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # 搵號碼球
    ball_els = soup.select(".ball, .lottery-ball, [class*='number'], [class*='ball']")
    nums = []
    for el in ball_els:
        t = el.get_text(strip=True)
        if t.isdigit() and 1 <= int(t) <= 49:
            nums.append(int(t))
        if len(nums) == 7:
            break

    if len(nums) < 7:
        # regex fallback
        text = soup.get_text()
        candidates = re.findall(r'\b([0-4]?\d)\b', text)
        for c in candidates:
            n = int(c)
            if 1 <= n <= 49 and n not in nums:
                nums.append(n)
            if len(nums) == 7:
                break

    if len(nums) < 7:
        print(f"[yelo] 搵唔夠 7 個號碼")
        return None

    # 搵期數
    text = soup.get_text()
    draw_no_match = re.search(r'Draw\s*#?\s*(\d+)|第\s*(\d+)\s*期', text, re.IGNORECASE)
    draw_no = (draw_no_match.group(1) or draw_no_match.group(2)) if draw_no_match else "?"

    # 搵日期
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    draw_date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")

    print(f"[yelo ✅] 期數：{draw_no}，號碼：{nums}")
    return {
        "draw_no":   draw_no,
        "draw_date": draw_date,
        "numbers":   nums[:6],
        "extra":     nums[6],
        "jackpot":   None,
        "prize_1":   None,
        "source":    "yelo.hk",
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
