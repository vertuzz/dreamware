from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import Dream, User, OwnershipClaim, ClaimStatus, Notification, NotificationType
from app.schemas import schemas
from app.routers.auth import get_current_user, require_admin

router = APIRouter()

@router.post("/dreams/{dream_id}/claim-ownership", response_model=schemas.OwnershipClaim)
async def claim_ownership(
    dream_id: int,
    claim_in: schemas.OwnershipClaimCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify dream exists
    result = await db.execute(select(Dream).filter(Dream.id == dream_id))
    dream = result.scalars().first()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")
    
    # Check if user is already the owner
    if dream.creator_id == current_user.id and dream.is_owner:
        raise HTTPException(status_code=400, detail="You are already marked as the owner of this dream")
    
    # Check for existing pending claim by this user for this dream
    stmt = select(OwnershipClaim).filter(
        OwnershipClaim.dream_id == dream_id,
        OwnershipClaim.claimant_id == current_user.id,
        OwnershipClaim.status == ClaimStatus.PENDING
    )
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="You already have a pending claim for this dream")

    db_claim = OwnershipClaim(
        dream_id=dream_id,
        claimant_id=current_user.id,
        message=claim_in.message,
        status=ClaimStatus.PENDING
    )
    db.add(db_claim)
    
    # Notify dream creator that someone is claiming their dream
    if dream.creator_id != current_user.id:
        notification = Notification(
            user_id=dream.creator_id,
            type=NotificationType.OWNERSHIP_CLAIM,
            content=f"{current_user.username} is claiming ownership of your dream: {dream.title}",
            link=f"/dreams/{dream.slug}"
        )
        db.add(notification)
    
    await db.commit()
    await db.refresh(db_claim)
    return db_claim

@router.get("/ownership-claims", response_model=List[schemas.OwnershipClaimWithDetails])
async def get_all_pending_claims(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all pending ownership claims (admin only)."""
    stmt = (
        select(OwnershipClaim)
        .options(selectinload(OwnershipClaim.claimant), selectinload(OwnershipClaim.dream))
        .filter(OwnershipClaim.status == ClaimStatus.PENDING)
        .order_by(OwnershipClaim.created_at)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/dreams/{dream_id}/ownership-claims", response_model=List[schemas.OwnershipClaim])
async def get_dream_claims(
    dream_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Only admin or dream creator should see this
    result = await db.execute(select(Dream).filter(Dream.id == dream_id))
    dream = result.scalars().first()
    if not dream:
        raise HTTPException(status_code=404, detail="Dream not found")
    
    if not current_user.is_admin and dream.creator_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to see claims for this dream")

    stmt = (
        select(OwnershipClaim)
        .options(selectinload(OwnershipClaim.claimant))
        .filter(OwnershipClaim.dream_id == dream_id)
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
        .options(selectinload(OwnershipClaim.dream))
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
        dream = claim.dream
        dream.creator_id = claim.claimant_id
        dream.is_owner = True
        db.add(dream)
        
        # Notify claimant
        notification = Notification(
            user_id=claim.claimant_id,
            type=NotificationType.OWNERSHIP_CLAIM,
            content=f"Your ownership claim for {dream.title} has been APPROVED!",
            link=f"/dreams/{dream.slug}"
        )
        db.add(notification)
    else:
        # Notify claimant of rejection
        notification = Notification(
            user_id=claim.claimant_id,
            type=NotificationType.OWNERSHIP_CLAIM,
            content=f"Your ownership claim for {claim.dream.title} was rejected.",
            link=f"/dreams/{claim.dream.slug}"
        )
        db.add(notification)

    await db.commit()
    await db.refresh(claim)
    return claim
