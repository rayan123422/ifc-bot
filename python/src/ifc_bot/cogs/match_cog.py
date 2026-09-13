from discord.ext import commands
from discord import app_commands, Interaction
from ..db import AsyncSessionLocal
from ..models import Match, AuditLog
from sqlalchemy.future import select

class MatchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='schedule', description='Schedule a match')
    async def schedule(self, interaction: Interaction, home: str, away: str, when: str, competition: str = None):
        # simple parser for ISO datetime
        import datetime
        try:
            scheduled = datetime.datetime.fromisoformat(when)
        except Exception:
            await interaction.response.send_message('Invalid datetime format. Use ISO format.', ephemeral=True)
            return
        async with AsyncSessionLocal() as session:
            m = Match(home_club_id=int(home), away_club_id=int(away), scheduled_for=scheduled, competition=competition)
            session.add(m)
            al = AuditLog(actor_id=str(interaction.user.id), action='MATCH_SCHEDULED', details=f'Match {home} vs {away} at {when}')
            session.add(al)
            await session.commit()
        await interaction.response.send_message('Match scheduled.', ephemeral=True)

    @app_commands.command(name='result', description='Record a match result')
    async def result(self, interaction: Interaction, match_id: int, home_goals: int, away_goals: int):
        # permission check: referee or admin
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('Only admins/referees may submit results (referee role not implemented).', ephemeral=True)
            return
        async with AsyncSessionLocal() as session:
            m = await session.get(Match, match_id)
            if not m:
                await interaction.response.send_message('Match not found.', ephemeral=True)
                return
            m.home_goals = home_goals
            m.away_goals = away_goals
            m.status = 'COMPLETED'
            session.add(m)
            al = AuditLog(actor_id=str(interaction.user.id), action='MATCH_RESULT', details=f'Match {match_id} {home_goals}-{away_goals}')
            session.add(al)
            await session.commit()
        await interaction.response.send_message(f'Result recorded for match {match_id}: {home_goals}-{away_goals}', ephemeral=True)
