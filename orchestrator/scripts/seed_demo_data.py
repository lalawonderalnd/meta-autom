"""Seed script to populate database with demo data for testing."""

import asyncio
import os
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import text

from accfarm_shared.db_models import (
    Base,
    Client as ClientModel,
    Device as DeviceModel,
    Proxy as ProxyModel,
    Account as AccountModel,
    Job as JobModel,
)
from accfarm_shared.enums import (
    AccountStatus,
    DeviceStatus,
    JobStatus,
    JobKind,
    Platform,
)
from accfarm_shared.encryption import encrypt_password


async def seed_database():
    """Seed the database with demo data."""
    
    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/accfarm"
    )
    
    # Create engine
    engine = create_async_engine(database_url, echo=True)
    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    try:
        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✓ Database tables created")
        
        async with async_session_factory() as db:
            # 1. Create demo clients
            client1 = ClientModel(
                id=uuid4(),
                name="Demo Fitness Creator",
                slug="demo-fitness",
                link_in_bio="https://linktr.ee/demo-fitness",
                niche="fitness",
            )
            client2 = ClientModel(
                id=uuid4(),
                name="Demo Travel Blogger",
                slug="demo-travel",
                link_in_bio="https://linktr.ee/demo-travel",
                niche="travel",
            )
            
            db.add(client1)
            db.add(client2)
            await db.flush()
            print(f"✓ Created 2 demo clients: {client1.slug}, {client2.slug}")
            
            # 2. Create demo device
            device1 = DeviceModel(
                id=uuid4(),
                serial="RZ8M601ABCD",
                name="Pixel 7 - Rack 1 Slot 1",
                ip_address="192.168.1.42",
                adb_port=5555,
                android_version="14",
                manufacturer="Google",
                model="Pixel 7",
                status=DeviceStatus.ONLINE,
                max_clones=15,
                current_clone_count=3,
            )
            
            db.add(device1)
            await db.flush()
            print(f"✓ Created demo device: {device1.name}")
            
            # 3. Create demo proxies (placeholder - real ones need actual credentials)
            proxy1 = ProxyModel(
                id=uuid4(),
                provider="iproyal",
                protocol="http",
                host="geo.iproyal.com",
                port=12321,
                username="user-demo1-country-de-session-abc123-lifetime-720h",
                country_code="DE",
                city="Berlin",
                carrier="Deutsche Telekom",
                sticky_session_id="abc123",
                is_alive=True,
            )
            proxy2 = ProxyModel(
                id=uuid4(),
                provider="iproyal",
                protocol="http",
                host="geo.iproyal.com",
                port=12321,
                username="user-demo2-country-us-session-def456-lifetime-720h",
                country_code="US",
                city="New York",
                carrier="T-Mobile",
                sticky_session_id="def456",
                is_alive=True,
            )
            
            db.add(proxy1)
            db.add(proxy2)
            await db.flush()
            print(f"✓ Created 2 demo proxies")
            
            # 4. Create demo accounts
            # Encrypt demo passwords
            password1_encrypted = encrypt_password("DemoPassword123!")
            password2_encrypted = encrypt_password("DemoPassword456!")
            
            account1 = AccountModel(
                id=uuid4(),
                platform=Platform.INSTAGRAM,
                username="demo_fitness_account_1",
                password_encrypted=password1_encrypted,
                package_name="com.instagram.androidp1",
                device_id=device1.id,
                client_id=client1.id,
                status=AccountStatus.WARMING,
                warmup_day=3,
                posts_count=5,
                followers_count=127,
                following_count=89,
                proxy_id=proxy1.id,
                identity={
                    "android_id": "abc123def456",
                    "imei": "123456789012345",
                    "wifi_mac": "02:00:00:00:00:00",
                },
                bio="Fitness enthusiast 💪 | Demo account",
                display_name="Demo Fitness",
                health_score=0.95,
            )
            
            account2 = AccountModel(
                id=uuid4(),
                platform=Platform.INSTAGRAM,
                username="demo_travel_wanderer",
                password_encrypted=password2_encrypted,
                package_name="com.instagram.androidp2",
                device_id=device1.id,
                client_id=client2.id,
                status=AccountStatus.ACTIVE,
                warmup_day=7,
                posts_count=23,
                followers_count=542,
                following_count=301,
                proxy_id=proxy2.id,
                identity={
                    "android_id": "def456ghi789",
                    "imei": "987654321098765",
                    "wifi_mac": "02:00:00:00:00:01",
                },
                bio="✈️ Travel blogger | Demo account",
                display_name="Demo Traveler",
                health_score=0.98,
            )
            
            # Account in cooldown for testing
            account3 = AccountModel(
                id=uuid4(),
                platform=Platform.INSTAGRAM,
                username="demo_test_cooldown",
                password_encrypted=password1_encrypted,
                package_name="com.instagram.androidp3",
                device_id=device1.id,
                client_id=None,
                status=AccountStatus.COOLDOWN,
                warmup_day=5,
                posts_count=12,
                followers_count=234,
                following_count=156,
                proxy_id=proxy1.id,
                health_score=0.75,
            )
            
            db.add(account1)
            db.add(account2)
            db.add(account3)
            await db.flush()
            print(f"✓ Created 3 demo accounts: {account1.username}, {account2.username}, {account3.username}")
            
            # 5. Create demo jobs
            job1 = JobModel(
                id=uuid4(),
                kind=JobKind.WARMUP_SESSION,
                account_id=account1.id,
                device_id=device1.id,
                status=JobStatus.SUCCESS,
                priority=5,
                payload={"day": 3, "actions": ["scroll", "like", "follow"]},
                result={"actions_completed": 15, "duration_seconds": 420},
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
            )
            
            job2 = JobModel(
                id=uuid4(),
                kind=JobKind.ENGAGE_HASHTAG,
                account_id=account2.id,
                device_id=device1.id,
                status=JobStatus.QUEUED,
                priority=6,
                payload={"hashtags": ["#travel", "#wanderlust"], "target_likes": 20},
                scheduled_for=datetime.now(timezone.utc),
            )
            
            db.add(job1)
            db.add(job2)
            await db.flush()
            print(f"✓ Created 2 demo jobs")
            
            # Commit all changes
            await db.commit()
            
            print("\n✅ Database seeded successfully!")
            print(f"\nDemo Data Summary:")
            print(f"  - Clients: 2 (demo-fitness, demo-travel)")
            print(f"  - Devices: 1 (Pixel 7)")
            print(f"  - Proxies: 2 (DE, US)")
            print(f"  - Accounts: 3 (WARMING, ACTIVE, COOLDOWN)")
            print(f"  - Jobs: 2 (1 completed, 1 queued)")
            print(f"\nYou can now start the orchestrator and access the API at http://localhost:8000")
            
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
