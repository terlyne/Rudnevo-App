from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.partner import Partner
from schemas.partner import PartnerCreate, PartnerUpdate


async def get_partners_list(
    db: AsyncSession, skip: int = 0, limit: int = 100, show_hidden: bool = False
) -> list[Partner]:
    """Получить список партнеров"""
    query = select(Partner)

    if not show_hidden:
        query = query.where(Partner.is_active == True)

    result = await db.execute(
        query.order_by(Partner.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def get_partner(db: AsyncSession, partner_id: int) -> Partner | None:
    """Получить партнера по ID"""
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    return result.scalar_one_or_none()


async def create_partner(db: AsyncSession, partner_in: PartnerCreate) -> Partner:
    """Создать партнера"""
    db_partner = Partner(**partner_in.model_dump())
    db.add(db_partner)
    await db.commit()
    await db.refresh(db_partner)
    return db_partner


async def update_partner(
    db: AsyncSession, partner_id: int, partner_in: PartnerUpdate
) -> Partner | None:
    """Обновить партнера"""
    db_partner = await get_partner(db, partner_id)
    if not db_partner:
        return None

    update_data = partner_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "image_url":
            setattr(db_partner, field, value)
        elif value is not None:
            setattr(db_partner, field, value)

    await db.commit()
    await db.refresh(db_partner)
    return db_partner


async def delete_partner(db: AsyncSession, partner_id: int) -> bool:
    """Удалить партнера"""
    db_partner = await get_partner(db, partner_id)
    if not db_partner:
        return False

    await db.delete(db_partner)
    await db.commit()
    return True


async def toggle_partner_visibility(db: AsyncSession, partner_id: int) -> Partner | None:
    """Переключить видимость партнера"""
    db_partner = await get_partner(db, partner_id)
    if not db_partner:
        return None

    db_partner.is_active = not db_partner.is_active
    await db.commit()
    await db.refresh(db_partner)
    return db_partner 