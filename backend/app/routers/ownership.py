from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import App, User, OwnershipClaim, ClaimStatus, Notification, NotificationType
from app.schemas import schemas
from app.routers.auth import get_current_user, require_admin
from app.services.telegram import notify_ownership_claim

router = APIRouter()

@router.post("/apps/{app_id}/claim-ownership", response_model=schemas.OwnershipClaimResponse)
async def claim_ownership(
    app_id: int,
    claim_in: schemas.OwnershipClaimCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify app exists
    result = await db.execute(select(App).filter(App.id == app_id))
    app = result.scalars().first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    # Check if user is already the owner
    if app.creator_id == current_user.id and app.is_owner:
        raise HTTPException(status_code=400, detail="You are already marked as the owner of this app")
    
    # Check for existing pending claim by this user for this app
    stmt = select(OwnershipClaim).filter(
        OwnershipClaim.app_id == app_id,
        OwnershipClaim.claimant_id == current_user.id,
        OwnershipClaim.status == ClaimStatus.PENDING
    )
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="You already have a pending claim for this app")

    db_claim = OwnershipClaim(
        app_id=app_id,
        claimant_id=current_user.id,
        message=claim_in.message,
        status=ClaimStatus.PENDING
    )
    db.add(db_claim)
    
    # Notify app creator that someone is claiming their app
    if app.creator_id != current_user.id:
        notification = Notification(
            user_id=app.creator_id,
            type=NotificationType.OWNERSHIP_CLAIM,
            content=f"{current_user.username} is claiming ownership of your app: {app.title}",
            link=f"/apps/{app.slug}"
        )
        db.add(notification)
    
    await db.commit()
    await db.refresh(db_claim)
    notify_ownership_claim(current_user.username, app.title)
    return db_claim

@router.get("/ownership-claims", response_model=List[schemas.OwnershipClaimWithDetails])
async def get_all_pending_claims(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all pending ownership claims (admin only)."""
    stmt = (
        select(OwnershipClaim)
        .options(selectinload(OwnershipClaim.claimant), selectinload(OwnershipClaim.app))
        .filter(OwnershipClaim.status == ClaimStatus.PENDING)
        .order_by(OwnershipClaim.created_at)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/apps/{app_id}/ownership-claims", response_model=List[schemas.OwnershipClaim])
async def get_app_claims(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Only admin or app creator should see this
    result = await db.execute(select(App).filter(App.id == app_id))
    app = result.scalars().first()
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    if not current_user.is_admin and app.creator_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to see claims for this app")

    stmt = (
        select(OwnershipClaim)
        .options(selectinload(OwnershipClaim.claimant))
        .filter(OwnershipClaim.app_id == app_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.put("/ownership-claims/{claim_id}/resolve", response_model=schemas.OwnershipClaim)
async def resolve_claim(
    claim_id: int,
    status: ClaimStatus,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Resolve an ownership claim (admin only)."""
    result = await db.execute(
        select(OwnershipClaim)
        .options(selectinload(OwnershipClaim.app))
        .filter(OwnershipClaim.id == claim_id)
    )
    claim = result.scalars().first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if claim.status != ClaimStatus.PENDING:
        raise HTTPException(status_code=400, detail="Claim already resolved")
    
    claim.status = status
    claim.resolved_at = datetime.now()
    
    if status == ClaimStatus.APPROVED:
        # Transfer ownership
        app = claim.app
        app.creator_id = claim.claimant_id
        app.is_owner = True
        db.add(app)
        
        # Notify claimant
        notification = Notification(
            user_id=claim.claimant_id,
            type=NotificationType.OWNERSHIP_CLAIM,
            content=f"Your ownership claim for {app.title} has been APPROVED!",
            link=f"/apps/{app.slug}"
        )
        db.add(notification)
    else:
        # Notify claimant of rejection
        notification = Notification(
            user_id=claim.claimant_id,
            type=NotificationType.OWNERSHIP_CLAIM,
            content=f"Your ownership claim for {claim.app.title} was rejected.",
            link=f"/apps/{claim.app.slug}"
        )
        db.add(notification)

    await db.commit()
    await db.refresh(claim)
    return claim
