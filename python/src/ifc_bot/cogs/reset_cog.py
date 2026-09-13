from discord.ext import commands
from discord import app_commands, Interaction
from ..db import AsyncSessionLocal
from ..models import AuditLog
from sqlalchemy.future import select
import secrets

class ResetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='reset', description='Request a reset (admin only)')
    async def reset(self, interaction: Interaction, scope: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('Only admins can request a reset.', ephemeral=True)
            return
        code = secrets.token_hex(3).upper()
        al = AuditLog(actor_id=str(interaction.user.id), action='RESET_REQUEST', details=f'{scope}:{code}')
        async with AsyncSessionLocal() as session:
            session.add(al)
            await session.commit()
        await interaction.response.send_message(f'Reset requested for {scope}. To confirm, run /reset_confirm code:{code}', ephemeral=True)

    @app_commands.command(name='reset_confirm', description='Confirm reset with code')
    async def reset_confirm(self, interaction: Interaction, code: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('Only admins can confirm a reset.', ephemeral=True)
            return
        async with AsyncSessionLocal() as session:
            q = await session.execute(select(AuditLog).where(AuditLog.details.contains(code)).where(AuditLog.action == 'RESET_REQUEST'))
            req = q.scalars().first()
            if not req:
                await interaction.response.send_message('Reset token not found or expired.', ephemeral=True)
                return
            scope = req.details.split(':')[0]
            # perform reset scopes (dangerous)
            if scope == 'everything':
                # delete many tables
                await session.execute('DELETE FROM transfer')
                await session.execute('DELETE FROM offer')
                await session.execute('DELETE FROM loan')
                await session.execute('DELETE FROM contract')
                await session.execute('DELETE FROM player_stats')
                await session.execute('DELETE FROM player_value_history')
                await session.execute('DELETE FROM player')
                await session.execute('DELETE FROM lfp_interest')
                await session.execute('DELETE FROM lfp_post')
                await session.commit()
                al = AuditLog(actor_id=str(interaction.user.id), action='RESET_DONE', details='Everything erased (except settings)')
                session.add(al)
                await session.commit()
                await interaction.response.send_message('Reset performed: everything removed (except settings).', ephemeral=True)
            else:
                await interaction.response.send_message('Reset scope handler not implemented yet.', ephemeral=True)
