from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ReviewFilter(str, Enum):
    ALL = "all"
    REPLIED = "replied"
    UNREPLIED = "unreplied"


class ReviewRating(str, Enum):
    ONE = "ONE"
    TWO = "TWO"
    THREE = "THREE"
    FOUR = "FOUR"
    FIVE = "FIVE"


# GBP Schemas
class GBPAccount(BaseModel):
    name: str
    account_name: str
    type: str
    role: Optional[str] = None


class GBPLocation(BaseModel):
    name: str
    location_name: str
    store_code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class ReviewerInfo(BaseModel):
    display_name: str
    profile_photo_url: Optional[str] = None
    is_anonymous: bool = False


class ReviewReply(BaseModel):
    comment: str
    update_time: Optional[datetime] = None


class Review(BaseModel):
    review_id: str
    reviewer: ReviewerInfo
    star_rating: str
    comment: Optional[str] = None
    create_time: datetime
    update_time: datetime
    review_reply: Optional[ReviewReply] = None
    name: str  # Full resource name


class ReviewsResponse(BaseModel):
    reviews: List[Review]
    total_count: int
    average_rating: Optional[float] = None


# Reply Generation
class GenerateReplyRequest(BaseModel):
    review_text: Optional[str] = None
    rating: Optional[int] = Field(default=3, ge=1, le=5)  # Optional for Naver reviews (no rating)
    store_name: Optional[str] = None
    custom_instructions: Optional[str] = None
    place_settings: Optional[dict] = None  # Place-specific AI settings


class GenerateReplyResponse(BaseModel):
    generated_reply: str
    rating: int
    prompt_used: str


# Reply Posting
class PostReplyRequest(BaseModel):
    review_id: str
    reply_text: str
    location_name: str


class PostReplyResponse(BaseModel):
    success: bool
    message: str
    review_id: str


# Store Management
class Store(BaseModel):
    id: str
    name: str
    gbp_location_name: Optional[str] = None
    naver_place_id: Optional[str] = None
    custom_prompt: Optional[str] = None


class StoresConfig(BaseModel):
    stores: List[Store] = []


# Prompt Templates
class PromptTemplate(BaseModel):
    positive: str  # For 4-5 star reviews
    neutral: str   # For 3 star reviews
    negative: str  # For 1-2 star reviews


class PromptsConfig(BaseModel):
    default: PromptTemplate
    custom: dict[str, PromptTemplate] = {}


# AI Settings for Place-specific reply generation
class PlaceAISettings(BaseModel):
    friendliness: int = Field(default=7, ge=1, le=10, description="친절함 정도 (1-10)")
    formality: int = Field(default=7, ge=1, le=10, description="격식 수준 (1=반말, 10=격식)")
    reply_length_min: int = Field(default=100, ge=50, le=450, description="최소 답글 길이")
    reply_length_max: int = Field(default=450, ge=50, le=450, description="최대 답글 길이")
    diversity: float = Field(default=0.9, ge=0.5, le=1.0, description="다양성 (temperature)")
    use_text_emoticons: bool = Field(default=True, description="텍스트 이모티콘 사용 (^^, ㅎㅎ 등)")
    mention_specifics: bool = Field(default=True, description="리뷰 구체 내용 언급")
    brand_voice: str = Field(default="warm", description="브랜드 톤 (warm/professional/casual/friendly)")
    response_style: str = Field(default="quick_thanks", description="응답 스타일 (quick_thanks/empathy/solution)")
    custom_instructions: Optional[str] = Field(default=None, description="추가 요청사항")


class PlaceAISettingsResponse(BaseModel):
    place_id: str
    google_email: str
    settings: PlaceAISettings
    created_at: datetime
    updated_at: datetime





