import discord
from discord.ext import commands
from discord import app_commands, Interaction
from ..db import AsyncSessionLocal
from ..models import Loan, Player, Club, AuditLog
from sqlalchemy.future import select
from datetime import datetime, timedelta

class LoanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='loan', description='Request or list loans')
    @app_commands.describe(action='request/list', player='Player discord id', to='Loan club name', days='Duration days', fee='Loan fee')
    async def loan(self, interaction: Interaction, action: str, player: str = None, to: str = None, days: int = 7, fee: int = 0):
        if action == 'request':
            async with AsyncSessionLocal() as session:
                # ensure player exists
                q = await session.execute(select(Player).where(Player.discord_id == player))
                p = q.scalars().first()
                if not p or not p.club_id:
                    await interaction.response.send_message('Player not found or not owned.', ephemeral=True)
                    return
                owner = await session.get(Club, p.club_id)
                if str(interaction.user.id) != str(owner.manager_id):
                    await interaction.response.send_message('Only owner club manager can request a loan.', ephemeral=True)
                    return
                loan_club_q = await session.execute(select(Club).where(Club.name == to))
                loan_club = loan_club_q.scalars().first()
                if not loan_club:
                    await interaction.response.send_message('Loan target club not found.', ephemeral=True)
                    return
                start = datetime.utcnow()
                end = start + timedelta(days=days)
                ln = Loan(player_id=p.id, owner_club_id=owner.id, loan_club_id=loan_club.id, start_date=start, end_date=end, fee=fee, status='PENDING')
                session.add(ln)
                al = AuditLog(actor_id=str(interaction.user.id), action='LOAN_REQUEST', details=f'Loan {ln.id}')
                session.add(al)
                await session.commit()
                # notify receiving manager
                if loan_club.manager_id:
                    try:
                        mgr = await self.bot.fetch_user(int(loan_club.manager_id))
                        await mgr.send(f'Loan request for <@{player}> to {loan_club.name}. Use /loan list to review.').catch(lambda e: None)
                    except Exception:
                        pass
            await interaction.response.send_message(f'Loan request created for player {player}.', ephemeral=True)
        elif action == 'list':
            async with AsyncSessionLocal() as session:
                q = await session.execute(select(Loan).order_by(Loan.created_at.desc()).limit(50))
                loans = q.scalars().all()
            if not loans:
                await interaction.response.send_message('No loans found.', ephemeral=True)
                return
            lines = [f'ID:{l.id} Player:{l.player_id} From:{l.owner_club_id} To:{l.loan_club_id} Status:{l.status}' for l in loans]
            await interaction.response.send_message('\n'.join(lines), ephemeral=True)
        else:
            await interaction.response.send_message('Invalid action. Use request or list.', ephemeral=True)
