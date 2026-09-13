from discord.ext import commands
from discord import app_commands, Interaction
from ..db import AsyncSessionLocal
from ..models import Player, PlayerValueHistory, AuditLog
from sqlalchemy.future import select

TIERS = [30000, 60000, 150000, 450000, 1000000, 3000000]

class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='stats', description='View player stats and valuation (staff only)')
    async def stats(self, interaction: Interaction, player_id: int):
        async with AsyncSessionLocal() as session:
            p = await session.get(Player, player_id)
            if not p:
                await interaction.response.send_message('Player not found.', ephemeral=True)
                return
            # fetch value history
            q = await session.execute(select(PlayerValueHistory).where(PlayerValueHistory.player_id == p.id).order_by(PlayerValueHistory.changed_at.desc()).limit(10))
            hist = q.scalars().all()
            lines = [f'OVR:{p.overall} Value:{p.market_value} Tier:{p.valuation_tier}']
            for h in hist:
                lines.append(f'{h.changed_at}: {h.old_value} -> {h.new_value} by {h.staff_id} Reason:{h.reason}')
            await interaction.response.send_message('\n'.join(lines), ephemeral=True)

    @app_commands.command(name='change_value', description='Change player market value (staff only)')
    async def change_value(self, interaction: Interaction, player_id: int, new_value: int, reason: str):
        # permission check: StatsStaffRoleId
        from ..utils.permissions import has_role_by_setting
        ok = await has_role_by_setting(interaction, 'StatsStaffRoleId')
        if not ok:
            await interaction.response.send_message('You are not authorized to change valuations.', ephemeral=True)
            return
        async with AsyncSessionLocal() as session:
            p = await session.get(Player, player_id)
            if not p:
                await interaction.response.send_message('Player not found.', ephemeral=True)
                return
            old = p.market_value
            p.market_value = new_value
            # determine tier
            tier = max([t for t in TIERS if new_value >= t]) if new_value >= TIERS[0] else TIERS[0]
            p.valuation_tier = tier
            session.add(p)
            vh = PlayerValueHistory(player_id=p.id, old_value=old, new_value=new_value, tierBefore=None, tierAfter=tier, staff_id=str(interaction.user.id), reason=reason)
            session.add(vh)
            al = AuditLog(actor_id=str(interaction.user.id), action='VALUE_CHANGED', details=f'Player {p.id} {old}->{new_value}')
            session.add(al)
            await session.commit()
        await interaction.response.send_message(f'Player value updated: {old} -> {new_value}', ephemeral=True)
