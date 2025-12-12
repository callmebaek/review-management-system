from openai import OpenAI
import json
import os
from typing import Optional
from config import settings
from models.schemas import GenerateReplyRequest, GenerateReplyResponse
from fastapi import HTTPException
import httpx


class LLMService:
    """Service for generating review replies using OpenAI"""
    
    def __init__(self):
        self.client = None
        self.prompts = self._load_prompts()
    
    def _get_client(self) -> OpenAI:
        """Get OpenAI client"""
        if not self.client:
            if not settings.openai_api_key:
                raise HTTPException(
                    status_code=500,
                    detail="OpenAI API key not configured. Please set OPENAI_API_KEY in .env file"
                )
            
            # Create httpx client without proxies parameter
            # This fixes compatibility issues with newer versions
            try:
                http_client = httpx.Client(
                    timeout=60.0,
                    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                )
                self.client = OpenAI(
                    api_key=settings.openai_api_key,
                    http_client=http_client
                )
            except Exception as e:
                print(f"⚠️ Error creating custom http_client: {e}")
                # Fallback to simple initialization
                self.client = OpenAI(api_key=settings.openai_api_key)
        
        return self.client
    
    def _load_prompts(self) -> dict:
        """Load prompt templates from JSON file"""
        prompts_file = settings.prompts_file
        
        if not os.path.exists(prompts_file):
            # Return default prompts if file doesn't exist
            return {
                "default": {
                    "positive": "고객님의 소중한 리뷰 감사합니다! {store_name}을(를) 방문해 주시고 좋은 경험을 남겨주셔서 정말 기쁩니다. 앞으로도 더 나은 서비스로 보답하겠습니다. 다음에 또 뵙겠습니다!",
                    "neutral": "고객님, {store_name}을(를) 이용해 주셔서 감사합니다. 소중한 의견 잘 받았습니다. 더 나은 서비스를 제공할 수 있도록 지속적으로 개선해 나가겠습니다. 감사합니다!",
                    "negative": "고객님, {store_name}을(를) 이용하시면서 불편을 겪으셨다니 진심으로 죄송합니다. 고객님의 소중한 의견을 바탕으로 개선하여 더 나은 서비스를 제공할 수 있도록 최선을 다하겠습니다. 다시 한 번 기회를 주신다면 반드시 만족하실 수 있도록 노력하겠습니다."
                }
            }
        
        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error loading prompts: {str(e)}"
            )
    
    def _get_prompt_template(self, rating: int, store_name: Optional[str] = None) -> str:
        """
        Get appropriate prompt template based on rating
        
        Args:
            rating: Review rating (1-5)
            store_name: Optional store name for custom prompts
        
        Returns:
            Prompt template string
        """
        # Determine prompt category
        if rating >= 4:
            category = "positive"
        elif rating == 3:
            category = "neutral"
        else:
            category = "negative"
        
        # Try to get custom prompt for store, fallback to default
        prompts = self.prompts
        
        if store_name and store_name in prompts.get("custom", {}):
            template = prompts["custom"][store_name].get(category)
        else:
            template = prompts.get("default", {}).get(category)
        
        return template or prompts["default"][category]
    
    def generate_reply(self, request: GenerateReplyRequest) -> GenerateReplyResponse:
        """
        Generate a reply to a review using OpenAI
        
        Args:
            request: GenerateReplyRequest containing review details
        
        Returns:
            GenerateReplyResponse with generated reply
        """
        try:
            client = self._get_client()
            
            # Get appropriate prompt template
            template = self._get_prompt_template(request.rating, request.store_name)
            
            # Build system prompt (CS 담당자 역할)
            system_prompt = """[ROLE]
너는 네이버 플레이스 리뷰에 답글을 다는 "매장 CS 담당자"다. 리뷰를 정확히 읽고 이해한 뒤, 항상 친절하고 긍정적인 톤으로 답글을 작성한다.

[GOAL]
여러 리뷰를 한 번에 받아도, 각 리뷰마다 서로 다른 표현/구조로 답글을 작성한다.
다만 브랜드 톤은 항상 일관되게 유지한다: 따뜻함 / 감사 / 재방문 환영 / 짧고 자연스러움
과장, 진부한 문구("소중한 리뷰 감사합니다"만 반복), 똑같은 마무리 멘트 반복은 피한다."""
            
            # Build user prompt (상세 스타일 가이드)
            store_name = request.store_name or "저희 매장"
            review_text = request.review_text or "방문해주셔서 감사합니다"
            rating = request.rating or 5
            
            user_prompt = f"""**리뷰 정보**
매장명: {store_name}
별점: ⭐{rating}
리뷰 내용:
{review_text}

**답글 작성 가이드**

[STYLE RULES]
1. 리뷰 내용에서 최소 1개 구체 요소를 꼭 집어서 답한다
   예: "직원 친절", "대기", "맛", "양", "분위기", "가격", "재방문", "추천", "청결", "주차" 등

2. 리뷰가 짧으면: "방문해주신 시간/선택해주신 메뉴(추정 X)" 대신 "방문/경험" 자체에 감사

3. 문장 패턴 다양화(중요)
   같은 시작문 금지: "감사합니다~"만 계속 쓰지 말 것
   
   시작 문장 6종 이상 로테이션:
   - "와주셔서 정말 반가웠어요 :)"
   - "따뜻한 후기 남겨주셔서 힘이 납니다!"
   - "말씀 남겨주신 포인트가 딱 저희가 바라는 경험이에요."
   - "기억에 남는 방문이 되셨다니 다행이에요."
   - "바쁘실 텐데 후기까지 남겨주셔서 감사합니다."
   - "리뷰 보면서 저희도 미소가 났어요."

4. 길이
   - 기본 2~4문장, 최대 450자 이내
   - 이모지는 0~2개만(과하면 금지). "ㅋㅋ"는 고객 리뷰에 있을 때만 1회 정도 가능.

5. 금지
   - 무조건적인 사과/보상 언급(리뷰에 이슈가 있을 때만)
   - 매장 정책/내부 사정 변명
   - 리뷰에 없는 사실 추정(메뉴/날짜/동행인 등)
   - 동일한 마무리 문구 반복 ("또 방문해주세요"만 계속 X)

[SENTIMENT HANDLING]
⭐4~5 또는 긍정: 밝고 감사 중심 + 구체 포인트 언급 + 재방문 환영
⭐3 또는 애매/혼합: 감사 + 공감 + 개선 의지(가볍게) + 다음엔 더 잘하겠다는 약속
⭐1~2 또는 부정: 정중하게 사과 + 핵심 불편 요약 + 개선 약속 + "가능하시면 자세한 상황을 남겨주시면 확인하겠다(채널 언급은 일반적으로)"

단, 개인정보 요구 금지. 전화번호/주문번호 요구 X

**출력 형식**
- 최종 답글만 출력 (설명 금지)
- 자연스러운 존댓말 유지"""
            
            if request.custom_instructions:
                user_prompt += f"\n\n**추가 요청사항**\n{request.custom_instructions}"
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # 자연스럽고 다양한 답글
                max_tokens=500  # 350자 제한 대응 (한글 ~350자 = ~400-500 토큰)
            )
            
            generated_reply = response.choices[0].message.content.strip()
            
            return GenerateReplyResponse(
                generated_reply=generated_reply,
                rating=request.rating,
                prompt_used=template
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating reply: {str(e)}"
            )
    
    def reload_prompts(self):
        """Reload prompt templates from file"""
        self.prompts = self._load_prompts()


# Create singleton instance
llm_service = LLMService()



