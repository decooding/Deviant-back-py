from sqlalchemy.orm import Session
from models import Alert
from schemas import AlertCreate, AlertResponse
from fastapi import HTTPException
from utils.logger import logger



def create_alert(db: Session, alert: AlertCreate) -> AlertResponse:
    new_alert = Alert(type=alert.type, description=alert.description)
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    logger.info(f"Создана тревога: {new_alert.id} - {new_alert.type}")
    return new_alert


def get_alerts(db: Session, type: str = None, limit: int = 10, offset: int = 0):
    query = db.query(Alert)
    if type:
        query = query.filter(Alert.type == type)
    return query.limit(limit).offset(offset).all()


def update_alert(db: Session, alert_id: int, updated_alert: AlertCreate):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        logger.error(f"Ошибка: Тревога ID {alert_id} не найдена")
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.type = updated_alert.type
    alert.description = updated_alert.description
    db.commit()
    db.refresh(alert)
    logger.info(f"Обновлена тревога: {alert_id}")
    return alert


def delete_alert(db: Session, alert_id: int):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        logger.error(f"Ошибка: Попытка удалить несуществующую тревогу ID {alert_id}")
        raise HTTPException(status_code=404, detail="Alert not found")

    db.delete(alert)
    db.commit()
    logger.info(f"Удалена тревога: {alert_id}")
    return {"message": "Alert deleted successfully"}
