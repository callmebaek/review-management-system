from fastapi import APIRouter, HTTPException
from services.llm_service import llm_service
from models.schemas import GenerateReplyRequest, GenerateReplyResponse

router = APIRouter()


@router.post("/generate-reply", response_model=GenerateReplyResponse)
async def generate_review_reply(request: GenerateReplyRequest):
    """
    Generate an AI-powered reply to a review
    
    Args:
        request: GenerateReplyRequest with review details
        
    Returns:
        GenerateReplyResponse with generated reply text
    """
    return llm_service.generate_reply(request)


@router.post("/reload-prompts")
async def reload_prompts():
    """
    Reload prompt templates from prompts.json file
    Useful after manually editing the prompts file
    """
    try:
        llm_service.reload_prompts()
        return {
            "success": True,
            "message": "Prompts reloaded successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reloading prompts: {str(e)}"
        )


@router.get("/prompts")
async def get_prompts():
    """
    Get current prompt templates
    """
    return llm_service.prompts



