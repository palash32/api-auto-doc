"""Team collaboration API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.models.team import (
    TeamMember, TeamRole, Workspace, WorkspaceMember,
    EndpointComment, ChangeRequest, ChangeStatus, ActivityLog
)
from app.models.user import User, Organization

router = APIRouter()


# ==================== Pydantic Schemas ====================

class TeamMemberCreate(BaseModel):
    email: str
    role: str = "viewer"


class TeamMemberResponse(BaseModel):
    id: str
    user_id: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    invited_at: datetime
    accepted_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TeamMemberUpdate(BaseModel):
    role: str


class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_private: bool = False


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    icon: Optional[str]
    color: Optional[str]
    is_default: bool
    is_private: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[str] = None
    line_number: Optional[str] = None


class CommentResponse(BaseModel):
    id: str
    endpoint_id: str
    user_id: str
    user_name: Optional[str]
    content: str
    parent_id: Optional[str]
    line_number: Optional[str]
    is_resolved: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChangeRequestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    changes: dict


class ChangeRequestResponse(BaseModel):
    id: str
    endpoint_id: str
    author_id: str
    author_name: Optional[str]
    title: str
    description: Optional[str]
    changes: dict
    status: str
    reviewer_id: Optional[str]
    reviewed_at: Optional[datetime]
    review_comment: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Team Member Endpoints ====================

@router.get("/members", response_model=List[TeamMemberResponse])
async def list_team_members(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List all team members in the organization."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(TeamMember, User)
        .join(User, TeamMember.user_id == User.id)
        .where(TeamMember.organization_id == org_id)
    )
    rows = result.all()
    
    return [
        TeamMemberResponse(
            id=str(member.id),
            user_id=str(member.user_id),
            email=user.email,
            full_name=user.full_name,
            role=member.role,
            is_active=member.is_active,
            invited_at=member.invited_at,
            accepted_at=member.accepted_at
        )
        for member, user in rows
    ]


@router.post("/members", response_model=TeamMemberResponse)
async def invite_team_member(
    data: TeamMemberCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Invite a new team member to the organization."""
    org_id = current_user.get("organization_id")
    
    # Check if inviter has permission
    # (In production, verify inviter's role)
    
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create placeholder user for invitation
        user = User(
            email=data.email,
            full_name=data.email.split("@")[0],
            organization_id=org_id,
            is_verified=False
        )
        db.add(user)
        await db.flush()
    
    # Check if already a member
    existing = await db.execute(
        select(TeamMember).where(
            TeamMember.user_id == str(user.id),
            TeamMember.organization_id == org_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="User is already a team member"
        )
    
    # Create team member
    member = TeamMember(
        user_id=str(user.id),
        organization_id=org_id,
        role=data.role,
        invited_by_id=current_user.get("id")
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    
    return TeamMemberResponse(
        id=str(member.id),
        user_id=str(member.user_id),
        email=user.email,
        full_name=user.full_name,
        role=member.role,
        is_active=member.is_active,
        invited_at=member.invited_at,
        accepted_at=member.accepted_at
    )


@router.patch("/members/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: str,
    data: TeamMemberUpdate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Update a team member's role."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(TeamMember, User)
        .join(User, TeamMember.user_id == User.id)
        .where(
            TeamMember.id == member_id,
            TeamMember.organization_id == org_id
        )
    )
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member, user = row
    
    # Validate role
    valid_roles = [r.value for r in TeamRole]
    if data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    member.role = data.role
    await db.commit()
    
    return TeamMemberResponse(
        id=str(member.id),
        user_id=str(member.user_id),
        email=user.email,
        full_name=user.full_name,
        role=member.role,
        is_active=member.is_active,
        invited_at=member.invited_at,
        accepted_at=member.accepted_at
    )


@router.delete("/members/{member_id}")
async def remove_team_member(
    member_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Remove a team member from the organization."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(TeamMember).where(
            TeamMember.id == member_id,
            TeamMember.organization_id == org_id
        )
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Can't remove owner
    if member.role == TeamRole.OWNER.value:
        raise HTTPException(status_code=400, detail="Cannot remove organization owner")
    
    await db.delete(member)
    await db.commit()
    
    return {"message": "Member removed"}


# ==================== Workspace Endpoints ====================

@router.get("/workspaces", response_model=List[WorkspaceResponse])
async def list_workspaces(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List all workspaces in the organization."""
    org_id = current_user.get("organization_id")
    
    result = await db.execute(
        select(Workspace).where(Workspace.organization_id == org_id)
    )
    workspaces = result.scalars().all()
    
    return [WorkspaceResponse(
        id=str(w.id),
        name=w.name,
        slug=w.slug,
        description=w.description,
        icon=w.icon,
        color=w.color,
        is_default=w.is_default,
        is_private=w.is_private,
        created_at=w.created_at
    ) for w in workspaces]


@router.post("/workspaces", response_model=WorkspaceResponse)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new workspace."""
    org_id = current_user.get("organization_id")
    
    # Generate slug from name
    slug = data.name.lower().replace(" ", "-").replace("_", "-")
    
    workspace = Workspace(
        organization_id=org_id,
        name=data.name,
        slug=slug,
        description=data.description,
        icon=data.icon,
        color=data.color,
        is_private=data.is_private,
        created_by_id=current_user.get("id")
    )
    
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    
    return WorkspaceResponse(
        id=str(workspace.id),
        name=workspace.name,
        slug=workspace.slug,
        description=workspace.description,
        icon=workspace.icon,
        color=workspace.color,
        is_default=workspace.is_default,
        is_private=workspace.is_private,
        created_at=workspace.created_at
    )


# ==================== Comment Endpoints ====================

@router.get("/endpoints/{endpoint_id}/comments", response_model=List[CommentResponse])
async def list_endpoint_comments(
    endpoint_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List all comments on an endpoint."""
    result = await db.execute(
        select(EndpointComment, User)
        .join(User, EndpointComment.user_id == User.id)
        .where(EndpointComment.endpoint_id == endpoint_id)
        .order_by(EndpointComment.created_at)
    )
    rows = result.all()
    
    return [
        CommentResponse(
            id=str(comment.id),
            endpoint_id=str(comment.endpoint_id),
            user_id=str(comment.user_id),
            user_name=user.full_name,
            content=comment.content,
            parent_id=str(comment.parent_id) if comment.parent_id else None,
            line_number=comment.line_number,
            is_resolved=comment.is_resolved,
            created_at=comment.created_at
        )
        for comment, user in rows
    ]


@router.post("/endpoints/{endpoint_id}/comments", response_model=CommentResponse)
async def add_endpoint_comment(
    endpoint_id: str,
    data: CommentCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Add a comment to an endpoint."""
    user_id = current_user.get("id")
    
    comment = EndpointComment(
        endpoint_id=endpoint_id,
        user_id=user_id,
        content=data.content,
        parent_id=data.parent_id,
        line_number=data.line_number
    )
    
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    # Get user name
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    return CommentResponse(
        id=str(comment.id),
        endpoint_id=str(comment.endpoint_id),
        user_id=str(comment.user_id),
        user_name=user.full_name if user else None,
        content=comment.content,
        parent_id=str(comment.parent_id) if comment.parent_id else None,
        line_number=comment.line_number,
        is_resolved=comment.is_resolved,
        created_at=comment.created_at
    )


@router.post("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Mark a comment as resolved."""
    result = await db.execute(
        select(EndpointComment).where(EndpointComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment.is_resolved = True
    comment.resolved_by_id = current_user.get("id")
    comment.resolved_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Comment resolved"}


# ==================== Change Request Endpoints ====================

@router.get("/endpoints/{endpoint_id}/changes", response_model=List[ChangeRequestResponse])
async def list_change_requests(
    endpoint_id: str,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List change requests for an endpoint."""
    query = select(ChangeRequest, User).join(
        User, ChangeRequest.author_id == User.id
    ).where(ChangeRequest.endpoint_id == endpoint_id)
    
    if status_filter:
        query = query.where(ChangeRequest.status == status_filter)
    
    result = await db.execute(query.order_by(ChangeRequest.created_at.desc()))
    rows = result.all()
    
    return [
        ChangeRequestResponse(
            id=str(cr.id),
            endpoint_id=str(cr.endpoint_id),
            author_id=str(cr.author_id),
            author_name=user.full_name,
            title=cr.title,
            description=cr.description,
            changes=cr.changes,
            status=cr.status,
            reviewer_id=str(cr.reviewer_id) if cr.reviewer_id else None,
            reviewed_at=cr.reviewed_at,
            review_comment=cr.review_comment,
            created_at=cr.created_at
        )
        for cr, user in rows
    ]


@router.post("/endpoints/{endpoint_id}/changes", response_model=ChangeRequestResponse)
async def create_change_request(
    endpoint_id: str,
    data: ChangeRequestCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a change request for an endpoint."""
    user_id = current_user.get("id")
    
    change_request = ChangeRequest(
        endpoint_id=endpoint_id,
        author_id=user_id,
        title=data.title,
        description=data.description,
        changes=data.changes
    )
    
    db.add(change_request)
    await db.commit()
    await db.refresh(change_request)
    
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    return ChangeRequestResponse(
        id=str(change_request.id),
        endpoint_id=str(change_request.endpoint_id),
        author_id=str(change_request.author_id),
        author_name=user.full_name if user else None,
        title=change_request.title,
        description=change_request.description,
        changes=change_request.changes,
        status=change_request.status,
        reviewer_id=None,
        reviewed_at=None,
        review_comment=None,
        created_at=change_request.created_at
    )


@router.post("/changes/{change_id}/review")
async def review_change_request(
    change_id: str,
    action: str,  # "approve" or "reject"
    comment: Optional[str] = None,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Approve or reject a change request."""
    result = await db.execute(
        select(ChangeRequest).where(ChangeRequest.id == change_id)
    )
    change_request = result.scalar_one_or_none()
    
    if not change_request:
        raise HTTPException(status_code=404, detail="Change request not found")
    
    if action == "approve":
        change_request.status = ChangeStatus.APPROVED.value
    elif action == "reject":
        change_request.status = ChangeStatus.REJECTED.value
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")
    
    change_request.reviewer_id = current_user.get("id")
    change_request.reviewed_at = datetime.utcnow()
    change_request.review_comment = comment
    
    await db.commit()
    
    return {"message": f"Change request {action}d", "status": change_request.status}
