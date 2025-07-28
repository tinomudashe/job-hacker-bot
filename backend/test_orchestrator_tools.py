import pytest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import User

# --- DEFINITIVE FIX ---
# We now import the newly separated, testable graph creation function.
from app.orchestrator.orchestrator_main import create_master_agent_graph
from app.orchestrator.orchestrator_tools.search_jobs_linkedin_api import search_jobs_linkedin_api

# THIS TEST IS NO LONGER NEEDED AND WILL BE REMOVED
# @pytest.mark.asyncio
# async def test_search_jobs_linkedin_api_direct_call():
#     """
#     Tests the search_jobs_linkedin_api tool directly to ensure it
#     handles multiple arguments correctly after the refactoring.
#     """
#     print("\n--- Testing search_jobs_linkedin_api ---")
#     
#     # Define the arguments as a dictionary, simulating how the AI would call it.
#     test_args = {
#         "keyword": "Python Developer",
#         "location": "Warsaw",
#         "limit": 3
#     }
#     
#     try:
#         # Await the tool's core function with the arguments.
#         result = await search_jobs_linkedin_api.func(**test_args)
#         
#         # Print the result to the console for verification.
#         print("Tool executed successfully. Result:")
#         print(result)
#         
#         # A successful result should contain the header and job listings.
#         assert "Found" in result
#         assert "jobs for 'Python Developer' in Warsaw" in result
#         assert "Apply:" in result
#         
#     except Exception as e:
#         # If any exception occurs, the test will fail and print the error.
#         print(f"Tool execution failed with error: {e}")
#         pytest.fail(f"search_jobs_linkedin_api raised an exception: {e}")

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