"""Prop / teams aggregated behavioral risk infrastructure."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.models.teams import Team, TeamMember
from app.services.tilt import full_behavioral_snapshot

router = APIRouter()


class TeamCreate(BaseModel):
    name: str


class InviteBody(BaseModel):
    email: str
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
    out = []
    for m in result.scalars().all():
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
    team = await _require_manager(db, team_id, current_user.id)
    ur = await db.execute(select(User).where(User.email == body.email))
    user = ur.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User must register on TiltShield first, then invite by email.")
    existing = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.user_id == user.id)
    )
    if existing.scalar_one_or_none():
        return {"status": "already_member"}
    role = body.role if body.role in ("owner", "coach", "risk_manager", "trader") else "trader"
    db.add(TeamMember(team_id=team.id, user_id=user.id, role=role))
    await db.flush()
    return {"status": "ok", "user_id": user.id, "email": user.email, "role": role}


@router.delete("/{team_id}/members/{user_id}")
async def remove_member(
    team_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _require_owner(db, team_id, current_user.id)
    if user_id == team.owner_user_id:
        raise HTTPException(400, "Cannot remove owner")
    r = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
    )
    m = r.scalar_one_or_none()
    if not m:
        raise HTTPException(404, "Member not found")
    await db.delete(m)
    await db.flush()
    return {"status": "ok"}


@router.get("/{team_id}/members")
async def list_members(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_member(db, team_id, current_user.id)
    result = await db.execute(select(TeamMember).where(TeamMember.team_id == team_id))
    rows = []
    for m in result.scalars().all():
        ur = await db.execute(select(User).where(User.id == m.user_id))
        u = ur.scalar_one_or_none()
        if u:
            rows.append({
                "user_id": u.id,
                "email": u.email,
                "name": u.full_name,
                "role": m.role,
                "plan": u.plan,
            })
    return rows


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
    high = elevated = controlled = 0
    for m in members:
        ur = await db.execute(select(User).where(User.id == m.user_id))
        user = ur.scalar_one_or_none()
        if not user:
            continue
        snap = await full_behavioral_snapshot(db, user.id)
        tilt = snap.get("tilt") or {}
        score = int(tilt.get("tilt_score") or 0)
        if score >= 70:
            high += 1
            band = "high"
        elif score >= 40:
            elevated += 1
            band = "elevated"
        else:
            controlled += 1
            band = "controlled"
        rows.append({
            "user_id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": m.role,
            "tilt_score": score,
            "state_label": tilt.get("state_label"),
            "do_not_trade": tilt.get("do_not_trade"),
            "today_trades": tilt.get("today_trades"),
            "locked": bool(getattr(user, "trading_locked", False)),
            "band": band,
            "top_signal": _top_signal(tilt),
        })
    rows.sort(key=lambda r: r["tilt_score"], reverse=True)
    return {
        "team_id": team_id,
        "traders": rows,
        "high_risk_count": high,
        "elevated_count": elevated,
        "controlled_count": controlled,
        "active_traders": len(rows),
        "message": "Aggregated behavioral risk across the desk — not a P&L leaderboard.",
    }


@router.get("/{team_id}/heatmap")
async def team_heatmap(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    risk = await team_risk(team_id, current_user, db)
    cells = [{
        "user_id": t["user_id"],
        "label": t["name"] or t["email"],
        "tilt_score": t["tilt_score"],
        "band": t["band"],
        "do_not_trade": t["do_not_trade"],
        "top_signal": t["top_signal"],
    } for t in risk["traders"]]
    return {
        "team_id": team_id,
        "summary": {
            "active": risk["active_traders"],
            "controlled": risk["controlled_count"],
            "elevated": risk["elevated_count"],
            "high": risk["high_risk_count"],
        },
        "cells": cells,
        "headline": (
            f"{risk['active_traders']} active · "
            f"{risk['controlled_count']} controlled · "
            f"{risk['elevated_count']} elevated · "
            f"{risk['high_risk_count']} high behavioral risk"
        ),
    }


@router.get("/{team_id}/high-risk")
async def high_risk_only(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    risk = await team_risk(team_id, current_user, db)
    hot = [t for t in risk["traders"] if t["tilt_score"] >= 70]
    return {
        "count": len(hot),
        "traders": hot,
        "message": "Traders showing dangerous behavioral deterioration right now.",
    }


def _top_signal(tilt: dict) -> Optional[str]:
    for s in (tilt.get("signals") or {}).values():
        if s.get("status") in ("red", "amber"):
            return f"{s.get('label')}: {s.get('detail')}"
    return None


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


async def _require_manager(db, team_id, user_id):
    r = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
    )
    m = r.scalar_one_or_none()
    tr = await db.execute(select(Team).where(Team.id == team_id))
    team = tr.scalar_one_or_none()
    if not team:
        raise HTTPException(404, "Team not found")
    if team.owner_user_id == user_id:
        return team
    if not m or m.role not in ("owner", "coach", "risk_manager"):
        raise HTTPException(403, "Manager role required")
    return team
