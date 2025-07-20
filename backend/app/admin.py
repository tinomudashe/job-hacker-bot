import logging
import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, cast, Date
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional


from app.db import get_db
from app.dependencies import get_current_active_user
from app.models_db import User, Document, Subscription, UserBehavior

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# This is a placeholder for a real admin check. In production, you'd verify
# a specific role or permission from the user's token or database record.
async def get_admin_user(user: User = Depends(get_current_active_user)):
    # Replace this with your actual admin verification logic
    # For now, we'll just check if the user is active.
    if not user.active:
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

@router.get("/stats")
async def get_application_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Retrieves key business intelligence statistics for the admin dashboard.
    """
    try:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        # --- Core User & Subscription Metrics ---
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar_one() or 1 # Avoid division by zero

        # --- Subscription Breakdown ---
        subscription_statuses = ['active', 'trialing', 'canceled', 'past_due']
        sub_tasks = [
            db.execute(select(func.count(Subscription.id)).where(Subscription.status == status))
            for status in subscription_statuses
        ]
        sub_results = await asyncio.gather(*sub_tasks)
        # Ensure the breakdown object is always created
        subscription_breakdown = {status: result.scalar_one() for status, result in zip(subscription_statuses, sub_results)}
        active_subscriptions = subscription_breakdown.get('active', 0)

        # --- Insightful KPIs ---
        weekly_active_users_result = await db.execute(
            select(func.count(User.id)).where(User.created_at >= seven_days_ago) # Simplified: active = created in last 7 days
        )
        weekly_active_users = weekly_active_users_result.scalar_one()
        
        conversion_rate = (active_subscriptions / total_users) * 100 if total_users > 0 else 0

        # --- Data Health Metrics ---
        users_missing_email_result = await db.execute(
            select(func.count(User.id)).where(User.email == None)
        )
        users_missing_emails = users_missing_email_result.scalar_one()


        return {
            "totalUsers": total_users,
            "weeklyActiveUsers": weekly_active_users,
            "activeSubscriptions": active_subscriptions,
            "subscriptionConversionRate": round(conversion_rate, 2),
            "usersMissingEmail": users_missing_emails,
            "subscriptionBreakdown": subscription_breakdown # Ensure this is always returned
        }
    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve application statistics.")


@router.get("/stats/users-over-time")
async def get_users_over_time_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Retrieves the number of new users and new subscriptions per day for the 
    last 30 days.
    """
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Query for new users
        users_result = await db.execute(
            select(
                cast(User.created_at, Date).label("date"),
                func.count(User.id).label("user_count")
            )
            .where(User.created_at >= thirty_days_ago)
            .group_by(cast(User.created_at, Date))
            .order_by(cast(User.created_at, Date))
        )
        
        # Query for new subscriptions
        subs_result = await db.execute(
            select(
                cast(Subscription.created_at, Date).label("date"),
                func.count(Subscription.id).label("sub_count")
            )
            .where(Subscription.created_at >= thirty_days_ago)
            .group_by(cast(Subscription.created_at, Date))
            .order_by(cast(Subscription.created_at, Date))
        )
        
        # Combine the results into a single structure for the frontend
        user_data = {record.date.isoformat(): record.user_count for record in users_result.all()}
        sub_data = {record.date.isoformat(): record.sub_count for record in subs_result.all()}
        
        # Create a complete date range for the last 30 days
        all_dates = [thirty_days_ago.date() + timedelta(days=i) for i in range(31)]
        
        combined_data = []
        for date in all_dates:
            date_str = date.isoformat()
            combined_data.append({
                "date": date_str,
                "New Users": user_data.get(date_str, 0),
                "New Subscriptions": sub_data.get(date_str, 0),
            })
            
        return combined_data

    except Exception as e:
        logger.error(f"Error fetching users over time stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve user statistics.")


class RecentUser(BaseModel):
    id: str
    email: Optional[str] = None
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class RecentSubscription(BaseModel):
    user_email: Optional[str] = None
    plan: str
    status: str
    
    class Config:
        from_attributes = True


class UsageEvent(BaseModel):
    user_email: Optional[str] = None
    action_type: str
    log_level: str
    success: bool
    context: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/activity/recent-users", response_model=List[RecentUser])
async def get_recent_users(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Retrieves the 5 most recently registered unique users.
    This query ensures that if a user has multiple records, only the newest one is returned.
    """
    # Create a window function to number user records, partitioning by their unique
    # external_id and ordering by creation date to find the most recent record.
    row_number_func = func.row_number().over(
        partition_by=User.external_id,
        order_by=User.created_at.desc()
    ).label("row_num")

    # Create a subquery that selects users and applies the row number.
    # We only consider users that have an external_id to ensure uniqueness.
    subquery = select(User, row_number_func).where(User.external_id.isnot(None)).subquery()
    
    # Alias the subquery to make it selectable.
    ranked_users_alias = aliased(User, subquery)

    # Final statement: Select from the ranked users where the row number is 1 
    # (i.e., the most recent record for each unique user), then order by date
    # to get the 5 most recent sign-ups overall.
    stmt = (
        select(ranked_users_alias)
        .where(subquery.c.row_num == 1)
        .order_by(ranked_users_alias.created_at.desc())
        .limit(5)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/activity/recent-subscriptions", response_model=List[RecentSubscription])
async def get_recent_subscriptions(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Retrieves the 5 most recent subscription events, joining with the User table
    to get the user's email.
    """
    result = await db.execute(
        select(
            User.email.label("user_email"),
            Subscription.plan,
            Subscription.status
        )
        .join(User, Subscription.user_id == User.id)
        .order_by(Subscription.id.desc()) # Assuming higher ID is newer
        .limit(5)
    )
    return result.all()


@router.get("/activity/usage-events", response_model=List[UsageEvent])
async def get_recent_usage_events(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Retrieves the 10 most recent key usage events.
    """
    result = await db.execute(
        select(
            User.email.label("user_email"),
            UserBehavior.action_type,
            UserBehavior.success,
            UserBehavior.context,
            UserBehavior.created_at
        )
        .join(User, UserBehavior.user_id == User.id)
        .order_by(UserBehavior.created_at.desc())
        .limit(10)
    )
    return result.all()


@router.get("/activity/errors", response_model=List[UsageEvent])
async def get_recent_errors(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Retrieves the 10 most recent failed usage events (errors).
    """
    result = await db.execute(
        select(
            User.email.label("user_email"),
            UserBehavior.action_type,
            UserBehavior.success,
            UserBehavior.context,
            UserBehavior.created_at
        )
        .join(User, UserBehavior.user_id == User.id)
        .where(UserBehavior.success == False)
        .order_by(UserBehavior.created_at.desc())
        .limit(10)
    )
    return result.all() 


@router.get("/activity/activity-log", response_model=List[UsageEvent])
async def get_activity_log(
    level: Optional[str] = None, # Filter by INFO, WARNING, ERROR
    user_email: Optional[str] = None, # Filter by user email (partial match)
    start_date: Optional[datetime] = None, # Filter by start date
    end_date: Optional[datetime] = None, # Filter by end date
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Retrieves a filterable list of the 100 most recent user behavior events.
    """
    stmt = (
        select(
            User.email.label("user_email"),
            UserBehavior.action_type,
            UserBehavior.log_level,
            UserBehavior.success,
            UserBehavior.context,
            UserBehavior.created_at
        )
        .join(User, UserBehavior.user_id == User.id)
    )

    if level:
        stmt = stmt.where(UserBehavior.log_level == level.upper())
    
    if user_email:
        stmt = stmt.where(User.email.ilike(f"%{user_email}%"))
        
    if start_date:
        stmt = stmt.where(UserBehavior.created_at >= start_date)
        
    if end_date:
        # Add a day to the end date to make it inclusive
        stmt = stmt.where(UserBehavior.created_at < end_date + timedelta(days=1))

    stmt = stmt.order_by(UserBehavior.created_at.desc()).limit(100)
    
    result = await db.execute(stmt)
    return result.all() 