# 🏇 香港賽馬 Triple Trio（三T）自動 Telegram 通知

自動抓取 HKJC **Triple Trio（三T）** 賽果，透過 GitHub Actions 定時執行，結果一出即時通知 Telegram。

> ⚠️ 注意：呢個係 **Triple Trio（三T）** bot，即係三場指定賽事、每場頭三名嘅串關彩池。
> 唔係三重彩（Trio / 單場頭三名）。

---

## 🎯 Triple Trio（三T）係咩？

| | Triple Trio（三T） | Trio（三重彩） |
|---|---|---|
| 賽事數量 | **三場**指定賽事 | 單場 |
| 玩法 | 每場選頭三名（次序不拘），**三場全中** | 單場頭三名 |
| 獎池 | 滾存式，可累積至過億 | 固定派彩 |

---

## 📱 Telegram 通知格式

```
🏇 香港賽馬 Triple Trio（三T）結果
📅 日期：2026/04/02
━━━━━━━━━━━━━━━━━━
🎯 Triple Trio (三T)
   第1關：🐎 3 / 7 / 11
   第2關：🐎 1 / 5 / 9
   第3關：🐎 2 / 6 / 10
   💰 賠率：HK$234,567（投注單位：HK$10）
━━━━━━━━━━━━━━━━━━
🔗 HKJC 賽果頁面
```

如果無人中：
```
🔄 今日三T無人中！獎池滾存落下次賽事。
```

---

## 🚀 部署步驟

### 第一步：Fork 呢個 Repo
點擊右上角 **Fork**。

### 第二步：設定 GitHub Secrets
```
Settings → Secrets and variables → Actions → New repository secret
```

| Secret 名稱 | 內容 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | 你嘅 Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | 你嘅 Telegram Chat ID |

### 第三步：啟用 Actions
```
Actions → Enable workflows
```

### 第四步：測試手動執行
```
Actions → 🏇 Triple Trio (三T) 自動通知 → Run workflow
```

---

## ⏰ 執行時間

每 **15 分鐘**喺 **HKT 14:00–23:00** 自動執行（即賽馬時段全程監察）。

- 沙田日賽三T通常約下午 **5–6 時**結算
- 快活谷夜賽三T通常約晚上 **10–11 時**結算

---

## 📁 文件結構

```
├── .github/
│   └── workflows/
│       └── hkjc_tt.yml           # GitHub Actions 定時執行
├── hkjc_tt_telegram.py           # 主腳本
├── requirements.txt
└── README.md
```
