# 🎱 香港六合彩自動 Telegram 通知

自動抓取 HKJC 最新六合彩開彩結果，透過 GitHub Actions 定時執行，開彩後即時通知你的 Telegram。

**完全免費，唔需要自己嘅伺服器！**

---

## 📱 Telegram 通知格式

```
🎱 香港六合彩開彩結果
📋 期數：第 26/026 期
📅 日期：2026-04-01
━━━━━━━━━━━━━━━━━━
🔢 正碼：
   🔴07  🟢18  🟠27  🟣35  ⚪42  🔵12
✨ 特別號碼：✨🟢22
━━━━━━━━━━━━━━━━━━
🔗 HKJC 六合彩官網
```

---

## 🚀 部署步驟

### 第一步：Fork 呢個 Repo
點擊右上角 **Fork** 按鈕。

### 第二步：設定 GitHub Secrets
```
Settings → Secrets and variables → Actions → New repository secret
```

| Secret 名稱 | 內容 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | 你嘅 Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | 你嘅 Telegram Chat ID |

> **點搵 Bot Token？** Telegram 搵 @BotFather → `/newbot`
>
> **點搵 Chat ID？** 瀏覽器打開：`https://api.telegram.org/bot<TOKEN>/getUpdates`，搵 `"chat":{"id":...}`

### 第三步：啟用 Actions
```
Actions → Enable workflows
```

### 第四步：測試
```
Actions → 🎱 六合彩自動通知 → Run workflow
```

---

## ⏰ 執行時間

GitHub Actions 會喺以下時間自動執行（HKT）：

| 時間 | 說明 |
|---|---|
| 晚上 9:30 | 開彩後即時檢查 |
| 晚上 9:45 | 補檢（如結果未更新）|
| 晚上 10:00 | 再補檢 |
| 晚上 10:15 | 最後補檢 |

執行日：**星期二、四、六、日**

---

## 🏇 同時用六合彩 + 賽馬三重彩通知？

如果你同時想收三重彩通知，可以喺同一個 repo 加入 [hkjc-3t-bot](https://github.com/你的用戶名/hkjc-3t-bot) 嘅文件，兩個 workflow 可以共用同一個 `TELEGRAM_BOT_TOKEN` 同 `TELEGRAM_CHAT_ID`。

---

## 📁 文件結構

```
├── .github/
│   └── workflows/
│       └── hkjc_marksix.yml      # GitHub Actions 定時執行
├── hkjc_marksix_telegram.py      # 主腳本
├── requirements.txt               # Python 依賴
└── README.md
```
