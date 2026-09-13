from ..models import Offer, Player, Club
from .db import AsyncSessionLocal
from .utils.roles import add_role_to_member, remove_role_from_member
import os

async def finalize_offer(offer_id: int, bot):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            offer = await session.get(Offer, offer_id)
            if not offer or offer.status != 'PENDING':
                return
            player = await session.get(Player, offer.to_player_id)
            buyer = await session.get(Club, offer.from_club_id) if offer.from_club_id else None
            seller = await session.get(Club, player.club_id) if player.club_id else None
            fee = offer.amount or 0
            if buyer and fee > 0 and (buyer.budget or 0) < fee:
                offer.status = 'CANCELLED'
                session.add(offer)
                return
            if buyer and fee > 0:
                buyer.budget = (buyer.budget or 0) - fee
                session.add(buyer)
                if seller:
                    seller.budget = (seller.budget or 0) + fee
                    session.add(seller)
                bt = session.execute
                await session.flush()
            tr = None
            if buyer:
                tr = await session.execute(session.bind.insert)
            # create transfer
            from datetime import datetime
            from .models import Transfer, Contract, AuditLog
            tr = Transfer(player_id=player.id, from_club_id=seller.id if seller else None, to_club_id=buyer.id if buyer else None, fee=fee, created_at=datetime.utcnow())
            session.add(tr)
            # end previous contracts
            await session.execute("UPDATE contract SET status='TERMINATED', end_date=CURRENT_TIMESTAMP WHERE player_id = :pid AND status='ACTIVE'", {'pid': player.id})
            contract = Contract(player_id=player.id, club_id=buyer.id if buyer else offer.from_club_id, status='ACTIVE')
            session.add(contract)
            # update player
            player.club_id = buyer.id if buyer else offer.from_club_id
            session.add(player)
            offer.status = 'ACCEPTED'
            session.add(offer)
            al = AuditLog(actor_id='system', action='OFFER_FINALIZED', details=f'Offer {offer.id}')
            session.add(al)
        # after commit
        # role updates
        try:
            if player.discord_id:
                # remove old role
                if seller and seller.role_id:
                    await remove_role_from_member(bot, str(player.discord_id), seller.role_id)
                if buyer and buyer.role_id:
                    await add_role_to_member(bot, str(player.discord_id), buyer.role_id)
        except Exception:
            pass
        # announcement
        channel_id = os.getenv('SIGNINGS_CHANNEL_ID')
        if channel_id:
            try:
                ch = bot.get_channel(int(channel_id))
                if ch:
                    await ch.send(f"Signing: <@{player.discord_id}> -> {buyer.name if buyer else 'Unknown'} (fee: {fee})")
            except Exception:
                pass
