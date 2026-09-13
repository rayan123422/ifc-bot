from discord.ext import commands
from discord import app_commands, Interaction
from ..db import AsyncSessionLocal
from ..models import Club, AuditLog
from sqlalchemy.future import select

class ManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='manager', description='Appoint or remove managers (admin only)')
    async def manager(self, interaction: Interaction, action: str, club_name: str = None, user_id: str = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('Only administrators may appoint managers.', ephemeral=True)
            return
        if action == 'appoint':
            async with AsyncSessionLocal() as session:
                q = await session.execute(select(Club).where(Club.name == club_name))
                club = q.scalars().first()
                if not club:
                    await interaction.response.send_message('Club not found.', ephemeral=True)
                    return
                club.manager_id = user_id
                session.add(club)
                al = AuditLog(actor_id=str(interaction.user.id), action='MANAGER_APPOINT', details=f'Club {club.id} -> {user_id}')
                session.add(al)
                await session.commit()
            await interaction.response.send_message(f'Appointed <@{user_id}> as manager of {club.name}.', ephemeral=True)
        elif action == 'remove':
            async with AsyncSessionLocal() as session:
                q = await session.execute(select(Club).where(Club.name == club_name))
                club = q.scalars().first()
                if not club:
                    await interaction.response.send_message('Club not found.', ephemeral=True)
                    return
                club.manager_id = None
                session.add(club)
                al = AuditLog(actor_id=str(interaction.user.id), action='MANAGER_REMOVE', details=f'Club {club.id}')
                session.add(al)
                await session.commit()
            await interaction.response.send_message(f'Removed manager from {club.name}.', ephemeral=True)
        elif action == 'view':
            async with AsyncSessionLocal() as session:
                q = await session.execute(select(Club).where(Club.name == club_name))
                club = q.scalars().first()
                if not club:
                    await interaction.response.send_message('Club not found.', ephemeral=True)
                    return
            await interaction.response.send_message(f'Manager for {club.name}: {club.manager_id or "None"}', ephemeral=True)
        else:
            await interaction.response.send_message('Invalid action. Use appoint/remove/view', ephemeral=True)
