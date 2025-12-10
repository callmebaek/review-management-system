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





