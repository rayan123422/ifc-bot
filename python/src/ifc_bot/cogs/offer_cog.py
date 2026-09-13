import discord
from discord.ext import commands
from discord import app_commands, Interaction
from ..db import AsyncSessionLocal
from ..models import Player, Offer, Club, AuditLog
from sqlalchemy.future import select
from ..utils.transactions import finalize_offer

class OfferView(discord.ui.View):
    def __init__(self, offer_id: int):
        super().__init__(timeout=None)
        self.offer_id = offer_id

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.success, custom_id='offer_accept')
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        # mark offer accepted and attempt finalize
        async with AsyncSessionLocal() as session:
            q = await session.execute(select(Offer).where(Offer.id == self.offer_id))
            offer = q.scalars().first()
            if not offer:
                await interaction.response.send_message('Offer not found.', ephemeral=True)
                return
            # only the player may accept
            player = await session.get(Player, offer.to_player_id)
            if str(interaction.user.id) != str(player.discord_id):
                await interaction.response.send_message('Only the offered player may accept.', ephemeral=True)
                return
            offer.player_accepted = True
            session.add(offer)
            await session.commit()
        await interaction.response.send_message('You accepted the offer. Finalizing...', ephemeral=True)
        await finalize_offer(self.offer_id, interaction.client)

    @discord.ui.button(label='Reject', style=discord.ButtonStyle.danger, custom_id='offer_reject')
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with AsyncSessionLocal() as session:
            offer = await session.get(Offer, self.offer_id)
            offer.status = 'REJECTED'
            session.add(offer)
            await session.commit()
        await interaction.response.send_message('You rejected the offer.', ephemeral=True)

class OfferCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='offer', description='Create an offer for a player')
    @app_commands.describe(target='Mention the player', amount='Amount (0 for free)')
    async def offer(self, interaction: Interaction, target: str, amount: int = 0, message: str = ''):
        # manager must be manager of some club
        async with AsyncSessionLocal() as session:
            q = await session.execute(select(Club).where(Club.manager_id == str(interaction.user.id)))
            club = q.scalars().first()
            if not club:
                await interaction.response.send_message('You must be a club manager to send offers.', ephemeral=True)
                return
            # find player by discord id string
            q2 = await session.execute(select(Player).where(Player.discord_id == target))
            player = q2.scalars().first()
            if not player:
                player = Player(discord_id=target)
                session.add(player)
                await session.commit()
                await session.refresh(player)
            offer = Offer(type='FREE' if not player.club_id else 'TRANSFER', from_club_id=club.id, to_player_id=player.id, amount=amount, message=message)
            session.add(offer)
            await session.commit()
            await session.refresh(offer)
            # audit
            al = AuditLog(actor_id=str(interaction.user.id), action='OFFER_CREATED', details=f'Offer {offer.id}')
            session.add(al)
            await session.commit()
        # DM the player with the offer embed and view
        try:
            user = await self.bot.fetch_user(int(target))
            embed = discord.Embed(title=f'Offer from {club.name}', description=message or 'You have an offer')
            embed.add_field(name='Amount', value=str(amount), inline=True)
            view = OfferView(offer.id)
            await user.send(embed=embed, view=view)
        except Exception:
            pass
        await interaction.response.send_message(f'Offer {offer.id} created and sent.', ephemeral=True)
