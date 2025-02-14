from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services import alerts as alert_service
from schemas import AlertCreate, AlertResponse
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/", response_model=AlertResponse)
def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    return alert_service.create_alert(db, alert)


@router.get("/", response_model=list[AlertResponse])
def read_alerts(
    type: str = None, limit: int = 10, offset: int = 0, db: Session = Depends(get_db)
):
    return alert_service.get_alerts(db, type, limit, offset)


@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int, updated_alert: AlertCreate, db: Session = Depends(get_db)
):
    return alert_service.update_alert(db, alert_id, updated_alert)


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    return alert_service.delete_alert(db, alert_id)