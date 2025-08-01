import os
import stripe
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any, Optional
from datetime import datetime

from app.db import get_db
from app.models_db import User, Subscription
from app.dependencies import get_current_active_user
from app.clerk import get_clerk_user
from app.email_service import (
    send_payment_failed_email, send_subscription_canceled_email, send_welcome_email
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter()

# --- Stripe Configuration ---
stripe.api_key = os.getenv("STRIPE_API_KEY")
if not stripe.api_key:
    logger.critical("STRIPE_API_KEY is not set. The billing service will not work.")

webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
premium_price_id = os.getenv("STRIPE_PREMIUM_PRICE_ID")
pro_product_id = os.getenv("STRIPE_PRO_PRODUCT_ID")
price_id = os.getenv("STRIPE_PRICE_ID")
app_url = os.getenv("APP_URL", "http://localhost:3000")


# --- Helper Functions ---
async def get_subscription(
    db: AsyncSession, user_id: str
) -> Optional[Subscription]:
    """Retrieve a user's subscription from the database."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    return result.scalar_one_or_none()


# --- Billing Endpoints ---

@router.get("/subscription")
async def get_subscription_status(
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Retrieves the current user's subscription status using Stripe as the single source of truth.
    """
    logger.info(f"Fetching subscription status for user: {db_user.id}")
    subscription_db = await get_subscription(db, str(db_user.id))

    if not subscription_db or not subscription_db.stripe_subscription_id:
        logger.info(f"No active subscription found in DB for user {db_user.id}.")
        return {"plan": "free", "status": "inactive", "is_active": False}

    try:
        logger.info(f"Retrieving Stripe subscription {subscription_db.stripe_subscription_id} for user {db_user.id}")
        stripe_sub = stripe.Subscription.retrieve(subscription_db.stripe_subscription_id)
        status = stripe_sub.status
        plan = "free"
        is_active = status in ['trialing', 'active']

        items_list_object = stripe_sub.get('items')
        if items_list_object and items_list_object.data:
            price_id_from_stripe = items_list_object.data[0].price.id
            if price_id_from_stripe == os.getenv("STRIPE_PRICE_ID"):
                plan = "pro"

        if status == 'trialing':
            plan = 'trial'

        period_end_timestamp = stripe_sub.get('trial_end') if status == 'trialing' else stripe_sub.get('current_period_end')
        period_end = datetime.utcfromtimestamp(period_end_timestamp) if period_end_timestamp else None
        
        logger.info(f"Subscription status for user {db_user.id}: plan={plan}, status={status}, is_active={is_active}")

        return {
            "plan": plan,
            "status": status,
            "is_active": is_active,
            "period_end": period_end.isoformat() if period_end else None
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error for user {db_user.id}: {e}", exc_info=True)
        return {"plan": subscription_db.plan, "status": "error", "is_active": False}
    except Exception as e:
        logger.error(f"Unexpected error fetching subscription for user {db_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.post("/create-portal-session")
async def create_portal_session(
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Creates a Stripe Customer Portal session for the user to manage their subscription.
    """
    subscription = await get_subscription(db, str(db_user.id))
    if not subscription or not subscription.stripe_customer_id:
        logger.error(f"Portal session failed for user {db_user.id}: No subscription or customer ID found.")
        raise HTTPException(status_code=404, detail="User subscription not found.")

    try:
        logger.info(f"Creating portal session for user {db_user.id} with customer ID {subscription.stripe_customer_id}")

        portal_configuration = stripe.billing_portal.Configuration.create(
            business_profile={
                "headline": "JobHackerBot - Manage Your Subscription",
                "privacy_policy_url": f"{app_url}/privacy",
                "terms_of_service_url": f"{app_url}/terms",
            },
            features={
                "customer_update": {"allowed_updates": ["email", "tax_id"], "enabled": True},
                "invoice_history": {"enabled": True},
                "payment_method_update": {"enabled": True},
            },
        )

        portal_session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=f"{app_url}/settings",
            configuration=portal_configuration.id,
        )
        return {"url": portal_session.url}
    except Exception as e:
        logger.error(f"Failed to create Stripe portal session for user {db_user.id} with customer ID {subscription.stripe_customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create customer portal session.")


@router.post("/create-checkout-session")
async def create_checkout_session(
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Creates a Stripe Checkout session for a user to subscribe to the Pro plan.
    """
    if not price_id:
        logger.error("STRIPE_PRICE_ID is not set in the environment variables.")
        raise HTTPException(status_code=500, detail="Stripe Price ID is not configured.")

    subscription = await get_subscription(db, str(db_user.id))

    # --- DEFINITIVE FIX FOR RECURRING ERROR ---
    # This block now correctly checks for a valid stripe_customer_id before attempting
    # to create a portal session. If the id is missing, it will fall through
    # to the new checkout logic, which will fix the inconsistent data.
    if subscription and subscription.stripe_customer_id and subscription.status in ['active', 'trialing', 'past_due']:
        try:
            logger.info(f"User {db_user.id} is already subscribed. Redirecting to customer portal.")
            portal_session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=f"{app_url}/settings",
            )
            return {"redirect_to_portal": True, "url": portal_session.url}
        except Exception as e:
            logger.error(f"Failed to create Stripe portal session for already-subscribed user {db_user.id}: {e}")
            raise HTTPException(status_code=500, detail="Could not create customer portal session.")

    # --- New Checkout Logic ---
    is_eligible_for_trial = not (subscription and subscription.status in ['active', 'trialing', 'past_due', 'canceled'])
    
    line_items = [{'price': price_id, 'quantity': 1}]
    subscription_data = {'trial_period_days': 1} if is_eligible_for_trial else {}

    customer_id = subscription.stripe_customer_id if subscription else None
    
    if not customer_id:
        user_email = db_user.email
        if not user_email and db_user.external_id:
            logger.info(f"User {db_user.id} is missing an email. Fetching from Clerk.")
            clerk_user = await get_clerk_user(db_user.external_id)
            if clerk_user:
                user_email = clerk_user.get("email")

        if not user_email:
            logger.error(f"Failed to create Stripe customer for user {db_user.id}: Email not found.")
            raise HTTPException(status_code=400, detail="A valid email is required. Please update your profile.")

        try:
            customer = stripe.Customer.create(
                email=user_email,
                name=db_user.name,
                metadata={"user_id": str(db_user.id)}
            )
            customer_id = customer.id
            if not subscription:
                subscription = Subscription(user_id=str(db_user.id))
                db.add(subscription)
            subscription.stripe_customer_id = customer_id
            await db.flush()
        except Exception as e:
            logger.error(f"Failed to create Stripe customer for user {db_user.id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to create Stripe customer.")

    try:
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=line_items,
            mode='subscription',
            subscription_data=subscription_data,
            success_url=f"{app_url}/?checkout=success",
            cancel_url=f"{app_url}/?checkout=cancel",
            metadata={'user_external_id': db_user.external_id, 'plan': 'pro-trial' if is_eligible_for_trial else 'pro'}
        )
        return {"url": checkout_session.url}
    except Exception as e:
        logger.error(f"Failed to create Stripe checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session.")


@router.post("/stripe-webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if not webhook_secret:
        logger.error("Stripe webhook secret is not configured.")
        return {"status": "error", "message": "Webhook secret not configured."}

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=stripe_signature, secret=webhook_secret
        )
    except ValueError as e:
        logger.error(f"Webhook error - Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook error - Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event['type']
    data = event['data']['object']

    if event_type == 'checkout.session.completed':
        metadata = data.get('metadata', {})
        user_external_id = metadata.get('user_external_id')
        plan = metadata.get('plan', 'pro')
        stripe_customer_id = data.get('customer')
        stripe_subscription_id = data.get('subscription')

        if not user_external_id:
            logger.error("Webhook received checkout.session.completed without user_external_id.")
            return {"status": "error", "message": "Missing user_external_id"}

        async with db.begin():
            user_result = await db.execute(select(User).where(User.external_id == user_external_id))
            user = user_result.scalar_one_or_none()
            if not user:
                logger.error(f"Webhook error: User with external_id {user_external_id} not found.")
                return {"status": "error", "message": "User not found"}

            subscription = await get_subscription(db, str(user.id))
            if not subscription:
                subscription = Subscription(user_id=str(user.id))
                db.add(subscription)
                logger.info(f"Creating new subscription record for user {user.id}.")

            subscription.plan = plan
            subscription.status = data.get('status', 'active')
            subscription.stripe_customer_id = stripe_customer_id
            subscription.stripe_subscription_id = stripe_subscription_id
            logger.info(f"User {user.id} subscribed to {plan} with status {subscription.status}.")

            if subscription.status in ['active', 'trialing']:
                if user.email:
                    background_tasks.add_task(send_welcome_email, user.email, user.name or "User")
                    logger.info(f"Queued welcome email for user {user.id}")

    elif event_type in ['customer.subscription.created', 'customer.subscription.updated', 'customer.subscription.deleted']:
        stripe_customer_id = data.get('customer')
        async with db.begin():
            subscription = await db.scalar(select(Subscription).where(Subscription.stripe_customer_id == stripe_customer_id))
            if subscription:
                subscription.status = data.get('status')
                subscription.stripe_subscription_id = data.get('id')
                logger.info(f"Subscription for customer {stripe_customer_id} updated to status {subscription.status}.")
                if subscription.status == 'canceled' and subscription.user:
                     if subscription.user.email:
                        background_tasks.add_task(send_subscription_canceled_email, subscription.user.email)

    elif event_type == 'invoice.payment_failed':
        stripe_customer_id = data.get('customer')
        async with db.begin():
            subscription = await db.scalar(select(Subscription).where(Subscription.stripe_customer_id == stripe_customer_id))
            if subscription:
                subscription.status = 'past_due'
                logger.warning(f"Invoice payment failed for customer {stripe_customer_id}. Status set to past_due.")
                if subscription.user and subscription.user.email:
                    background_tasks.add_task(send_payment_failed_email, subscription.user.email)

    elif event_type == 'invoice.payment_succeeded':
        stripe_customer_id = data.get('customer')
        async with db.begin():
            subscription = await db.scalar(select(Subscription).where(Subscription.stripe_customer_id == stripe_customer_id))
            if subscription and subscription.status != 'active':
                subscription.status = 'active'
                logger.info(f"Recurring payment for customer {stripe_customer_id} succeeded. Subscription active.")

    else:
        logger.info(f"Unhandled Stripe event type: {event['type']}")

    return {"status": "success"}