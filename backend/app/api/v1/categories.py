import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Category)
        .where(or_(Category.user_id == current_user.id, Category.user_id.is_(None)))
        .order_by(Category.name.asc())
    )
    return db.execute(stmt).scalars().all()


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    body: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Check if duplicate name for this user
    existing = db.execute(
        select(Category).where(
            Category.user_id == current_user.id,
            Category.name.ilike(body.name.strip()),
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Category already exists."
        )

    category = Category(
        user_id=current_user.id,
        name=body.name.strip(),
        icon=body.icon,
        color=body.color,
        is_system=False,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", response_model=MessageResponse)
def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    category = db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found."
        )

    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System categories cannot be deleted.",
        )

    db.delete(category)
    db.commit()
    return MessageResponse(message="Category deleted successfully.")
