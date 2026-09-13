from discord.ext import commands
from discord import app_commands
from discord import Interaction
from ..db import AsyncSessionLocal
from ..models import Club, AuditLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

class CoreCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='config', description='View settings (admin only)')
    async def config(self, interaction: Interaction):
        # simple config viewer
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(5))
            items = res.scalars().all()
        text = '\n'.join([f'{i.action}: {i.details}' for i in items]) or 'No audit logs yet.'
        await interaction.response.send_message(f'Latest audit logs:\n{text}', ephemeral=True)

    @app_commands.command(name='createteam', description='Create a club')
    @app_commands.describe(name='Club name', logo='Logo URL', budget='Starting budget')
    async def createteam(self, interaction: Interaction, name: str, logo: str = None, budget: int = 0):
        # only allow guild admins
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('Only server administrators may create clubs.', ephemeral=True)
            return
        async with AsyncSessionLocal() as session:
            # check exists
            q = await session.execute(select(Club).where(Club.name == name))
            if q.scalars().first():
                await interaction.response.send_message('Club with that name already exists.', ephemeral=True)
                return
            club = Club(name=name, logo=logo, budget=budget)
            session.add(club)
            await session.commit()
            await session.refresh(club)
            # audit
            al = AuditLog(actor_id=str(interaction.user.id), action='CLUB_CREATED', details=f'Club {club.id}:{club.name}')
            session.add(al)
            await session.commit()
        await interaction.response.send_message(f'Created club {club.name} (id {club.id})')
