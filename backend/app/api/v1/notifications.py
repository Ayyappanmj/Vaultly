import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.notification import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=PaginatedResponse[NotificationResponse])
def list_notifications(
    unread_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))

    stmt = stmt.order_by(Notification.created_at.desc())
    items = (
        db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    )

    return PaginatedResponse[NotificationResponse](
        items=items,
        total=len(items),
        page=page,
        page_size=page_size,
        total_pages=1,
    )


@router.post("/{notification_id}/read", response_model=MessageResponse)
def mark_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    notif = db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found."
        )

    notif.is_read = True
    db.commit()
    return MessageResponse(message="Notification marked as read.")


@router.post("/read-all", response_model=MessageResponse)
def mark_all_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    notifs = (
        db.execute(
            select(Notification).where(
                Notification.user_id == current_user.id, Notification.is_read.is_(False)
            )
        )
        .scalars()
        .all()
    )

    for n in notifs:
        n.is_read = True
    db.commit()
    return MessageResponse(message=f"Marked {len(notifs)} notifications as read.")


@router.delete("/{notification_id}", response_model=MessageResponse)
def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    notif = db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found."
        )

    db.delete(notif)
    db.commit()
    return MessageResponse(message="Notification deleted successfully.")
