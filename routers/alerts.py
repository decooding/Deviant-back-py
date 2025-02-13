from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import schemas
from database import get_db
from services import alerts as alert_service  # ✅ Импортируем сервис

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/", response_model=schemas.AlertResponse)
def create_alert(alert: schemas.AlertCreate, db: Session = Depends(get_db)):
    return alert_service.create_alert(db, alert)


@router.get("/", response_model=list[schemas.AlertResponse])
def read_alerts(
    type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 10,
    offset: int = 0,
    sort_desc: bool = True,
    db: Session = Depends(get_db),
):
    return alert_service.get_alerts(
        db, type, from_date, to_date, limit, offset, sort_desc
    )


@router.put("/{alert_id}", response_model=schemas.AlertResponse)
def update_alert(
    alert_id: int, updated_alert: schemas.AlertCreate, db: Session = Depends(get_db)
):
    return alert_service.update_alert(db, alert_id, updated_alert)


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    return alert_service.delete_alert(db, alert_id)
