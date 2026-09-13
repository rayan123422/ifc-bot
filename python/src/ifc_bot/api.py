from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from .db import AsyncSessionLocal
from .models import Player, Club
from sqlalchemy.future import select

app = FastAPI()

class PlayerSync(BaseModel):
    discord_id: str
    roblox: str | None = None
    country: str | None = None
    position: str | None = None
    overall: int | None = None
    market_value: int | None = None

@app.get('/v1/players/{player_id}')
async def get_player(player_id: int):
    async with AsyncSessionLocal() as session:
        p = await session.get(Player, player_id)
        if not p:
            raise HTTPException(status_code=404, detail='Not found')
        return { 'id': p.id, 'discord_id': p.discord_id, 'overall': p.overall, 'club_id': p.club_id }

@app.get('/v1/clubs/{club_id}')
async def get_club(club_id: int):
    async with AsyncSessionLocal() as session:
        c = await session.get(Club, club_id)
        if not c:
            raise HTTPException(status_code=404, detail='Not found')
        return { 'id': c.id, 'name': c.name, 'budget': c.budget }

@app.post('/v1/webhook/sync-player')
async def sync_player(payload: PlayerSync):
    # simple upsert
    async with AsyncSessionLocal() as session:
        q = await session.execute(select(Player).where(Player.discord_id == payload.discord_id))
        p = q.scalars().first()
        if not p:
            p = Player(discord_id=payload.discord_id, roblox=payload.roblox, country=payload.country, position=payload.position, overall=payload.overall or 0, market_value=payload.market_value or 30000)
            session.add(p)
            await session.commit()
            await session.refresh(p)
        else:
            if payload.roblox: p.roblox = payload.roblox
            if payload.country: p.country = payload.country
            if payload.position: p.position = payload.position
            if payload.overall is not None: p.overall = payload.overall
            if payload.market_value is not None: p.market_value = payload.market_value
            session.add(p)
            await session.commit()
        return {'ok': True, 'player_id': p.id}
