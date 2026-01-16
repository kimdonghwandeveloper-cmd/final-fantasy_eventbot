# FF14 Event Bot 코드 설명서

이 문서는 유지보수를 위해 프로젝트의 코드 구조와 핵심 로직을 상세히 설명합니다.

## 📂 프로젝트 구조

```text
final-fantasy_eventbot/
├── src/final_fantasy_eventbot/
│   └── main.py          # 메인 실행 파일 (모든 핵심 로직 포함)
├── .env                 # 환경 변수 (웹훅 URL 등 민감 정보)
├── latest_event.json    # 상태 저장 파일 (마지막 이벤트 ID)
├── pyproject.toml       # 프로젝트 의존성 및 설정 관리 (uv)
└── README.md            # 프로젝트 개요
```

## 📝 핵심 로직 (`main.py`)

### 1. 설정 및 상수 정의
맨 윗부분에 `TARGET_URL`, `LATEST_EVENT_FILE` 등 상수를 정의하여, 나중에 URL이 바뀌거나 파일명이 바뀌었을 때 쉽게 수정할 수 있도록 했습니다.

### 2. 함수 설명

#### `fetch_events()`
- **역할**: 웹사이트에서 HTML을 가져와 파싱합니다.
- **주요 로직**:
  - `requests`로 페이지 요청 (User-Agent 헤더 필수).
  - `BeautifulSoup`으로 HTML 파싱.
  - **CSS Selector**: `.banner_list.event li`를 사용하여 이벤트 배너 목록을 정확히 타겟팅합니다.
  - **데이터 정제**: 상대 경로 URL(`//...`)을 절대 경로(`https://...`)로 변환하고, 쿼리 파라미터를 제거하여 순수한 ID를 추출합니다.

#### `crawling_job(is_startup=False)`
- **역할**: 주기적으로 실행되는 작업 단위입니다.
- **작동 방식**:
  1. **랜덤 지연**: 기계적인 패턴을 숨기기 위해 1~3초 대기.
  2. **수집**: `fetch_events()` 호출.
  3. **비교**: `latest_event.json`에 저장된 ID와 비교.
  4. **알림**: 저장된 ID보다 최신인 글들만 골라내어 디스코드 웹훅 전송.
  5. **상태 업데이트**: 알림 전송 후 즉시 `save_latest_event()`로 저장하여 중복 방지.
- **Startup 모드**: `is_startup=True`인 경우, 비교 로직 전에 "현재 진행 중인 이벤트 요약"을 전송합니다.

#### `start_discord_webhook(event)` & `send_summary_webhook(events)`
- **역할**: 디스코드 웹훅 포맷에 맞춰 JSON 페이로드를 구성하고 `POST` 요청을 보냅니다.
- `embeds`를 사용하여 깔끔한 카드(이미지, 제목, 링크 포함) 형태로 전송합니다.

### 3. 스케줄링 및 실행 (`main()`)
- `schedule` 라이브러리를 사용하여 1분 간격으로 `crawling_job`을 실행합니다.
- `argparse`를 통해 CLI 옵션(`--summary`)을 처리합니다.
- 무한 루프(`while True`)로 프로그램이 계속 실행되도록 유지하며, 예외 발생 시 프로그램이 꺼지지 않고 로그를 남기고 재시도하도록 안전장치를 두었습니다.

## 💡 유지보수 팁
- **사이트 구조 변경 시**: `fetch_events` 함수 내의 `soup.select(...)` 부분만 수정하면 됩니다.
- **알림 디자인 변경 시**: `send_discord_webhook` 함수 내의 `embed` 딕셔너리를 수정하세요.
- **실행 주기 변경 시**: `main()` 함수 내의 `schedule.every(1).minutes...` 숫자를 변경하세요.
