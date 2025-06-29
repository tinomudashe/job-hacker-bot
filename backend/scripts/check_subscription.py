import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dotenv import load_dotenv

# Add the parent directory to Python path so we can import from app
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.db import async_session_maker
from app.models_db import User, Subscription

async def check_subscription():
    async with async_session_maker() as db:
        # Find the user
        user_result = await db.execute(select(User).where(User.email == 'client_hmcRCt3f35DJC2NF0iVipwgrub1jlgTS@auth0-client.com'))
        user = user_result.scalar_one_or_none()
        
        if not user:
            print("User not found!")
            return

        print(f"Found user: {user.id} ({user.email})")

        # Find subscription
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        subscription = sub_result.scalar_one_or_none()

        if subscription:
            print(f"Subscription found:")
            print(f"  Plan: {subscription.plan}")
            print(f"  Status: {subscription.status}")
            print(f"  Customer ID: {subscription.stripe_customer_id}")
            print(f"  Subscription ID: {subscription.stripe_subscription_id}")
        else:
            print("No subscription found!")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(check_subscription()) 