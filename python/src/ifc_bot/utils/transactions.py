import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from .db import AsyncSessionLocal
from .models import Offer, Player, Club, Contract, Transfer, BudgetTransaction, AuditLog

async def finalize_offer(offer_id: int, bot):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            offer = await session.get(Offer, offer_id)
            if not offer or offer.status != 'PENDING':
                return
            player = await session.get(Player, offer.to_player_id)
            buyer = await session.get(Club, offer.from_club_id) if offer.from_club_id else None
            seller = await session.get(Club, player.club_id) if player.club_id else None
            # check buyer budget
            fee = offer.amount or 0
            if buyer and fee > 0 and buyer.budget < fee:
                offer.status = 'CANCELLED'
                session.add(offer)
                await session.commit()
                return
            # move money
            if buyer and fee > 0:
                buyer.budget -= fee
                session.add(buyer)
                if seller:
                    seller.budget = (seller.budget or 0) + fee
                    session.add(seller)
                bt = BudgetTransaction(club_id=buyer.id, type='TRANSFER_OUT', amount=-fee, details=f'Offer {offer.id}')
                session.add(bt)
                if seller:
                    bt2 = BudgetTransaction(club_id=seller.id, type='TRANSFER_IN', amount=fee, details=f'Offer {offer.id}')
                    session.add(bt2)
            # create transfer record
            tr = Transfer(player_id=player.id, from_club_id=seller.id if seller else None, to_club_id=buyer.id if buyer else None, fee=fee)
            session.add(tr)
            # end previous contracts
            # create new contract
            contract = Contract(player_id=player.id, club_id=buyer.id if buyer else offer.from_club_id, status='ACTIVE')
            session.add(contract)
            # update player club
            player.club_id = buyer.id if buyer else offer.from_club_id
            session.add(player)
            offer.status = 'ACCEPTED'
            session.add(offer)
            al = AuditLog(actor_id='system', action='OFFER_FINALIZED', details=f'Offer {offer.id}')
            session.add(al)
        # after commit, try announce
        # send signings announcement if configured
        # best-effort: use SIGNINGS_CHANNEL_ID env var
        import os
        channel_id = os.getenv('SIGNINGS_CHANNEL_ID')
        if channel_id and player.discord_id:
            chan = bot.get_channel(int(channel_id))
            if chan:
                try:
                    await chan.send(f"Signing: <@{player.discord_id}> -> {buyer.name if buyer else 'Unknown'} (fee: {fee})")
                except Exception:
                    pass
