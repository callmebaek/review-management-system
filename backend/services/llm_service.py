from openai import OpenAI
import json
import os
from typing import Optional
from config import settings
from models.schemas import GenerateReplyRequest, GenerateReplyResponse
from fastapi import HTTPException


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
            
            # Build system prompt (전문가 버전)
            system_prompt = """너는 네이버 플레이스 사장님 답글을 대신 작성하는 전문가다. 말투는 정중하지만 과하게 딱딱하지 않으며, 진심 어린 인간적인 톤을 유지한다."""
            
            # Build user prompt (상세 버전)
            store_name = request.store_name or "저희 매장"
            review_text = request.review_text or "방문해주셔서 감사합니다"
            
            user_prompt = f"""아래 정보를 바탕으로 네이버 플레이스 리뷰 답글을 작성해줘.

**매장 정보**
- 매장명: {store_name}
- 리뷰 내용을 보고 업종과 분위기를 자동으로 파악해서 적절히 대응할 것

**리뷰 원문**
{review_text}

**작성 규칙(중요)**
1. 이모지 사용 금지
2. 350자 이내(공백 포함)
3. 리뷰 성격을 스스로 판단해 긍정/중립/부정 중 하나로 분류한 뒤 톤을 맞출 것
   - 긍정 리뷰: 반드시 감사함을 분명히 표현하고, 구체적으로 무엇이 좋았는지 짚어 공감
   - 부정 리뷰: 변명하지 말고, 불편에 공감 + 사과 + 개선 의지 + 가능한 경우 짧은 개선 방향 제시
   - 중립 리뷰: 감사 + 보완 약속의 균형
4. 과장/허위 약속 금지. 리뷰에 없는 사실을 지어내지 말 것
5. 문장 2~4개 정도로 자연스럽게 마무리
6. 마지막에 자연스러운 재방문/재이용 초대 한 문장 포함(강요 금지)
7. 업종/업태를 리뷰 내용에서 추론하여 그에 맞는 답글 작성(예: 음식점→맛/서비스, 카페→분위기/음료, 병원→진료/친절 등)

**출력 형식**
- 최종 답글만 출력
- 따로 설명하지 말 것
- 답글의 말투는 '따뜻하지만 과하지 않은 존댓말'을 유지해줘"""
            
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



