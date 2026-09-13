# import asyncio
# from app.core.database import Base, engine
# import app.models


# async def create_tables():
#     async with engine.begin() as conn:
#         print("Creating all tables in PostgreSQL...")
#         await conn.run_sync(Base.metadata.create_all)
#         print("All tables, foreign keys, and check constraints successfully created!")
#     await engine.dispose()


# if __name__ == "__main__":
#     asyncio.run(create_tables())