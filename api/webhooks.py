from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/webhook/approval")
async def approval_webhook(request: Request):
    data = await request.json()
    # TODO: Process approval
    return {"status": "received"}

@router.post("/webhook/image-selection")
async def image_selection_webhook(request: Request):
    data = await request.json()
    # TODO: Process image selection
    return {"status": "received"}