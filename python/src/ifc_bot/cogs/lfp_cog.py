import discord
from discord.ext import commands
from discord import app_commands, Interaction
from ..db import AsyncSessionLocal
from ..models import LfpPost, LfpInterest, Club, Player, AuditLog
from sqlalchemy.future import select

class LfpInterestView(discord.ui.View):
    def __init__(self, post_id: int):
        super().__init__(timeout=None)
        self.post_id = post_id

    @discord.ui.button(label="I'm Interested", style=discord.ButtonStyle.primary, custom_id='lfp_interest')
    async def interested(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with AsyncSessionLocal() as session:
            post = await session.get(LfpPost, self.post_id)
            if not post:
                await interaction.response.send_message('Post not found.', ephemeral=True)
                return
            # ensure player record
            q = await session.execute(select(Player).where(Player.discord_id == str(interaction.user.id)))
            player = q.scalars().first()
            if not player:
                player = Player(discord_id=str(interaction.user.id))
                session.add(player)
                await session.commit()
                await session.refresh(player)
            # prevent duplicates
            q2 = await session.execute(select(LfpInterest).where(LfpInterest.post_id == post.id).where(LfpInterest.player_id == player.id))
            if q2.scalars().first():
                await interaction.response.send_message('You already expressed interest.', ephemeral=True)
                return
            interest = LfpInterest(post_id=post.id, player_id=player.id)
            session.add(interest)
            al = AuditLog(actor_id=str(interaction.user.id), action='LFP_INTEREST', details=f'Post {post.id} Player {player.id}')
            session.add(al)
            await session.commit()
            # notify manager
            try:
                if post.manager_id:
                    user = await interaction.client.fetch_user(int(post.manager_id))
                    await user.send(f'Player <@{interaction.user.id}> expressed interest in your LFP post for {post.club_id}').catch(lambda e: None)
            except Exception:
                pass
            await interaction.response.send_message('Interest recorded. The manager has been notified.', ephemeral=True)

class LfpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='lfp', description='Create or view LFP posts')
    @app_commands.describe(action='create/list/my', position='Position needed', players='Number of players', minoverall='Minimum overall', desc='Description')
    async def lfp(self, interaction: Interaction, action: str, position: str = None, players: int = None, minoverall: int = None, desc: str = None):
        if action == 'create':
            # manager check
            async with AsyncSessionLocal() as session:
                q = await session.execute(select(Club).where(Club.manager_id == str(interaction.user.id)))
                club = q.scalars().first()
                if not club:
                    await interaction.response.send_message('Only managers may create team LFP posts.', ephemeral=True)
                    return
                post = LfpPost(club_id=club.id, manager_id=str(interaction.user.id), position=position, players_needed=players, min_overall=minoverall, description=desc)
                session.add(post)
                al = AuditLog(actor_id=str(interaction.user.id), action='LFP_CREATED', details=f'Post {post.id} Club {club.id}')
                session.add(al)
                await session.commit()
                await session.refresh(post)
            # send embed with interest button
            embed = discord.Embed(title=f'LFP • {club.name}', description=desc or '—')
            embed.add_field(name='Position', value=position or '—', inline=True)
            embed.add_field(name='Players Needed', value=str(players or '—'), inline=True)
            embed.add_field(name='Min OVR', value=str(minoverall or '—'), inline=True)
            view = LfpInterestView(post.id)
            await interaction.response.send_message('LFP created.', embed=embed, view=view)
        elif action == 'list':
            async with AsyncSessionLocal() as session:
                q = await session.execute(select(LfpPost).where(LfpPost.status == 'ACTIVE'))
                posts = q.scalars().all()
            if not posts:
                await interaction.response.send_message('No active LFP posts.', ephemeral=True)
                return
            lines = [f'ID:{p.id} Club:{p.club_id} Pos:{p.position or "—"} Need:{p.players_needed or "—"}' for p in posts]
            await interaction.response.send_message('\n'.join(lines), ephemeral=True)
        elif action == 'my':
            async with AsyncSessionLocal() as session:
                q = await session.execute(select(Club).where(Club.manager_id == str(interaction.user.id)))
                club = q.scalars().first()
                if not club:
                    await interaction.response.send_message('You are not a manager.', ephemeral=True)
                    return
                q2 = await session.execute(select(LfpPost).where(LfpPost.club_id == club.id))
                posts = q2.scalars().all()
            if not posts:
                await interaction.response.send_message('No LFP posts for your club.', ephemeral=True)
                return
            lines = [f'ID:{p.id} {p.position or "—"} Interested: (use command to view)' for p in posts]
            await interaction.response.send_message('\n'.join(lines), ephemeral=True)
        else:
            await interaction.response.send_message('Invalid action. Use create/list/my', ephemeral=True)
