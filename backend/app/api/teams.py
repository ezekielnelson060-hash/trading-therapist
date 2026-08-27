from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models.teams import Team, TeamMember
from app.services.tilt import full_behavioral_snapshot

router = APIRouter()


class TeamCreate(BaseModel):
    name: str


class InviteBody(BaseModel):
    email: EmailStr
    role: str = "trader"


@router.post("/")
async def create_team(
    body: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = Team(name=body.name, owner_user_id=current_user.id)
    db.add(team)
    await db.flush()
    db.add(TeamMember(team_id=team.id, user_id=current_user.id, role="owner"))
    await db.flush()
    return {"id": team.id, "name": team.name}


@router.get("/")
async def my_teams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TeamMember).where(TeamMember.user_id == current_user.id))
    memberships = list(result.scalars().all())
    out = []
    for m in memberships:
        tr = await db.execute(select(Team).where(Team.id == m.team_id))
        team = tr.scalar_one_or_none()
        if team:
            out.append({"id": team.id, "name": team.name, "role": m.role})
    return out


@router.post("/{team_id}/invite")
async def invite_member(
    team_id: str,
    body: InviteBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _require_owner(db, team_id, current_user.id)
    ur = await db.execute(select(User).where(User.email == body.email))
    user = ur.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User must register first, then invite by email.")
    existing = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.user_id == user.id)
    )
    if existing.scalar_one_or_none():
        return {"status": "already_member"}
    db.add(TeamMember(team_id=team.id, user_id=user.id, role=body.role))
    await db.flush()
    return {"status": "ok", "user_id": user.id, "email": user.email, "role": body.role}


@router.get("/{team_id}/risk")
async def team_risk(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_member(db, team_id, current_user.id)
    result = await db.execute(select(TeamMember).where(TeamMember.team_id == team_id))
    members = list(result.scalars().all())
    rows = []
    high = 0
    for m in members:
        ur = await db.execute(select(User).where(User.id == m.user_id))
        user = ur.scalar_one_or_none()
        if not user:
            continue
        snap = await full_behavioral_snapshot(db, user.id)
        tilt = snap.get("tilt") or {}
        score = tilt.get("tilt_score") or 0
        if score >= 70:
            high += 1
        rows.append(
            {
                "user_id": user.id,
                "email": user.email,
                "name": user.full_name,
                "role": m.role,
                "tilt_score": score,
                "state_label": tilt.get("state_label"),
                "do_not_trade": tilt.get("do_not_trade"),
                "today_trades": tilt.get("today_trades"),
                "locked": bool(getattr(user, "trading_locked", False)),
            }
        )
    rows.sort(key=lambda r: r["tilt_score"], reverse=True)
    return {
        "team_id": team_id,
        "traders": rows,
        "high_risk_count": high,
        "message": "Aggregated behavioral risk across the desk — not a P&L leaderboard.",
    }


async def _require_member(db, team_id, user_id):
    r = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
    )
    if not r.scalar_one_or_none():
        raise HTTPException(403, "Not a team member")


async def _require_owner(db, team_id, user_id):
    r = await db.execute(select(Team).where(Team.id == team_id))
    team = r.scalar_one_or_none()
    if not team:
        raise HTTPException(404, "Team not found")
    if team.owner_user_id != user_id:
        raise HTTPException(403, "Owner only")
    return team
