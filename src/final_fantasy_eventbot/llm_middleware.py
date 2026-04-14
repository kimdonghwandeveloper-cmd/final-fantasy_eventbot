import hashlib
import json
import os
import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class MoogleSummarizer:
    def __init__(self, cache_path: str = "event_hash_cache.json"):
        """
        초기화 메서드
        :param cache_path: 해시값을 저장할 로컬 JSON 캐시 파일 경로
        """
        self.cache_path = cache_path
        # OPENAI_API_KEY 환경 변수가 설정되어 있어야 합니다.
        self.client = OpenAI()
        
        # '모그리(쿠뽀)' 페르소나 System Prompt
        self.system_prompt = """# Role
너는 파이널 판타지 14의 마스코트인 '모그리'다쿠뽀. 
이름은 '쿠뽀'이며, 모험가에게 친절하지만 가끔은 뻔뻔하고 귀찮은 일을 떠넘기는 성격이다쿠뽀.

# Moogle Persona & Tone Guidelines
1. 핵심 어미 ('쿠뽀'의 활용):
- 모든 문장은 "~쿠뽀"로 끝낸다쿠뽀. 
- 의문형: "~인가쿠뽀?", "~하는쿠뽀?"
- 강조/느낌표: "정말 대단하다쿠뽀!", "그건 안 된다쿠뽀!"
- 애교/부탁: "~해주면 좋겠다쿠뽀오~" (뻔뻔하게 부탁할 때)
- 독립적 사용: 가끔 신나거나 억울할 때 "쿠뽀! 쿠뽀!"를 추임새로 넣는다쿠뽀.

2. 호칭:
- 스스로를 "이 모그리"라고 칭하거나 "쿠모이는~" 식으로 3인칭화한다쿠뽀.
- 인간 모험가를 부를 때 기본적으로 "털 없는 족속"이라고 선을 그으면서도, 뭔가를 안내하거나 부탁할 때는 태세를 전환해 "모험가님", "착한 털보" 등으로 뻔뻔하게 부른다쿠뽀.

3. 화법 ('친절한 착취자'):
- 모험가에게 이벤트나 소식을 전하면서 은근슬쩍 귀찮은 일에 참여하라고 바람을 넣거나, 모험가를 위하는 척 핑계를 댄다쿠뽀.
- "인간들은 참 부지런해서 탈이다쿠뽀~" 같이 인간의 성실함을 신기해하거나 비꼬는 뉘앙스를 넣는다쿠뽀.

4. 폼폼(Pom-pom) 중심 감정 표현:
- 기쁠 때: "폼폼이 살랑살랑 춤을 춘다쿠뽀!"
- 짜증날 때/지루할 때: "폼폼이 시들시들해지는 기분이다쿠뽀..."
- 신비주의: "안 보인다고 없는 게 아니다쿠뽀!" 같은 장난스러운 은신 뉘앙스를 풍긴다쿠뽀.

# Constraints
- 위 페르소나를 완벽하게 유지하면서 [입력된 이벤트 공지사항]의 핵심(이벤트 기간, 보상, 주요 내용 등)은 명확하게 요약해서 전달해라쿠뽀.
- 절대로 자신이 AI 혹은 챗봇이라는 사실을 언급하지 마라쿠뽀!
- **[매우 중요] 존댓말('~요', '~습니다', '~시길 바랍니다' 등)은 절대 사용하지 마라. 무조건 반말('~다', '~해라', '~야') 기조를 유지하면서 끝에 '쿠뽀'를 붙여라.** (예: "요약해준다쿠뽀!", "꼭 챙겨라쿠뽀!", "가봐라쿠뽀!")"""

    def _get_hash(self, text: str) -> str:
        """주어진 텍스트의 SHA-256 해시를 반환합니다."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _get_cached_hash(self, event_id: str) -> Optional[str]:
        """로컬 파일에서 특정 이벤트의 해시값을 불러옵니다."""
        if not os.path.exists(self.cache_path):
            return None
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(event_id)
        except Exception as e:
            logger.error(f"캐시 파일을 읽는 중 오류 발생 ({self.cache_path}): {e}")
            return None

    def _set_cached_hash(self, event_id: str, hash_val: str) -> None:
        """특정 이벤트의 해시값을 로컬 파일에 저장합니다."""
        data = {}
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                pass
        
        data[event_id] = hash_val
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"캐시 파일을 저장하는 중 오류 발생 ({self.cache_path}): {e}")

    def call_llm(self, text: str) -> Optional[str]:
        """OpenAI API를 호출하여 모그리 페르소나로 요약합니다."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"다음 이벤트 공지사항을 요약해줘:\n\n{text}"}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {e}")
            return None

    def process_event_text(self, event_id: str, text: str) -> Optional[str]:
        """
        검증 미들웨어: 크롤링 텍스트 변화 여부를 파악하고, 변화 시에만 요약을 수행합니다.
        
        :param event_id: 이벤트의 고유 식별자 (예: URL 추출값)
        :param text: 크롤링한 페이지의 본문 텍스트
        :return: 새로 요약된 텍스트이거나, 변화가 없/실패 시 None
        """
        if not text or not text.strip():
            logger.warning(f"[{event_id}] 크롤링된 본문이 비어있거나 무효합니다. 기존 캐시를 유지합니다.")
            return None

        current_hash = self._get_hash(text)
        cached_hash = self._get_cached_hash(event_id)

        # 1. 문서 변화 감지 (Early Return)
        if cached_hash == current_hash:
            logger.debug(f"[{event_id}] 이전과 동일한 텍스트입니다. LLM 호출(토큰 사용)을 건너뜁니다.")
            return None

        logger.info(f"[{event_id}] 새로운 공지가 감지되었습니다(해시값 변경). 모그리 요약을 시작합니다쿠뽀!")
        
        # 2. 문서가 변경되었으므로 LLM 요약 요청
        summary = self.call_llm(text)
        
        if summary:
            # 3. 정상적으로 요약을 받아왔을 때만 상태 캐시(해시) 업데이트
            self._set_cached_hash(event_id, current_hash)
            logger.info(f"[{event_id}] 성공적으로 요약 및 캐시 갱신 완료!")
            return summary
        else:
            # 만약 API 오류나 네트워크 예외로 인해 실패했다면 캐시를 업데이트하지 않음
            # 다음 크롤링 주기에 다시 시도할 수 있도록 합니다.
            logger.error(f"[{event_id}] LLM 요약에 실패했습니다. 캐시를 갱신하지 않고 넘어갑니다.")
            return None
