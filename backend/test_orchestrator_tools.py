import pytest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import User

# --- DEFINITIVE FIX ---
# We now import the newly separated, testable graph creation function.
from app.orchestrator.orchestrator_main import create_master_agent_graph

@pytest.fixture
def mock_db_session():
    """Provides a mock SQLAlchemy AsyncSession."""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def mock_user():
    """Provides a mock User object."""
    # The user object needs an 'id' attribute for the tool creation to work.
    user = MagicMock(spec=User)
    user.id = "test_user_id"
    return user

@pytest.mark.asyncio
async def test_agent_graph_creation_smoke_test(mock_db_session, mock_user):
    """
    This is the definitive "smoke test".
    It calls the new, separated graph creation function and verifies
    that it can be compiled without errors.

    If any tool is misconfigured or fails to import (is None), this test
    will fail with the `TypeError`, definitively identifying the root cause
    of the server crash.
    """
    try:
        # This is the function that contains all the complex tool creation logic.
        # We are calling it directly in a controlled test environment.
        graph = create_master_agent_graph(db=mock_db_session, user=mock_user)
        
        # If the test reaches this point, it means the graph (including all tools)
        # was created and compiled successfully without any TypeErrors.
        assert graph is not None
        print("\n--- SUCCESS: Master agent graph created and compiled successfully. ---")
        print(f"--- All tools were loaded without causing a TypeError. ---")

    except Exception as e:
        # If this test fails, pytest will capture the full traceback,
        # showing us exactly where the error occurred during tool creation.
        pytest.fail(f"Graph creation failed with a critical error: {e}", tb_limit=None)

# To run this test:
# cd backend
# pytest test_orchestrator_tools.py 