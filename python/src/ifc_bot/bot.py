import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from .cogs.core import CoreCog
from .cogs.player_cog import PlayerCog
from .cogs.offer_cog import OfferCog

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot ready: {bot.user} (id: {bot.user.id})')
    try:
        # sync tree to guild if provided
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            await bot.tree.sync(guild=guild)
            print('Synced commands to guild', GUILD_ID)
        else:
            await bot.tree.sync()
            print('Synced global commands')
    except Exception as e:
        print('Failed to sync commands', e)


def main():
    # add cogs
    bot.add_cog(CoreCog(bot))
    bot.add_cog(PlayerCog(bot))
    bot.add_cog(OfferCog(bot))
    bot.run(DISCORD_TOKEN)

if __name__ == '__main__':
    main()
