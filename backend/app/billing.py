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
from app.clerk import get_clerk_user # Make sure this is imported
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
    # You might want to raise an exception here in a production environment
    # raise ValueError("STRIPE_API_KEY is not set.")

webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
premium_price_id = os.getenv("STRIPE_PREMIUM_PRICE_ID")
pro_product_id = os.getenv("STRIPE_PRO_PRODUCT_ID")
price_id = os.getenv("STRIPE_PRICE_ID")
# FIX: Set the default APP_URL to the frontend's typical local port (3000)
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
        plan = "free" # Default to free
        is_active = status in ['trialing', 'active']

        # Definitive Fix: Access 'items' like a dictionary key, which is what the traceback indicates.
        items_list_object = stripe_sub.get('items')
        if items_list_object and items_list_object.data:
            price_id = items_list_object.data[0].price.id
            if price_id == os.getenv("STRIPE_PRICE_ID"):
                plan = "pro"

        # The status is the most reliable source for trial information
        if status == 'trialing':
            plan = 'trial'

        # Determine period_end based on status
        if status == 'trialing':
            period_end_timestamp = stripe_sub.get('trial_end')
        else:
            period_end_timestamp = stripe_sub.get('current_period_end')

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
        # Fallback to DB state only if Stripe fails, but mark as inactive
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
    This now includes a dynamic portal configuration to avoid live mode errors.
    """
    subscription = await get_subscription(db, str(db_user.id))
    if not subscription or not subscription.stripe_customer_id:
        logger.error(f"Portal session failed for user {db_user.id}: No subscription or customer ID found.")
        raise HTTPException(status_code=404, detail="User subscription not found.")

    try:
        logger.info(f"Creating portal session for user {db_user.id} with customer ID {subscription.stripe_customer_id}")

        # FIX: Create a portal configuration on-the-fly.
        # This is the safest way to ensure the portal works in both test and live modes
        # without needing a default configuration set in the Stripe dashboard.
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
            return_url=f"{app_url}/settings", # URL to return to after portal session
            configuration=portal_configuration.id, # Use the newly created configuration
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
    It now includes logic to prevent users with a previous subscription from getting a new trial.
    """
    if not price_id:
        logger.error("STRIPE_PRICE_ID is not set in the environment variables.")
        raise HTTPException(
            status_code=500,
            detail="Stripe Price ID is not configured."
        )

    subscription = await get_subscription(db, str(db_user.id))

    # --- NEW: Free Trial Eligibility Check ---
    is_eligible_for_trial = True
    if subscription and subscription.status in ['active', 'trialing', 'past_due', 'canceled']:
        # If the user has EVER had a subscription (even a canceled one), they are not eligible for a new trial.
        is_eligible_for_trial = False
        logger.info(f"User {db_user.id} has a subscription with status '{subscription.status}'. Not eligible for a new trial.")
    
    # If user is already active, redirect them to the customer portal instead of a new checkout.
    if subscription and subscription.status in ['active', 'trialing', 'past_due']:
         try:
            logger.info(f"User {db_user.id} is already subscribed. Redirecting to customer portal.")
            
            # FIX: Ensure a portal configuration is created and used for robustness.
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
            # Return a special response type that the frontend can use to redirect.
            return {"redirect_to_portal": True, "url": portal_session.url}
         except Exception as e:
            logger.error(f"Failed to create Stripe portal session for already-subscribed user {db_user.id}: {e}")
            raise HTTPException(status_code=500, detail="Could not create customer portal session.")

    line_items = [{'price': price_id, 'quantity': 1}]
    subscription_data: Dict[str, Any] = {}
    if is_eligible_for_trial:
        subscription_data['trial_period_days'] = 1
        logger.info(f"User {db_user.id} is eligible for a new trial.")

    if not subscription:
        subscription = Subscription(user_id=str(db_user.id))
        db.add(subscription)
        await db.flush()
        await db.refresh(subscription)

    customer_id = subscription.stripe_customer_id
    if not customer_id:
        user_email = db_user.email
        user_name = db_user.name

        # This block ensures we have an email and name before proceeding.
        # It serves as a final safeguard to prevent invalid requests to Stripe.
        if not user_email and db_user.external_id:
            logger.info(f"User {db_user.id} is missing an email. Attempting to fetch from Clerk.")
            clerk_user = await get_clerk_user(db_user.external_id)
            if clerk_user:
                primary_email_id = clerk_user.get("primary_email_address_id")
                for email_info in clerk_user.get("email_addresses", []):
                    if email_info.get("id") == primary_email_id:
                        user_email = email_info.get("email_address")
                        db_user.email = user_email
                        break

                first_name = clerk_user.get("first_name", "")
                last_name = clerk_user.get("last_name", "")
                user_name = f"{first_name} {last_name}".strip() or "New User"
                db_user.name = user_name
                
                await db.commit()
                await db.refresh(db_user)
                logger.info(f"Successfully updated user {db_user.id} with info from Clerk.")

        # Final, definitive check before calling Stripe.
        if not user_email:
            logger.error(f"Failed to create Stripe customer for user {db_user.id}: No email address found after all checks.")
            raise HTTPException(
                status_code=400,
                detail="A valid email address is required to create a subscription. Please update your profile.",
            )
        try:
            customer = stripe.Customer.create(
                email=user_email,
                name=user_name,
                metadata={"user_id": str(db_user.id)}
            )
            customer_id = customer.id
            subscription.stripe_customer_id = customer_id
        except Exception as e:
            logger.error(
                "Failed to create Stripe customer for user "
                f"{db_user.id}: {e}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to create Stripe customer."
            )

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
        raise HTTPException(
            status_code=500, detail="Failed to create checkout session."
        )


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

    # Handle the event
    event_type = event['type']
    data = event['data']['object']

    if event_type == 'checkout.session.completed':
        metadata = data.get('metadata', {})
        user_external_id = metadata.get('user_external_id')
        plan = metadata.get('plan', 'pro')
        stripe_customer_id = data.get('customer')
        stripe_subscription_id = data.get('subscription')

        if not user_external_id:
            logger.error(
                "Webhook received for checkout.session.completed "
                "without user_external_id in metadata."
            )
            return {"status": "error", "message": "Missing user_external_id"}

        new_status = 'active'
        if stripe_subscription_id:
            try:
                stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
                new_status = stripe_sub.status
            except stripe.error.StripeError as e:
                logger.error(f"Could not retrieve subscription {stripe_subscription_id} from Stripe: {e}")

        async with db.begin():
            user_result = await db.execute(select(User).where(User.external_id == user_external_id))
            user = user_result.scalar_one_or_none()
            if not user:
                logger.error(f"Webhook error: User with external_id {user_external_id} not found.")
                return {"status": "error", "message": "User not found"}

            sub_result = await db.execute(
                select(Subscription).where(Subscription.user_id == str(user.id))
            )
            subscription = sub_result.scalar_one_or_none()
            
            if not subscription:
                subscription = Subscription(user_id=str(user.id))
                db.add(subscription)
                logger.info(f"Creating new subscription record for user {user.id}.")

            subscription.plan = plan
            subscription.status = new_status
            subscription.stripe_customer_id = stripe_customer_id
            subscription.stripe_subscription_id = stripe_subscription_id
            logger.info(f"User {user.id} subscribed to {plan} with status {new_status}.")

            # Send welcome email on successful subscription
            if new_status in ['active', 'trialing']:
                if user.email:
                    background_tasks.add_task(send_welcome_email, user.email, user.name or "User")
                    logger.info(f"Queued welcome email for user {user.id}")

    elif event_type in [
        'customer.subscription.created', 'customer.subscription.updated', 'customer.subscription.deleted'
    ]:
        stripe_subscription_id = data.get('id')
        stripe_customer_id = data.get('customer')  # Get customer ID from the event

        async with db.begin():
            # Find the subscription record by the Stripe customer ID, as this is constant.
            sub_result = await db.execute(select(Subscription).where(
                Subscription.stripe_customer_id == stripe_customer_id
            ))
            subscription = sub_result.scalar_one_or_none()

            # If no subscription record exists, we need to create one.
            if not subscription:
                try:
                    # Find the user by their Stripe customer ID. We assume a customer is
                    # created when they first attempt to check out.
                    user_result = await db.execute(select(User).join(Subscription).where(
                        Subscription.stripe_customer_id == stripe_customer_id
                    ))
                    user = user_result.scalar_one_or_none()

                    if not user:
                         # Fallback: If user not found via subscription, try retrieving customer email from Stripe
                        customer = stripe.Customer.retrieve(stripe_customer_id)
                        user_email = customer.email
                        user_result = await db.execute(select(User).where(User.email == user_email))
                        user = user_result.scalar_one_or_none()

                    if user:
                        # Create a new subscription record for this user
                        subscription = Subscription(user_id=str(user.id), stripe_customer_id=stripe_customer_id)
                        db.add(subscription)
                        await db.flush()  # Ensure it's in the session before updating
                        logger.info(f"Webhook created a new subscription record for user {user.id}")
                    else:
                        logger.error(f"Webhook could not find a user for customer ID {stripe_customer_id}")
                        return {"status": "error", "message": "User not found for customer ID"}

                except Exception as e:
                    logger.error(f"Error handling new subscription for customer {stripe_customer_id}: {e}")
                    return {"status": "error", "message": "Failed to process new subscription"}

            # Now that we have a subscription record, update it.
            if subscription:
                new_status = data.get('status')
                subscription.status = new_status
                subscription.stripe_subscription_id = stripe_subscription_id

                # Update the plan based on the price ID
                price_data = data.get('items', {}).get('data', [{}])[0].get('price', {})
                if price_data.get('id') == premium_price_id:
                    subscription.plan = 'premium'
                else:
                    # Handle other plans or set to a default if needed
                    subscription.plan = 'free' if new_status == 'canceled' else subscription.plan


                logger.info(
                    f"Subscription {stripe_subscription_id} for user {subscription.user_id} updated. "
                    f"New plan: {subscription.plan}, New status: {new_status}"
                )

                if new_status == 'canceled':
                    user_result = await db.execute(
                        select(User).where(User.id == subscription.user_id)
                    )
                    user = user_result.scalar_one_or_none()
                    if user and user.email:
                        background_tasks.add_task(
                            send_subscription_canceled_email,
                            user.email
                        )
                        logger.info(
                            f"Subscription for user {subscription.user_id} "
                            "was canceled. Cancellation email queued."
                        )

    elif event_type == 'invoice.payment_failed':
        stripe_customer_id = data.get('customer')
        async with db.begin():
            sub_result = await db.execute(select(Subscription).where(
                Subscription.stripe_customer_id == stripe_customer_id
            ))
            subscription = sub_result.scalar_one_or_none()
            if subscription:
                subscription.status = 'past_due'
                logger.warning(
                    f"Invoice payment failed for user {subscription.user_id}."
                    " Status set to past_due."
                )
                user_result = await db.execute(
                    select(User).where(User.id == subscription.user_id)
                )
                user = user_result.scalar_one_or_none()
                if user and user.email:
                    background_tasks.add_task(
                        send_payment_failed_email, user.email
                    )

    elif event_type == 'invoice.payment_succeeded':
        stripe_customer_id = data.get('customer')
        async with db.begin():
            sub_result = await db.execute(select(Subscription).where(
                Subscription.stripe_customer_id == stripe_customer_id
            ))
            subscription = sub_result.scalar_one_or_none()
            if subscription and subscription.status != 'active':
                subscription.status = 'active'
                logger.info(
                    "Successful recurring payment for customer "
                    f"{stripe_customer_id}. Subscription set to active."
                )

    else:
        logger.info(f"Unhandled Stripe event type: {event['type']}")

    return {"status": "success"}