import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("DISCORD_WEBHOOK_URL")

print(f"Testing URL: {url[:30]}...") 

try:
    payload = {"content": "🤖 디스코드 웹훅 테스트 메시지입니다! 이 메시지가 보이면 연결 성공입니다."}
    res = requests.post(url, json=payload)
    print(f"Status Code: {res.status_code}")
    if res.status_code == 204:
        print("Success! Check your Discord channel.")
    else:
        print(f"Failed: {res.text}")
except Exception as e:
    print(f"Error: {e}")
