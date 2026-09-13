from discord import Guild, Member

async def add_role_to_member(bot, discord_id: str, role_id: str):
    # Find the guild and member where this user exists and add role
    for guild in bot.guilds:
        try:
            member = guild.get_member(int(discord_id)) or await guild.fetch_member(int(discord_id))
        except Exception:
            member = None
        if member:
            role = guild.get_role(int(role_id))
            if role and guild.me.guild_permissions.manage_roles:
                try:
                    await member.add_roles(role)
                except Exception:
                    pass
            return True
    return False

async def remove_role_from_member(bot, discord_id: str, role_id: str):
    for guild in bot.guilds:
        try:
            member = guild.get_member(int(discord_id)) or await guild.fetch_member(int(discord_id))
        except Exception:
            member = None
        if member:
            role = guild.get_role(int(role_id))
            if role and guild.me.guild_permissions.manage_roles:
                try:
                    await member.remove_roles(role)
                except Exception:
                    pass
            return True
    return False
