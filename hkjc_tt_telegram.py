#!/usr/bin/env python3
"""
香港賽馬 Triple Trio（三T）結果自動通知 Telegram
支援 GitHub Actions 定時執行

Triple Trio（三T）= 三場指定賽事，每場需選出頭三名（次序不拘）
需全中三場頭三名方可獲彩，唔中可滾存落下次
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
    "Referer": "https://racing.hkjc.com/",
    "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
}

# Triple Trio 喺 HKJC dividend API 入面嘅 betType 關鍵字
TT_BET_TYPES = {"TT", "TRIPLETRIO", "TRIPLE TRIO", "三T", "三重串"}


# ============================================================
# 抓取 Triple Trio 賽果
# ============================================================

def get_today_date_str() -> str:
    return datetime.now().strftime("%Y/%m/%d")


def fetch_tt_results(race_date: str = None) -> list:
    """
    抓取指定日期嘅 Triple Trio 結果。
    優先用官方 dividend JSON API，備用抓 HTML。
    回傳 list of dict。
    """
    if race_date is None:
        race_date = get_today_date_str()

    results = fetch_via_dividend_api(race_date)
    if not results:
        results = fetch_via_results_html(race_date)
    return results


def fetch_via_dividend_api(race_date: str) -> list:
    """
    方法一：HKJC dividend JSON API
    endpoint: /racing/data/dividend/[date]/[racecourse]
    Triple Trio 係跨場彩池，通常喺最後幾場賽事後結算
    """
    # HKJC 有兩個已知 dividend API endpoint，兩個都試
    api_date = race_date.replace("/", "-")
    urls = [
        f"https://racing.hkjc.com/racing/data/dividend/{api_date}/ST",
        f"https://racing.hkjc.com/racing/data/dividend/{api_date}/HV",
        f"https://racing.hkjc.com/racing/api/common/dividend?date={api_date}&lang=en",
    ]

    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json()
            results = parse_tt_from_json(data, race_date)
            if results:
                print(f"[API ✅] 從 {url} 搵到 Triple Trio 結果")
                return results
        except Exception as e:
            print(f"[API] {url} 失敗：{e}")

    return []


def parse_tt_from_json(data, race_date: str) -> list:
    """解析 JSON 格式，搵出 Triple Trio 相關記錄"""
    results = []

    # 支援兩種常見 JSON 結構
    if isinstance(data, list):
        races = data
    elif isinstance(data, dict):
        races = (
            data.get("races")
            or data.get("raceList")
            or data.get("dividends")
            or []
        )

    for race in races:
        race_no = race.get("raceNo") or race.get("race_no") or "?"
        dividends = race.get("dividends") or race.get("dividend") or []
        if isinstance(dividends, dict):
            dividends = [dividends]

        for div in dividends:
            bet_type = str(
                div.get("betType") or div.get("poolType") or div.get("type") or ""
            ).upper().replace(" ", "")

            # 判斷係唔係 Triple Trio
            is_tt = any(
                k.replace(" ", "") in bet_type
                for k in TT_BET_TYPES
            ) or bet_type in {"TT", "TRIPLETRIO"}

            if not is_tt:
                continue

            # 解析每個中獎組合
            combos = div.get("combinations") or div.get("winningCombinations") or []
            if not combos:
                # 有時候直接係 flat 結構
                combos = [div]

            for combo in combos:
                winning = (
                    combo.get("winningCombinations")
                    or combo.get("combinations")
                    or combo.get("horses")
                    or combo.get("selection")
                    or []
                )
                amount = (
                    combo.get("dividendAmount")
                    or combo.get("dividend")
                    or combo.get("amount")
                    or div.get("dividendAmount")
                    or "未有"
                )
                unit = combo.get("unitBet") or div.get("unitBet") or 10

                # winning 可能係 list of list（三場）或 flat list
                if winning and isinstance(winning[0], list):
                    legs = winning  # [[leg1], [leg2], [leg3]]
                else:
                    # 嘗試將 flat list 拆成三份
                    n = len(winning)
                    per_leg = n // 3 if n >= 3 else n
                    legs = [
                        winning[i * per_leg:(i + 1) * per_leg]
                        for i in range(3)
                    ] if per_leg > 0 else [winning]

                results.append({
                    "date":      race_date,
                    "type":      "Triple Trio (三T)",
                    "legs":      legs,
                    "dividend":  f"HK${amount}",
                    "unit_bet":  f"HK${unit}",
                    "jackpot":   False,
                })

    return results


def fetch_via_results_html(race_date: str) -> list:
    """
    方法二：抓 HKJC 賽果 HTML 頁面，搵 Triple Trio 區塊
    """
    url = (
        "https://racing.hkjc.com/racing/information/Chinese/Racing/ResultsAll.aspx"
        f"?RaceDate={race_date}"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[HTML] 連接失敗：{e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    # 搵含有「三T」或「Triple Trio」嘅文字節點
    keywords = ["三T", "Triple Trio", "TRIPLE TRIO", "三重串"]
    target_sections = []

    for kw in keywords:
        for node in soup.find_all(string=re.compile(kw, re.IGNORECASE)):
            parent = (
                node.find_parent("table")
                or node.find_parent("div")
                or node.find_parent("tr")
            )
            if parent and parent not in target_sections:
                target_sections.append(parent)

    for section in target_sections:
        rows = section.find_all("tr")
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            text = " ".join(cells)

            # 搵含有賠率（$）同號碼嘅行
            if "$" in text or any(kw in text for kw in keywords):
                # 嘗試提取號碼組合（格式如：1,2,3 / 4,5,6 / 7,8,9）
                number_groups = re.findall(r'[\d]+(?:[,，\s]+[\d]+)*', text)
                dividend_match = re.search(r'HK\$[\d,]+|[$＄][\d,]+', text)
                dividend = dividend_match.group(0) if dividend_match else "未有"

                if number_groups:
                    results.append({
                        "date":     race_date,
                        "type":     "Triple Trio (三T)",
                        "legs":     [g.split() for g in number_groups[:3]],
                        "raw":      text,
                        "dividend": dividend,
                        "unit_bet": "HK$10",
                        "jackpot":  False,
                    })

    # 如果完全搵唔到，檢查係咪今日無賽馬 / 三T未結算
    if not results:
        page_text = soup.get_text()
        no_race_keywords = ["沒有賽事", "No Race", "no result", "沒有結果"]
        if any(kw.lower() in page_text.lower() for kw in no_race_keywords):
            print("[HTML] 今日無賽事")
        else:
            print("[HTML] 頁面有內容但搵唔到三T結果，可能三T未結算")

    return results


def is_jackpot_carried(race_date: str) -> bool:
    """
    檢查三T係咪無人中、獎池滾存。
    喺賽果頁面搵「無人中」或「Jackpot Carried」字眼。
    """
    url = (
        "https://racing.hkjc.com/racing/information/Chinese/Racing/ResultsAll.aspx"
        f"?RaceDate={race_date}"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text()
        jackpot_keywords = ["無人中彩", "Jackpot Carried", "jackpot carried", "滾存"]
        return any(kw.lower() in text.lower() for kw in jackpot_keywords)
    except Exception:
        return False


# ============================================================
# 重複發送防護
# ============================================================

SENT_FILE = "sent_tt_results.json"

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

def record_key(r: dict) -> str:
    legs_str = str(r.get("legs", r.get("raw", "")))
    return f"{r['date']}_{legs_str}_{r['dividend']}"


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


def format_result_message(results: list, race_date: str) -> str:
    lines = [
        "🏇 <b>香港賽馬 Triple Trio（三T）結果</b>",
        f"📅 <b>日期：</b>{race_date}",
        "━━━━━━━━━━━━━━━━━━",
    ]

    for r in results:
        legs = r.get("legs", [])
        if legs:
            leg_lines = []
            for i, leg in enumerate(legs, 1):
                horses = " / ".join(str(h) for h in leg) if leg else "未知"
                leg_lines.append(f"   第{i}關：🐎 {horses}")
            legs_str = "\n".join(leg_lines)
        else:
            legs_str = f"   {r.get('raw', '未有詳情')}"

        jackpot_note = "🔄 <b>無人中，獎池滾存！</b>" if r.get("jackpot") else ""

        lines.append(
            f"🎯 <b>{r['type']}</b>\n"
            f"{legs_str}\n"
            f"   💰 賠率：{r['dividend']}（投注單位：{r['unit_bet']}）"
        )
        if jackpot_note:
            lines.append(jackpot_note)

    lines += [
        "━━━━━━━━━━━━━━━━━━",
        "🔗 <a href='https://racing.hkjc.com/racing/information/Chinese/Racing/ResultsAll.aspx'>HKJC 賽果頁面</a>",
    ]
    return "\n".join(lines)


def format_jackpot_message(race_date: str) -> str:
    return (
        "🏇 <b>香港賽馬 Triple Trio（三T）</b>\n"
        f"📅 <b>日期：</b>{race_date}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔄 <b>今日三T無人中！獎池滾存落下次賽事。</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔗 <a href='https://racing.hkjc.com/racing/information/Chinese/Racing/ResultsAll.aspx'>HKJC 賽果頁面</a>"
    )


# ============================================================
# 主程式
# ============================================================

def main():
    now = datetime.now().strftime("%H:%M:%S")
    race_date = get_today_date_str()
    print(f"[{now}] 抓取 {race_date} Triple Trio 結果...")

    results = fetch_tt_results(race_date)
    sent = load_sent()

    if results:
        new_results = [r for r in results if record_key(r) not in sent]
        if not new_results:
            print("ℹ️  三T結果已發送過，跳過。")
            return
        msg = format_result_message(new_results, race_date)
        if send_telegram(msg):
            for r in new_results:
                save_sent(record_key(r))

    else:
        # 搵唔到結果時，檢查係咪無人中滾存
        jackpot_key = f"{race_date}_jackpot"
        if jackpot_key not in sent and is_jackpot_carried(race_date):
            msg = format_jackpot_message(race_date)
            if send_telegram(msg):
                save_sent(jackpot_key)
        else:
            print("ℹ️  暫時未有三T結果（今日可能無賽馬或三T未結算）")


if __name__ == "__main__":
    main()
