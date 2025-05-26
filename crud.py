#crud.py
from sqlalchemy.orm import Session
from models import Alert
from schemas import AlertUpdate # Предположим, у вас есть такая Pydantic модель

def update_alert(db: Session, alert_id: int, alert_update_data: AlertUpdate):
    db_alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if db_alert:
        update_data = alert_update_data.model_dump(exclude_unset=True) # Используем model_dump для Pydantic v2+
        for key, value in update_data.items():
            setattr(db_alert, key, value)
        db.commit()
        db.refresh(db_alert)
        return db_alert
    return None

def create_alert(db: Session, alert_type: str, description: str):
    alert = Alert(type=alert_type, description=description)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_alerts(db: Session):
    return db.query(Alert).all()


def get_alert_by_id(db: Session, alert_id: int):
    return db.query(Alert).filter(Alert.id == alert_id).first()


def delete_alert(db: Session, alert_id: int):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        db.delete(alert)
        db.commit()
        return True
    return False
