import requests

def test_telegram():
    token = '你的_BOT_TOKEN'
    chat_id = '你的_CHAT_ID'
    message = "測試：六合彩程式運行中，但目前抓取官方 JSON 失敗。"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    
    try:
        response = requests.post(url, data=payload)
        print(response.json()) # 查看 Telegram 回傳的錯誤訊息
    except Exception as e:
        print(f"發送失敗: {e}")

test_telegram()
