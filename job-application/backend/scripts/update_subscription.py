import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dotenv import load_dotenv
import uuid

# Add the parent directory to Python path so we can import from app
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.db import async_session_maker
from app.models_db import User, Subscription

async def update_subscription():
    async with async_session_maker() as db:
        # Find the user - use the email that matches our Auth0 token
        user_result = await db.execute(select(User).where(User.external_id == 'hmcRCt3f35DJC2NF0iVipwgrub1jlgTS@clients'))
        user = user_result.scalar_one_or_none()
        
        if not user:
            print("User not found. Creating user...")
            user = User(
                external_id='hmcRCt3f35DJC2NF0iVipwgrub1jlgTS@clients',
                email='client_hmcRCt3f35DJC2NF0iVipwgrub1jlgTS@auth0-client.com',
                name='Test User'
            )
            db.add(user)
            await db.flush()

        # Find or create subscription
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        subscription = sub_result.scalar_one_or_none()

        if subscription:
            print("Updating existing subscription...")
            subscription.plan = 'premium'
            subscription.status = 'active'
            subscription.stripe_customer_id = f'cus_test_{uuid.uuid4()}'
            subscription.stripe_subscription_id = f'sub_test_{uuid.uuid4()}'
        else:
            print("Creating new subscription...")
            subscription = Subscription(
                user_id=user.id,
                plan='premium',
                status='active',
                stripe_customer_id=f'cus_test_{uuid.uuid4()}',
                stripe_subscription_id=f'sub_test_{uuid.uuid4()}'
            )
            db.add(subscription)

        await db.commit()
        print("Subscription updated successfully!")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(update_subscription()) 