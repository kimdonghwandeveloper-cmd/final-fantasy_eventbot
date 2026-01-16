# FF14 Event Bot 배포 가이드

이 봇이 24시간 작동하려면 **항상 켜져 있는 컴퓨터(서버)**가 필요합니다.
개인 PC를 계속 켜둘 수 없다면, 아래 방법 중 하나를 선택해 보세요.

## 추천 방법 1: 안 쓰는 노트북/PC 활용 (가장 쉬움)
집에 남는 노트북이나 데스크탑이 있다면 전원을 연결해두고 봇을 실행해 두는 것이 가장 간편합니다.
- **장점**: 무료, 설정이 쉬움.
- **단점**: 전기세, 장비 필요.



## 🚀 Railway 배포 가이드 (상세)

Railway는 Dockerfile을 자동으로 인식하여 배포해주는 아주 편리한 클라우드입니다.

### 1단계: GitHub에 코드 올리기
1. GitHub에 새 Repository를 만듭니다 (예: `ff14-eventbot`).
2. 현재 코드를 푸시합니다:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   # 원격 저장소 연결 (본인 주소로 변경)
   git remote add origin https://github.com/YOUR_ID/ff14-eventbot.git
   git push -u origin main
   ```

### 2단계: Railway 프로젝트 생성
1. [Railway.app](https://railway.app/)에 접속하여 GitHub 계정으로 로그인합니다.
2. **"New Project"** -> **"Deploy from GitHub repo"**를 클릭합니다.
3. 방금 올린 `ff14-eventbot` 리포지토리를 선택합니다.
4. **"Deploy Now"**를 클릭합니다.

### 3단계: 환경변수 설정 (필수!)
배포가 시작되지만, 웹훅 URL이 없어서 에러가 날 수 있습니다. 바로 설정해줍시다.
1. 방금 만든 프로젝트의 **"Settings"** 탭(또는 "Variables" 탭)으로 이동합니다.
2. **"New Variable"** 버튼을 누릅니다.
3. 다음 내용을 입력합니다:
   - **VARIABLE_NAME**: `DISCORD_WEBHOOK_URL`
   - **VALUE**: (본인의 디스코드 웹훅 주소 전체)
4. 추가(`Add`)하면 Railway가 자동으로 **재배포(Redeploy)**를 시작합니다.

### 4단계: 배포 확인
1. **"Deployments"** 탭에서 상태가 `Active` 초록색 불이 들어오는지 확인합니다.
2. **"Logs"** 탭을 클릭하여 봇이 정상적으로 시작되었는지 메시지를 확인합니다 (`Checking for new events...`).

### 💡 (선택 사항) Railway Volume 설정
Railway는 재배포 시 파일 데이터(`latest_event.json`)가 초기화됩니다.
- **기본 동작**: 재배포되면 "지금 있는 가장 최신 글"을 기준으로 다시 잡습니다. 중복 알림은 없지만, **꺼져 있던 시간 동안의 글은 놓칠 수 있습니다.**
- **영구 저장**: 이를 방지하려면 `latest_event.json`을 저장할 [Volume](https://docs.railway.app/reference/volumes)을 생성하고 마운트해야 합니다. (선택 사항)

### 💡 (참고) 무료 플랜 정책
Railway의 [Trial Plan](https://docs.railway.app/reference/pricing)이나 요금 정책을 확인하세요. $5 정도의 크레딧을 주지만 소진 시 서비스가 중단될 수 있습니다. (Oracle Free Tier와 달리 완전 평생 무료는 아닐 수 있음)


## 참고: `--once` 모드
서버리스 환경(Cron Job, GitHub Actions 등)에서 봇을 1회만 실행하고 끄고 싶다면 `--once` 옵션을 사용하세요.
```bash
uv run src/final_fantasy_eventbot/main.py --once
```

---

## 🧐 자주 묻는 질문 (FAQ)

### Q1. Docker로는 해결 못하나요?
**A. Docker만으로는 24시간 실행을 해결할 수 없습니다.**
- Docker는 "프로그램을 예쁘게 포장하는 박스"입니다.
- 이 박스(컨테이너)를 계속 실행해 줄 **장소(호스트 컴퓨터/서버)**는 여전히 필요합니다.
- **하지만!** Docker를 쓰면 클라우드 서버에 배포하기가 엄청나게 쉬워집니다. 그래서 `Dockerfile`을 만들어 두었습니다.

### Q2. 클라우드 서버는 어떤 종류가 있나요?
봇을 24시간 돌리기 위한 "컴퓨터 대여 서비스"는 크게 두 종류입니다.

1.  **VPS (가상 서버)**: 텅 빈 컴퓨터를 한 대 빌려줍니다. (예: AWS EC2, Oracle Cloud, Google Cloud)
    - **장점**: 자유도가 높음. 무료 티어(Oracle/GCP) 잘 쓰면 평생 공짜.
    - **단점**: 리눅스 명령어 등을 조금 알아야 함.
2.  **PaaS (플랫폼 서비스)**: 코드나 Docker 이미지만 주면 알아서 실행해줍니다. (예: Railway, Fly.io, Heroku)
    - **장점**: 설정이 정말 쉬움. 클릭 몇 번이면 끝.
    - **단점**: 무료 제공량이 적거나, 일정 시간 후 꺼지는 제한(Sleep)이 있을 수 있음.

### Q3. 디스코드 개발자 포털(Bot API)을 써야 하나요?
**A. 굳이 필요 없습니다.**
- **Webhook(현재 방식)**: "알림 발송"에 특화되어 있습니다. 서버가 없어도 URL만 있으면 되므로 가장 가볍고 관리가 쉽습니다.
- **Bot API**: 사용자의 채팅에 반응하거나, 대화형 기능이 필요할 때 씁니다.
    - **중요**: Bot API를 쓰더라도 **Web Socket 연결을 유지해 줄 24시간 서버가 똑같이 필요합니다.**
    - 즉, Bot으로 바꿔도 "컴퓨터를 켜놔야 한다"는 문제는 똑같습니다. 알림만 필요하다면 Webhook이 훨씬 효율적입니다.

