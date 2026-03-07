from fastapi import APIRouter, Depends, Response

from ibidem.homely_mqtt.subsystems import SubsystemManager, manager

router = APIRouter()


@router.get("/live")
def liveness():
    return "Ok"


@router.get("/ready")
def readiness(response: Response, subsystem_manager: SubsystemManager = Depends(manager)):
    state = subsystem_manager.ready()
    response.status_code = 200 if all(v for k, v in state.items()) else 500
    return state
