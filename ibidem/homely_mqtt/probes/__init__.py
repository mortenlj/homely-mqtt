from fastapi import APIRouter

router = APIRouter()


@router.get("/live")
def liveness():
    return "Ok"


@router.get("/ready")
def readiness():
    return "Ok"
