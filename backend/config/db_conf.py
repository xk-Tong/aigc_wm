from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# db_url = "mysql+aiomysql://root:200212@localhost:3306/aigc_wm"
db_url = "mysql+aiomysql://aigc_admin:200212@10.1.115.170:3306/aigc_wm"
async_engine = create_async_engine(
    db_url, 
    echo=False,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()