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
    
    def _build_custom_system_prompt(self, place_settings) -> str:
        """
        Build customized system prompt based on place settings
        
        Args:
            place_settings: PlaceAISettings object with custom configurations
        
        Returns:
            Customized system prompt string
        """
        # 🔥 더 구체적이고 차별화된 친절함 수준
        if place_settings.friendliness >= 9:
            friendliness_level = "극도로 열정적이고 감동적인"
            friendliness_detail = "고객을 매우 특별하게 대우하고, 과도할 정도로 긍정적이며, 감탄사와 감사 표현을 풍부하게 사용한다."
        elif place_settings.friendliness >= 7:
            friendliness_level = "매우 따뜻하고 친절한"
            friendliness_detail = "고객에게 진심 어린 감사를 전하고, 개인적인 느낌을 주며, 따뜻한 표현을 자주 사용한다."
        elif place_settings.friendliness >= 5:
            friendliness_level = "적절히 친절한"
            friendliness_detail = "기본적인 예의를 갖추고 정중하게 대하되, 과하지 않게 감사를 표현한다."
        elif place_settings.friendliness >= 3:
            friendliness_level = "간결하고 사무적인"
            friendliness_detail = "필요한 내용만 간단히 전달하고, 감사 표현을 최소화하며, 효율적으로 작성한다."
        else:
            friendliness_level = "매우 간결하고 형식적인"
            friendliness_detail = "사무적이고 건조하게, 감정 표현 없이 필수 내용만 전달한다."
        
        # 🔥 더 명확한 격식 수준
        if place_settings.formality >= 9:
            formality_desc = "매우 격식있는 존댓말 사용 (예: ~입니다, ~하겠습니다, ~주시기 바랍니다)"
            formality_example = "예: '소중한 말씀 감사드립니다', '최선을 다하겠습니다'"
        elif place_settings.formality >= 7:
            formality_desc = "정중한 존댓말 사용 (예: ~해요, ~드려요, ~주세요)"
            formality_example = "예: '감사해요', '노력할게요', '방문해주세요'"
        elif place_settings.formality >= 5:
            formality_desc = "편안한 존댓말 사용 (예: ~요 체)"
            formality_example = "예: '고마워요', '좋았어요', '또 와요'"
        elif place_settings.formality >= 3:
            formality_desc = "친근한 반말 사용 (예: ~어, ~지, ~네)"
            formality_example = "예: '고마워', '좋았어', '또 와'"
        else:
            formality_desc = "매우 캐주얼한 반말 사용"
            formality_example = "예: '감사~', '굿!', '또 봐'"
        
        # 🔥 이모티콘 사용 빈도
        if place_settings.use_text_emoticons:
            emoticon_instruction = "텍스트 이모티콘(^^, ㅎㅎ, :) 등)을 적극적으로 사용하여 친근함을 표현한다. (문장당 1-2개 정도)"
        else:
            emoticon_instruction = "이모티콘을 절대 사용하지 않고 텍스트만으로 표현한다."
        
        # 🔥 구체성 지시
        if place_settings.mention_specifics:
            specifics_instruction = "리뷰에서 언급된 구체적인 내용(맛, 분위기, 서비스, 직원, 메뉴 등)을 반드시 1-2가지 이상 답글에 언급한다."
        else:
            specifics_instruction = "구체적인 내용보다는 전반적이고 일반적인 감사 인사 위주로 작성한다."
        
        # 🔥 브랜드 보이스 상세화
        brand_voice_map = {
            "warm": ("따뜻하고 감성적인", "고객의 감정에 공감하고, '감동', '기쁨', '행복' 같은 감성 단어를 사용"),
            "professional": ("전문적이고 신뢰감 있는", "정확하고 명확한 표현을 사용하며, 전문성과 책임감을 강조"),
            "casual": ("캐주얼하고 편안한", "일상적이고 자연스러운 표현을 사용하며, 부담 없는 분위기 조성"),
            "friendly": ("친근하고 활기찬", "밝고 에너지 넘치는 표현을 사용하며, 친구같은 느낌")
        }
        brand_voice_desc, brand_voice_detail = brand_voice_map.get(place_settings.brand_voice, ("따뜻한", "고객에게 따뜻하게 대응"))
        
        # 🔥 응답 스타일 상세화
        response_style_map = {
            "quick_thanks": ("신속한 감사 표현", "먼저 감사를 표현하고 간단히 마무리. 짧고 명확하게."),
            "empathy": ("공감과 이해", "고객의 경험과 감정에 깊이 공감하고, '~하셨군요', '~하셨다니' 같은 표현 사용"),
            "solution": ("해결책 제시", "개선 의지와 구체적인 노력을 강조하며, '~하겠습니다', '~할게요' 같은 약속 표현")
        }
        response_style_desc, response_style_detail = response_style_map.get(place_settings.response_style, ("감사", "감사 표현"))
        
        system_prompt = f"""[ROLE]
너는 네이버 플레이스 리뷰에 답글을 다는 "매장 CS 담당자"다. 리뷰를 정확히 읽고 이해한 뒤, {friendliness_level} 톤으로 답글을 작성한다.

[TONE & STYLE - 매우 중요!]
친절함 수준 ({place_settings.friendliness}/10): {friendliness_level}
→ {friendliness_detail}

격식 수준 ({place_settings.formality}/10): {formality_desc}
→ {formality_example}

브랜드 보이스: {brand_voice_desc}
→ {brand_voice_detail}

응답 스타일: {response_style_desc}
→ {response_style_detail}

이모티콘: {emoticon_instruction}

구체성: {specifics_instruction}

🔥 위 설정값들을 정확히 반영하여 답글의 톤, 어투, 길이, 내용이 명확히 달라져야 한다!

[실제 적용 예시]
친절함 1-3 (사무적): "방문 감사합니다. 의견 전달드리겠습니다."
친절함 7-8 (따뜻): "와주셔서 정말 반가웠어요^^ 좋은 말씀 너무 감사드려요!"
친절함 9-10 (열정): "정말정말 감사합니다!! 이렇게 좋은 리뷰를 남겨주시다니 저희에게는 최고의 선물이에요!!"

격식 1-3 (반말): "고마워! 또 와~"
격식 5-7 (존댓말): "감사해요! 또 방문해주세요^^"
격식 9-10 (격식): "진심으로 감사드립니다. 다음에도 방문해주시기 바랍니다."

🔥 설정값에 따라 위처럼 극명한 차이가 나야 한다!"""
        
        if place_settings.custom_instructions:
            system_prompt += f"\n\n[매장 특별 요청사항 - 일반]\n{place_settings.custom_instructions}"
        
        return system_prompt
    
    def _build_custom_system_prompt_negative(self, place_settings) -> str:
        """
        Build customized system prompt for negative reviews (1-2 stars)
        
        Args:
            place_settings: PlaceAISettings object with custom configurations
        
        Returns:
            Customized system prompt string for negative reviews
        """
        # Start with base prompt
        base_prompt = self._build_custom_system_prompt(place_settings)
        
        # Add negative review specific instructions
        negative_instructions = """

[부정 리뷰 특별 대응 지침]
⚠️ 이 리뷰는 부정적입니다. 다음 원칙을 반드시 지켜주세요:

1. 진심 어린 사과: 고객의 불편함에 대해 먼저 진심으로 사과
2. 구체적 공감: 리뷰에 언급된 불편 사항을 구체적으로 언급하며 공감
3. 개선 약속: 문제 해결을 위한 구체적인 개선 의지 표현
4. 직접 소통 제안: 가능하면 직접 대화할 수 있는 채널 안내 (변명 X)
5. 보상/재방문 기회: 적절한 경우 재방문 혜택이나 보상 언급

❌ 금지사항:
- 고객 탓하기, 변명하기
- 일반적인 사과만 나열
- 너무 짧은 답글 (최소한 성의 있게)
- 과도한 긍정적 표현 (부정 리뷰에는 진중함 필요)"""
        
        result = base_prompt + negative_instructions
        
        # Add negative-specific custom instructions if provided
        if place_settings.custom_instructions_negative:
            result += f"\n\n[매장 특별 요청사항 - 부정 리뷰]\n{place_settings.custom_instructions_negative}"
        
        return result
    
    def generate_reply(self, request: GenerateReplyRequest, place_settings=None) -> GenerateReplyResponse:
        """
        Generate a reply to a review using OpenAI
        
        Args:
            request: GenerateReplyRequest containing review details
            place_settings: Optional PlaceAISettings for customization
        
        Returns:
            GenerateReplyResponse with generated reply
        """
        try:
            client = self._get_client()
            
            # Get appropriate prompt template
            template = self._get_prompt_template(request.rating, request.store_name)
            
            # Determine parameters based on place_settings
            if place_settings:
                temperature = place_settings.diversity
                max_tokens = int(place_settings.reply_length_max * 1.5)  # 여유를 두고 설정
                min_length = place_settings.reply_length_min
                max_length = place_settings.reply_length_max
                
                # 🔥 다양성에 따라 penalty 조정
                # 다양성이 높을수록 더 창의적이고 반복 회피
                frequency_penalty = 0.5 + (place_settings.diversity * 0.4)  # 0.7-0.9
                presence_penalty = 0.3 + (place_settings.diversity * 0.4)   # 0.5-0.7
                
                print(f"🎨 AI Parameters: temp={temperature}, freq_penalty={frequency_penalty:.2f}, presence_penalty={presence_penalty:.2f}")
                print(f"📏 Length range: {min_length}-{max_length}, max_tokens={max_tokens}")
                print(f"🎭 Settings: friendliness={place_settings.friendliness}, formality={place_settings.formality}")
                
                # 🔥 부정 리뷰 (1-2점)는 특별 프롬프트 사용
                if request.rating and request.rating <= 2:
                    system_prompt = self._build_custom_system_prompt_negative(place_settings)
                    print(f"🔥 Using NEGATIVE review prompt for rating {request.rating}")
                else:
                    system_prompt = self._build_custom_system_prompt(place_settings)
                    print(f"✅ Using normal review prompt for rating {request.rating}")
            else:
                # Default values
                temperature = 0.9
                max_tokens = 500
                min_length = 100
                max_length = 450
                frequency_penalty = 0.8
                presence_penalty = 0.6
                
                print(f"🎨 Using DEFAULT AI parameters")
                
                # Build default system prompt
                system_prompt = """[ROLE]
너는 네이버 플레이스 리뷰에 답글을 다는 "매장 CS 담당자"다. 리뷰를 정확히 읽고 이해한 뒤, 항상 친절하고 긍정적인 톤으로 답글을 작성한다.

[CRITICAL: 다양성 최우선]
⚠️ 매우 중요: 각 답글마다 완전히 다른 시작과 마무리를 사용해야 한다.
절대로 같은 패턴을 반복하지 마라. 창의적이고 예측 불가능한 표현을 사용하라.

[GOAL]
각 리뷰마다 서로 다른 표현/구조로 답글을 작성한다.
브랜드 톤은 일관되게 유지: 따뜻함 / 감사 / 재방문 환영 / 짧고 자연스러움
과장, 진부한 문구 반복은 절대 금지."""
            
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

[LENGTH REQUIREMENT]
- 답글 길이: {min_length}~{max_length}자 사이로 작성
- 너무 짧거나 길지 않게, 이 범위 내에서 자연스럽게 작성

[STYLE RULES]
🔥 핵심 원칙: 이 답글은 세상에 단 하나뿐이어야 한다. 다른 답글과 겹치지 않는 독특한 시작과 마무리를 사용하라.

1. 리뷰 내용에서 최소 1개 구체 요소를 꼭 집어서 답한다
   예: "직원 친절", "대기", "맛", "양", "분위기", "가격", "재방문", "추천", "청결", "주차" 등

2. 리뷰가 짧으면: "방문해주신 시간/선택해주신 메뉴(추정 X)" 대신 "방문/경험" 자체에 감사

3. 문장 패턴 다양화 (🔥 매우 중요!)
   ⚠️ CRITICAL: 이전 답글과 완전히 다른 시작/마무리를 사용할 것
   
   시작 문장 예시 (이것만 사용하지 말고 매번 새롭게 창작):
   - "와주셔서 정말 반가웠어요^^"
   - "따뜻한 후기 남겨주셔서 힘이 납니다!"
   - "말씀 남겨주신 포인트가 딱 저희가 바라는 경험이에요."
   - "기억에 남는 방문이 되셨다니 다행이에요."
   - "바쁘실 텐데 후기까지 남겨주셔서 감사합니다."
   - "리뷰 보면서 저희도 미소가 났어요."
   - "소중한 시간 내주셔서 고맙습니다."
   - "이렇게 좋은 말씀 남겨주시니 감동이네요."
   - "후기 하나하나가 정말 큰 힘이 됩니다."
   - "세심하게 봐주셔서 감사해요."
   
   ⚠️ 중요: 이모지(😊, 🎉 등) 절대 사용 금지! 텍스트 이모티콘(:), ^^, ㅎㅎ)만 사용
   
   마무리 문장도 매번 다르게:
   - "다음에 또 뵙겠습니다!"
   - "또 오시면 반갑게 맞이할게요."
   - "언제든 편하게 방문해주세요."
   - "다음엔 더 좋은 경험 드릴게요."
   - "기다리고 있을게요!"
   - "꼭 다시 만나요."
   - "좋은 하루 되세요!"
   
   🔥 핵심: 위 예시를 그대로 쓰지 말고, 이 분위기로 매번 새롭게 창작하라!

4. 길이
   - {min_length}~{max_length}자 사이로 작성 (이 범위를 반드시 지킬 것)
   - 🚨 이모지 사용 금지 (시스템 호환성 문제)
   - "ㅋㅋ", ":)", "^^" 같은 텍스트 이모티콘은 설정에 따라 사용
   - "ㅎㅎ"는 고객 리뷰에 있을 때만 1회 정도 가능

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

[다양성 강화 예시]
같은 긍정 리뷰 3개에도 완전히 다른 답글:

리뷰A: "맛있어요!"
→ "와주셔서 정말 반가웠어요^^ 맛에 대한 칭찬이 가장 큰 보람입니다. 다음에도 맛있게 드실 수 있게 준비할게요!"

리뷰B: "분위기 좋아요"
→ "후기 하나하나가 정말 큰 힘이 됩니다. 편안한 분위기 만들려고 신경 쓴 부분을 알아봐주셔서 감사해요. 언제든 편하게 방문해주세요."

리뷰C: "직원 친절해요"
→ "세심하게 봐주셔서 감사해요. 말씀해주신 직원 친절함이 저희에게 가장 중요한 가치예요. 좋은 하루 되세요!"

🔥 주목: 시작도, 마무리도, 구조도 모두 다름!

**출력 형식**
- 최종 답글만 출력 (설명 금지)
- 자연스러운 존댓말 유지
- 🔥 매번 완전히 새로운 문장 구조 사용

🎲 랜덤성 체크리스트:
□ 이전과 다른 시작 문구 사용했는가?
□ 이전과 다른 마무리 문구 사용했는가?
□ 문장 구조를 바꿨는가? (예: 감사→구체→마무리 vs 구체→공감→감사)
□ 새로운 표현을 시도했는가?

🚨 절대 금지: "감사합니다", "다음에 또 뵙겠습니다" 같은 뻔한 표현 연속 사용"""
            
            if request.custom_instructions:
                user_prompt += f"\n\n**추가 요청사항**\n{request.custom_instructions}"
            
            # Call OpenAI API with customized parameters
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,  # Customizable diversity
                max_tokens=max_tokens,  # Customizable length
                frequency_penalty=frequency_penalty,  # 반복 패턴 억제 (설정 기반)
                presence_penalty=presence_penalty   # 새로운 표현 장려 (설정 기반)
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



