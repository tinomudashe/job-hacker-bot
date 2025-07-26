import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
import stripe
from datetime import datetime, timedelta
import uuid

from app.main import app
from app.models_db import User, Subscription
from app.dependencies import get_current_active_user

# The user ID you provided for testing
TEST_USER_EXTERNAL_ID = "user_30P1FE8U5d4J7gI41XsQy3PuhyO"

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def mock_user(db_session):
    """Fixture to create and save a mock user with the specified external_id."""
    user = User(
        id=str(uuid.uuid4()),
        external_id=TEST_USER_EXTERNAL_ID,
        email="test@example.com",
        name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    return user


def override_get_current_active_user(user: User):
    """Factory to create a dependency override for the current user."""
    async def _override():
        return user
    return _override


@pytest.fixture
def mock_stripe_subscription():
    """A fixture to patch stripe.Subscription.retrieve."""
    with patch("stripe.Subscription.retrieve") as mock_retrieve:
        yield mock_retrieve


async def test_get_subscription_status_active_pro(
    client: AsyncClient,
    mock_user: User,
    db_session,
    mock_stripe_subscription: MagicMock,
):
    """
    Test Case 1: The specified user has an active 'pro' subscription.
    """
    # --- Arrange ---
    # 1. Override the dependency to simulate the user being logged in
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user(mock_user)

    # 2. Create a subscription record in the database for this user
    sub_in_db = Subscription(
        user_id=str(mock_user.id),
        stripe_subscription_id="sub_pro_user",
        stripe_customer_id="cus_pro_user",
        plan="pro",
        status="active",
    )
    db_session.add(sub_in_db)
    await db_session.commit()

    # 3. Mock the Stripe API response
    period_end = datetime.utcnow() + timedelta(days=30)
    mock_stripe_subscription.return_value.to_dict.return_value = {
        "status": "active",
        "items": {"data": [{"price": {"id": "price_pro_plan"}}]},
        "current_period_end": int(period_end.timestamp()),
        "trial_end": None,
    }

    # 4. Patch the environment variable for the price ID
    with patch("os.getenv", side_effect=lambda key, default=None: {"STRIPE_PRICE_ID": "price_pro_plan"}.get(key, default)):
        # --- Act ---
        response = await client.get("/api/billing/subscription")

    # --- Assert ---
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "pro"
    assert data["status"] == "active"
    assert data["is_active"] is True
    assert "period_end" in data

    # Clean up the override
    app.dependency_overrides = {}


async def test_get_subscription_status_trialing(
    client: AsyncClient,
    mock_user: User,
    db_session,
    mock_stripe_subscription: MagicMock,
):
    """
    Test Case 2: The specified user has an active 'trial' subscription.
    """
    # --- Arrange ---
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user(mock_user)

    sub_in_db = Subscription(
        user_id=str(mock_user.id),
        stripe_subscription_id="sub_trial_user",
        plan="pro-trial",
        status="trialing",
    )
    db_session.add(sub_in_db)
    await db_session.commit()

    trial_end = datetime.utcnow() + timedelta(days=1)
    mock_stripe_subscription.return_value.to_dict.return_value = {
        "status": "trialing",
        "items": {"data": [{"price": {"id": "price_pro_plan"}}]},
        "current_period_end": int((trial_end + timedelta(days=30)).timestamp()),
        "trial_end": int(trial_end.timestamp()),
    }

    # --- Act ---
    with patch("os.getenv", side_effect=lambda key, default=None: {"STRIPE_PRICE_ID": "price_pro_plan"}.get(key, default)):
        response = await client.get("/api/billing/subscription")

    # --- Assert ---
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "trial"
    assert data["status"] == "trialing"
    assert data["is_active"] is True
    assert data["period_end"] is not None

    app.dependency_overrides = {}


async def test_get_subscription_status_no_subscription(
    client: AsyncClient, mock_user: User
):
    """
    Test Case 3: The specified user has no subscription record.
    """
    # --- Arrange ---
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user(mock_user)

    # --- Act ---
    response = await client.get("/api/billing/subscription")

    # --- Assert ---
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "free"
    assert data["status"] == "inactive"
    assert data["is_active"] is False

    app.dependency_overrides = {}


async def test_get_subscription_status_stripe_api_error(
    client: AsyncClient,
    mock_user: User,
    db_session,
    mock_stripe_subscription: MagicMock,
):
    """
    Test Case 4: The Stripe API call fails.
    """
    # --- Arrange ---
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user(mock_user)

    sub_in_db = Subscription(
        user_id=str(mock_user.id),
        stripe_subscription_id="sub_error_user",
        plan="pro",
        status="active",
    )
    db_session.add(sub_in_db)
    await db_session.commit()

    mock_stripe_subscription.side_effect = stripe.error.StripeError(
        "API connection error"
    )

    # --- Act ---
    response = await client.get("/api/billing/subscription")

    # --- Assert ---
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "pro"
    assert data["status"] == "error"
    assert data["is_active"] is False

    app.dependency_overrides = {} 