from fastapi import APIRouter

router = APIRouter()


@router.get("/test", tags=["calculator"])
async def test_calculator():
    return {"status": "calculator ok"}
