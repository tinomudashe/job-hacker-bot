import os
import stripe
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db import get_db
from app.models_db import User, Subscription
from app.dependencies import get_current_active_user
from app.email_service import send_payment_failed_email, send_subscription_canceled_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter()

# --- Stripe Configuration ---
stripe.api_key = os.getenv("STRIPE_API_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
premium_price_id = os.getenv("STRIPE_PREMIUM_PRICE_ID")
app_url = os.getenv("APP_URL", "http://localhost:8000")

# --- Billing Endpoints ---

@router.post("/create-checkout-session")
async def create_checkout_session(
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user)
):
    """
    Creates a Stripe Checkout session for a user to upgrade to the premium plan.
    """
    if not premium_price_id:
        raise HTTPException(status_code=500, detail="Stripe Premium Price ID is not configured.")

    async with db.begin():
        subscription_result = await db.execute(select(Subscription).where(Subscription.user_id == db_user.id))
        subscription = subscription_result.scalar_one_or_none()

        if not subscription:
            subscription = Subscription(user_id=db_user.id)
            db.add(subscription)
            await db.flush() # Flush to get subscription object for customer creation

        customer_id = subscription.stripe_customer_id
        if not customer_id:
            try:
                customer = stripe.Customer.create(email=db_user.email, name=db_user.name, metadata={"user_id": db_user.id})
                customer_id = customer.id
                subscription.stripe_customer_id = customer_id
            except Exception as e:
                logger.error(f"Failed to create Stripe customer for user {db_user.id}: {e}")
                raise HTTPException(status_code=500, detail="Failed to create Stripe customer.")

    try:
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{'price': premium_price_id, 'quantity': 1}],
            mode='subscription',
            success_url=f"{app_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{app_url}/billing/cancel",
            metadata={'user_id': db_user.id}
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
    """
    Listens for and processes webhooks from Stripe.
    """
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

    # Handle the event
    event_type = event['type']
    data = event['data']['object']

    if event_type == 'checkout.session.completed':
        user_id = data.get('metadata', {}).get('user_id')
        stripe_customer_id = data.get('customer')
        stripe_subscription_id = data.get('subscription')

        if not user_id:
            logger.error("Webhook received for checkout.session.completed without user_id in metadata.")
            return {"status": "error", "message": "Missing user_id"}
            
        async with db.begin():
            sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
            subscription = sub_result.scalar_one_or_none()
            if subscription:
                subscription.plan = 'premium'
                subscription.status = 'active'
                subscription.stripe_customer_id = stripe_customer_id
                subscription.stripe_subscription_id = stripe_subscription_id
                logger.info(f"User {user_id} upgraded to premium.")

    elif event_type in ['customer.subscription.updated', 'customer.subscription.deleted']:
        stripe_subscription_id = data.get('id')
        async with db.begin():
            sub_result = await db.execute(select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id))
            subscription = sub_result.scalar_one_or_none()
            if subscription:
                new_plan = 'premium' if data['items']['data'][0]['price']['id'] == premium_price_id else 'free'
                new_status = data.get('status') # e.g., 'active', 'past_due', 'canceled'
                
                subscription.plan = new_plan
                subscription.status = new_status
                logger.info(f"Subscription {stripe_subscription_id} for user {subscription.user_id} updated. New plan: {new_plan}, New status: {new_status}")
                
                if new_status == 'canceled':
                    background_tasks.add_task(send_subscription_canceled_email, subscription.user.email)
                    logger.info(f"Subscription for user {subscription.user_id} was canceled. Cancellation email queued.")


    elif event_type == 'invoice.payment_failed':
        stripe_customer_id = data.get('customer')
        async with db.begin():
            sub_result = await db.execute(select(Subscription).where(Subscription.stripe_customer_id == stripe_customer_id))
            subscription = sub_result.scalar_one_or_none()
            if subscription:
                subscription.status = 'past_due'
                logger.warning(f"Invoice payment failed for user {subscription.user_id}. Status set to past_due.")
                background_tasks.add_task(send_payment_failed_email, subscription.user.email)


    elif event_type == 'invoice.payment_succeeded':
        stripe_customer_id = data.get('customer')
        logger.info(f"Successful recurring payment for customer {stripe_customer_id}.")
        # Here you could trigger sending a receipt email
    
    else:
        logger.info(f"Unhandled Stripe event type: {event['type']}")

    return {"status": "success"} 