from .db import AsyncSessionLocal
from .models import Setting

async def get_setting_value(key: str):
    async with AsyncSessionLocal() as session:
        s = await session.get(Setting, key)
        return s.value if s else None

async def set_setting_value(key: str, value: str):
    async with AsyncSessionLocal() as session:
        s = await session.get(Setting, key)
        if s:
            s.value = value
            session.add(s)
            await session.commit()
            return s
        else:
            s = Setting(key=key, value=value)
            session.add(s)
            await session.commit()
            return s
