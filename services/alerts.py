from sqlalchemy.orm import Session
from fastapi import HTTPException
import crud, schemas
from sqlalchemy.exc import IntegrityError


def create_alert(db: Session, alert_data: schemas.AlertCreate):
    """Создает новую тревогу с обработкой ошибок базы данных"""
    try:
        new_alert = crud.create_alert(db, alert_data.type, alert_data.description)
        return new_alert
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ошибка в данных (IntegrityError)")


def get_alerts(
    db: Session,
    type=None,
    from_date=None,
    to_date=None,
    limit=10,
    offset=0,
    sort_desc=True,
):
    """Получить список тревог с фильтрацией и пагинацией"""
    query = db.query(crud.Alert)

    if type:
        query = query.filter(crud.Alert.type == type)
    if from_date:
        query = query.filter(crud.Alert.timestamp >= from_date)
    if to_date:
        query = query.filter(crud.Alert.timestamp <= to_date)

    query = query.order_by(
        crud.Alert.timestamp.desc() if sort_desc else crud.Alert.timestamp.asc()
    )

    return query.limit(limit).offset(offset).all()


def update_alert(db: Session, alert_id: int, updated_data: schemas.AlertCreate):
    """Обновляет данные тревоги по ID"""
    alert = db.query(crud.Alert).filter(crud.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.type = updated_data.type
    alert.description = updated_data.description
    db.commit()
    db.refresh(alert)
    return alert


def delete_alert(db: Session, alert_id: int):
    """Удаляет тревогу по ID"""
    alert = db.query(crud.Alert).filter(crud.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    db.delete(alert)
    db.commit()
    return {"message": "Alert deleted successfully"}
