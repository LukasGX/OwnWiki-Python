from fastapi import Depends, Header, HTTPException
async def get_api_key(api_key: str = Header(None)):
    return True # DUMMY IMPLEMENTATION