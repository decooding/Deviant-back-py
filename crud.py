from sqlalchemy.orm import Session
from models import Alert


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
