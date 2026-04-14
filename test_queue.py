import time
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# 가상 데이터 셋업 (인덱스 0이 가장 최신 공지)
all_events_on_website = [
    {"id": "new_5", "title": "신규 이벤트 5"},
    {"id": "new_4", "title": "신규 이벤트 4"},
    {"id": "new_3", "title": "신규 이벤트 3"},
    {"id": "new_2", "title": "신규 이벤트 2"},
    {"id": "new_1", "title": "신규 이벤트 1"},
    {"id": "old_5", "title": "기존 이벤트 5"},
    {"id": "old_4", "title": "기존 이벤트 4"},
    {"id": "old_3", "title": "기존 이벤트 3"},
    {"id": "old_2", "title": "기존 이벤트 2"},
    {"id": "old_1", "title": "기존 이벤트 1"},
]

# 이미 DB에 저장되어 있는 이벤트들
known_ids = {"old_1", "old_2", "old_3", "old_4", "old_5"}

logger.info("=== 봇 시뮬레이션 시작 ===")
logger.info(f"현재 웹사이트 이벤트 개수: {len(all_events_on_website)}개")
logger.info(f"DB에 이미 저장된 이벤트 개수: {len(known_ids)}개\n")

for minute in range(1, 8):
    logger.info(f"--- [ {minute}분 째 크롤러 실행 ] ---")
    events = all_events_on_website
    
    # 캐시에 없는 이벤트만 필터링
    new_events = [e for e in events if e['id'] not in known_ids]
    
    if new_events:
        event_to_process = new_events[-1]
        logger.info(f"발견된 새 이벤트: {len(new_events)}개. 도배 방지를 위해 딱 1개만 먼저 처리 대기열에 올립니다.")
        logger.info(f">>> [디스코드 발송!] {event_to_process['title']} 요약 발송 완료")
        
        # 캐시에 방금 보낸 1개만 추가
        known_ids.add(event_to_process['id'])
    else:
        logger.info("새로운 이벤트가 없습니다. 대기합니다.")
        # 옛날 이벤트 정리
        current_event_ids = {e['id'] for e in events}
        known_ids = known_ids.intersection(current_event_ids)
        
    logger.info("")
