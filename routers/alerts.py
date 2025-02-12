from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import crud, schemas
from database import get_db

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/", response_model=schemas.AlertResponse)
def create_alert(alert: schemas.AlertCreate, db: Session = Depends(get_db)):
    return crud.create_alert(db, alert.type, alert.description)


@router.get("/", response_model=list[schemas.AlertResponse])
def read_alerts(db: Session = Depends(get_db)):
    return crud.get_alerts(db)


@router.get("/{alert_id}", response_model=schemas.AlertResponse)
def read_alert(alert_id: int, db: Session = Depends(get_db)):
    return crud.get_alert_by_id(db, alert_id)


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    return {"deleted": crud.delete_alert(db, alert_id)}
