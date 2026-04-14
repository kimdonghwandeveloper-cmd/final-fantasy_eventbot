import os
from dotenv import load_dotenv
from final_fantasy_eventbot.llm_middleware import MoogleSummarizer

def test_moogle_middleware():
    load_dotenv()
    
    print("🤖 모그리 요약기 초기화 중...")
    summarizer = MoogleSummarizer(cache_path="test_cache.json")
    
    event_id = "mock_event_2026_valentione"
    
    text_content = """
    [2026 발렌티온 데이 이벤트 안내]
    
    사랑의 전도사 리제트 드 발렌티온이 에오르제아에 찾아왔습니다!
    모험가 여러분, 사랑하는 마음을 전하고 특별한 탈것과 의상을 획득하세요.
    - 기간: 2026년 2월 14일 ~ 2026년 3월 1일
    - 제한 레벨: 레벨 15 이상
    - 수주 장소: 그리다니아 구시가지 (미 케토 야외음악당)
    - 보상: '사랑의 포옹' 감정표현, 하트 초콜릿 하우징 소품.
    
    올해는 특별히 톤베리 모양의 초콜릿 분수도 준비되어 있으니 놓치지 마세요!
    """
    
    print("-------------------------------------------------")
    print("✨ [1차 요청] LLM 요약 요청 (캐시 없으므로 무조건 실행)")
    summary_1 = summarizer.process_event_text(event_id, text_content)
    print("📝 요약 결과:")
    print(summary_1)
    
    print("-------------------------------------------------")
    print("✨ [2차 요청] 동일한 텍스트로 바로 다시 요청 (조기 종료 및 None 반환 확인)")
    summary_2 = summarizer.process_event_text(event_id, text_content)
    if summary_2 is None:
        print("✅ 성공! 변경점이 없어서 LLM 요청을 스킵(Early Return)했습니다.")
    else:
        print("❌ 실패! 캐시가 작동하지 않았습니다.")
        
    print("-------------------------------------------------")
    print("✨ [3차 요청] 내용이 추가/변경된 텍스트로 요청")
    text_content_modified = text_content + "\n\n(긴급 추가) 사보텐더 테마의 쿠키 레시피도 이벤트 교환소에 추가되었습니다!"
    summary_3 = summarizer.process_event_text(event_id, text_content_modified)
    
    if summary_3:
        print("✅ 성공! 새로운 내용이 감지되어 다시 LLM을 호출했습니다.")
        print("📝 새 요약 결과:")
        print(summary_3)
        
        # --- 디스코드 발송 테스트 ---
        print("\n-------------------------------------------------")
        print("🚀 디스코드 발송 테스트 시작...")
        
        discord_url = os.getenv("DISCORD_WEBHOOK_URL")
        if discord_url and discord_url != "your_webhook_url_here":
            from final_fantasy_eventbot.main import send_discord_webhook
            
            mock_event_data = {
                "id": event_id,
                "title": "2026 발렌티온 데이 (테스트)",
                "link": "https://www.ff14.co.kr/news/event",
                "date": "2026.02.14 ~ 2026.03.01",
                "thumbnail": "https://image.ff14.co.kr/static/path/to/mock_image.jpg",
                "summary": summary_3
            }
            
            try:
                send_discord_webhook(mock_event_data)
                print("✅ 디스코드 발송 테스트 완료! 디스코드 채널을 확인해주세요.")
            except Exception as e:
                print(f"❌ 디스코드 발송 실패: {e}")
        else:
            print("⚠️ DISCORD_WEBHOOK_URL이 설정되어 있지 않아서 발송 테스트를 스킵합니다.")
            print(".env 파일에 올바른 웹훅 URL을 넣어주시면 발송 테스트가 가능합니다!")
            
    else:
        print("❌ 실패! 내용이 바뀌었는데 LLM을 호출하지 않았습니다.")

if __name__ == "__main__":
    test_moogle_middleware()
