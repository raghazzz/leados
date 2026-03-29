from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# This creates the actual connection to PostgreSQL
# Think of it like dialing a phone number to the database
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # if DEBUG=true, prints every database query in terminal
)

# This is a "session factory" — it creates new sessions when needed
# A session is like a conversation with the database
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# All your database tables will inherit from this Base class
class Base(DeclarativeBase):
    pass

# This creates all your tables in PostgreSQL if they don't exist yet
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# This is used by every API endpoint that needs the database
# FastAPI calls this automatically before each request
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session        # gives the session to the endpoint
            await session.commit() # saves any changes
        except Exception:
            await session.rollback() # undoes changes if something went wrong
            raise
        finally:
            await session.close() # always close the connection when done