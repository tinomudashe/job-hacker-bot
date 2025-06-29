import logging
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.db import get_db
from app.models_db import User, Subscription, Application, GeneratedCV, GeneratedCoverLetter
from app.dependencies import get_current_active_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Tier Limits ---
PLAN_LIMITS = {
    'free': {
        'applications': 5,
        'cvs': 10,
        'cover_letters': 5,
        'chat_agent': False,
        'interview_tools': False,
        'resume_generation': 3,
    },
    'premium': {
        'applications': 200,
        'cvs': 20,
        'cover_letters': float('inf'), # Unlimited
        'chat_agent': True,
        'interview_tools': True,
        'resume_generation': float('inf'), # Unlimited
    }
}

class UsageManager:
    def __init__(self, feature: str):
        self.feature = feature

    async def __call__(self, db: AsyncSession = Depends(get_db), db_user: User = Depends(get_current_active_user)):
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == db_user.id))
        subscription = sub_result.scalar_one_or_none()
        
        plan = 'free'
        if subscription and subscription.plan == 'premium' and subscription.status == 'active':
            plan = 'premium'
        
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS['free'])

        # Tier-based access check
        if self.feature in ['chat_agent', 'interview_tools'] and not limits[self.feature]:
            logger.warning(f"User {db_user.id} (plan: {plan}) attempted to access premium feature: {self.feature}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to '{self.feature}' requires a premium plan. Please upgrade your subscription."
            )

        # Metered usage check (for features with monthly limits)
        if self.feature in ['applications', 'cvs', 'cover_letters']:
            first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            if self.feature == 'applications':
                count_query = select(func.count(Application.id)).where(
                    Application.user_id == db_user.id,
                    Application.date_applied >= first_of_month,
                    Application.success == True  # Only count successful applications
                )
            elif self.feature == 'cvs':
                count_query = select(func.count(GeneratedCV.id)).where(GeneratedCV.user_id == db_user.id, GeneratedCV.created_at >= first_of_month)
            elif self.feature == 'cover_letters':
                count_query = select(func.count(GeneratedCoverLetter.id)).where(GeneratedCoverLetter.user_id == db_user.id, GeneratedCoverLetter.created_at >= first_of_month)
            
            usage_result = await db.execute(count_query)
            current_usage = usage_result.scalar_one()

            if current_usage >= limits[self.feature]:
                logger.warning(f"User {db_user.id} (plan: {plan}) exceeded monthly limit for {self.feature}. Usage: {current_usage}, Limit: {limits[self.feature]}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You have exceeded your monthly limit for '{self.feature}'. Please upgrade or wait until next month."
                )
        
        logger.info(f"User {db_user.id} (plan: {plan}) granted access to feature: {self.feature}")
        return True # Grant access 