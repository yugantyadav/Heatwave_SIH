import asyncio
import csv
import sys
sys.path.insert(0, '/Users/Yugant/Desktop/hackathon/Heatwave/backend')

from sqlalchemy.ext.asyncio import create_async_engine
from app.models import Ward
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL)

async def seed_wards():
    async with engine.begin() as conn:
        await conn.run_sync(Ward.__table__.create)
        wards = [
            {"ward_code": "1", "ward_name": "Ward 1", "zone": "South Mumbai", "district": "Mumbai City", "total_population": 99427, "elderly_percent": 8.5},
            {"ward_code": "2", "ward_name": "Ward 2", "zone": "South Mumbai", "district": "Mumbai City", "total_population": 185572, "elderly_percent": 9.2},
            {"ward_code": "3", "ward_name": "Ward 3", "zone": "South Mumbai", "district": "Mumbai City", "total_population": 272240, "elderly_percent": 10.1},
            {"ward_code": "4", "ward_name": "Ward 4", "zone": "Island", "district": "Mumbai City", "total_population": 57426, "elderly_percent": 7.8},
            {"ward_code": "5", "ward_name": "Ward 5", "zone": "Island", "district": "Mumbai City", "total_population": 99002, "elderly_percent": 8.9},
        ]
        for w in wards:
            await conn.execute(Ward.__table__.insert().values(**w))
        await conn.commit()
    print("Seeded 5 wards successfully")

if __name__ == "__main__":
    asyncio.run(seed_wards())