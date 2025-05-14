from aiohttp import ClientSession, FormData

from config import SITE_API

session = None


async def init_session():
    global session
    if session is None or session.closed:
        session = ClientSession()


async def close_session():
    global session
    if isinstance(session, ClientSession):
        if session and not session.closed:
            await session.close()


async def fetch_post(endpoint, payload, file_bytes=None, field_name='file', filename=None, content_type=None):
    url = f"{SITE_API}{endpoint}"

    if isinstance(session, ClientSession):
        if file_bytes is not None:
            form = FormData()
            for key, value in payload.items():
                form.add_field(key, str(value))
            form.add_field(
                field_name,
                file_bytes,
                filename=filename,
                content_type=content_type,
            )
            async with session.post(url, data=form) as resp:
                return await resp.json(), resp.status
        else:
            async with session.post(url, json=payload) as resp:
                return await resp.json(), resp.status
    return None
