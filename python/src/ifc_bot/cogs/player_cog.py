from discord.ext import commands
from discord import app_commands, Interaction
from ..db import AsyncSessionLocal
from ..models import Player, Club, AuditLog
from sqlalchemy.future import select

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='player', description='View your or another player profile')
    @app_commands.describe(target='Mention the player (optional)')
    async def player(self, interaction: Interaction, target: str = None):
        # target is discord id or None
        user_id = str(interaction.user.id) if not target else target
        async with AsyncSessionLocal() as session:
            q = await session.execute(select(Player).where(Player.discord_id == user_id).options())
            p = q.scalars().first()
            if not p:
                await interaction.response.send_message('Player not found.', ephemeral=True)
                return
            club_name = 'Free Agent' if not p.club_id else str(p.club_id)
            await interaction.response.send_message(f'Player {p.discord_id} OVR:{p.overall} Club:{club_name} Value:{p.market_value}', ephemeral=True)

    @app_commands.command(name='editplayer', description='Edit your player profile')
    async def editplayer(self, interaction: Interaction, roblox: str = None, country: str = None, position: str = None, overall: int = None):
        async with AsyncSessionLocal() as session:
            q = await session.execute(select(Player).where(Player.discord_id == str(interaction.user.id)))
            p = q.scalars().first()
            if not p:
                p = Player(discord_id=str(interaction.user.id))
                session.add(p)
            if roblox:
                p.roblox = roblox
            if country:
                p.country = country
            if position:
                p.position = position
            if overall is not None:
                p.overall = overall
            await session.commit()
            await interaction.response.send_message('Profile updated.', ephemeral=True)
