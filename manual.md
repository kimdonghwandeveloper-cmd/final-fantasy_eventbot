# FF14 Event Bot Walkthrough

## 개요
이 봇은 `https://www.ff14.co.kr/news/event`를 주기적으로 모니터링하여 새로운 이벤트가 감지되면 디스코드 웹훅으로 알림을 보냅니다.

## 구현 기능
- **스마트 폴링**: `User-Agent` 설정 및 랜덤 지연 시간을 통해 차단 방지.
- **실시간 감지**: 봇 시작 시 즉시 크롤링을 수행하며, 이후 1분 간격으로 체크.
- **진행 중인 이벤트 요약**: 봇이 처음 실행될 때(또는 데이터 파일이 없을 때), 현재 진행 중인 모든 이벤트를 요약하여 알림을 보냅니다. (사용자 요청 기능)
- **중복 방지**: `latest_event.json`에 마지막 이벤트 ID를 저장하여 중복 알림 방지.
- **견고성**: 네트워크 오류 발생 시 자동으로 재시도(다음 스케줄).

## 실행 방법

### 1. 환경 설정
`.env` 파일에 디스코드 웹훅 URL을 입력하세요.
```ini
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### 2. 실행 (기본)
봇을 실행하면 새로운 이벤트만 감시합니다. 기존 이벤트 알림은 보내지 않습니다.
```bash
uv run src/final_fantasy_eventbot/main.py
```

### 3. 실행 (요약 모드)
시작 시 현재 진행 중인 모든 이벤트 목록을 요약해서 받고 싶다면 `--summary` 옵션을 추가하세요.
```bash
uv run src/final_fantasy_eventbot/main.py --summary
```

### 4. 배포 (24시간 실행)
개인 PC를 계속 켜둘 수 없다면, 클라우드 서버에 배포해야 합니다.
`deployment.md` 파일에 **Railway**를 이용한 상세 배포 가이드가 있습니다.
- **Railway**: 초보자 추천 (설정 쉬움)
- **로그 확인**:
  ```
  [INFO] No previous event data found. Setting baseline.
  [INFO] Updated latest event ID to https://www.ff14.co.kr/news/event/view/710
  ```
- **데이터 파일**: `latest_event.json`이 정상적으로 생성되었습니다.

## 파일 구조
- `src/final_fantasy_eventbot/main.py`: 봇의 핵심 로직.
- `latest_event.json`: 상태 저장 파일 (자동 생성).
- `.env`: 설정 파일.
