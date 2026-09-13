from discord.ext import commands
from ..db import AsyncSessionLocal
from ..models import Setting
from sqlalchemy.future import select

async def is_server_admin(interaction):
    try:
        return interaction.user.guild_permissions.administrator
    except Exception:
        return False

async def has_role_by_setting(interaction, key: str):
    if not interaction.guild:
        return False
    if await is_server_admin(interaction):
        return True
    async with AsyncSessionLocal() as session:
        q = await session.execute(select(Setting).where(Setting.key == key))
        s = q.scalars().first()
        if not s or not s.value:
            return False
        role_id = s.value
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            try:
                member = await interaction.guild.fetch_member(interaction.user.id)
            except Exception:
                return False
        return any(r.id == int(role_id) for r in member.roles)
