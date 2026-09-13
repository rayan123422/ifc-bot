from discord.ext import commands
from discord import app_commands, Interaction
from ..db import AsyncSessionLocal
from ..models import League, Club, Match
from sqlalchemy.future import select

class TableCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='table', description='Show league table')
    async def table(self, interaction: Interaction, league_name: str = None):
        async with AsyncSessionLocal() as session:
            if league_name:
                q = await session.execute(select(League).where(League.name == league_name))
                league = q.scalars().first()
                if not league:
                    await interaction.response.send_message('League not found.', ephemeral=True)
                    return
                clubs = await session.execute(select(Club).where(Club.league_id == league.id))
                clubs = clubs.scalars().all()
            else:
                q = await session.execute(select(Club))
                clubs = q.scalars().all()
            matches_q = await session.execute(select(Match).where(Match.status == 'COMPLETED'))
            matches = matches_q.scalars().all()
            standings = {c.id: {'club': c, 'played':0,'win':0,'draw':0,'loss':0,'gf':0,'ga':0,'pts':0} for c in clubs}
            for m in matches:
                if m.home_club_id not in standings or m.away_club_id not in standings:
                    continue
                h = standings[m.home_club_id]
                a = standings[m.away_club_id]
                h['played'] += 1; a['played'] += 1
                h['gf'] += m.home_goals or 0; h['ga'] += m.away_goals or 0
                a['gf'] += m.away_goals or 0; a['ga'] += m.home_goals or 0
                if (m.home_goals or 0) > (m.away_goals or 0):
                    h['win'] += 1; a['loss'] += 1; h['pts'] += 3
                elif (m.home_goals or 0) < (m.away_goals or 0):
                    a['win'] += 1; h['loss'] += 1; a['pts'] += 3
                else:
                    h['draw'] +=1; a['draw'] +=1; h['pts'] +=1; a['pts'] +=1
            rows = sorted(standings.values(), key=lambda x: (x['pts'], x['gf'] - x['ga']), reverse=True)
            lines = [f"{i+1}. {r['club'].name} P:{r['played']} W:{r['win']} D:{r['draw']} L:{r['loss']} GF:{r['gf']} GA:{r['ga']} GD:{r['gf']-r['ga']} PTS:{r['pts']}" for i,r in enumerate(rows)]
            await interaction.response.send_message('\n'.join(lines) if lines else 'No completed matches yet.', ephemeral=True)
