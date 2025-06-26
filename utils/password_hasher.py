from starlette.concurrency import run_in_threadpool
from passlib.context import CryptContext
import asyncio


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def hash_password(password: str) -> str:
    return await run_in_threadpool(pwd_context.hash, password)

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return await run_in_threadpool(pwd_context.verify, plain_password, hashed_password)


async def test():
    test_password = "<PASSWORD>"
    hashed_test_password = await hash_password(test_password)
    print(hashed_test_password)

    verified = await verify_password(test_password, hashed_test_password)
    if verified:
        print("Password verified")

if __name__ == '__main__':
    asyncio.run(test())