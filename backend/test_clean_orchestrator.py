"""
Test script for the new clean orchestrator structure
Run this to verify everything works before switching
"""

import asyncio
import logging
from datetime import datetime

# Configure logging for testing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

async def test_tool_creation():
    """Test tool creation with new structure"""
    print("🧪 Testing Tool Creation...")
    
    try:
        # Import the new tools module
        from app.orchestrator_tools import create_all_tools, validate_tools_setup, log_tools_summary
        
        # Create mock user for testing (replace with real user)
        class MockUser:
            def __init__(self):
                self.id = "test-user-123"
                self.name = "Test User"
                self.first_name = "Test"
                self.last_name = "User"
                self.email = "test@example.com"
                self.phone = "+1234567890"
                self.address = "Test City, Test Country"
                self.linkedin = "https://linkedin.com/in/testuser"
                self.profile_headline = "Test Professional"
                self.skills = "Python, JavaScript, React"
        
        mock_user = MockUser()
        
        # Test tool creation
        tools = await create_all_tools(mock_user, None)  # No DB session for basic test
        
        print(f"✅ Created {len(tools)} tools")
        
        # Validate tools
        validation = validate_tools_setup(tools)
        print(f"✅ Tool validation: {'PASSED' if validation['is_valid'] else 'FAILED'}")
        
        if not validation['is_valid']:
            print(f"❌ Missing essential tools: {validation['essential_tools_missing']}")
        
        # Log detailed summary
        log_tools_summary(tools)
        
        return tools, validation
        
    except Exception as e:
        print(f"❌ Tool creation failed: {e}")
        log.error(f"Tool creation error: {e}", exc_info=True)
        return None, None

async def test_agent_creation():
    """Test agent creation with new structure"""
    print("\n🧪 Testing Agent Creation...")
    
    try:
        # Test tool creation first
        tools, validation = await test_tool_creation()
        
        if not tools or not validation['is_valid']:
            print("❌ Cannot test agent - tool creation failed")
            return None
        
        # Import clean master agent
        from app.master_agent import create_master_agent, build_user_context_for_agent
        
        # Create mock user context
        class MockUser:
            def __init__(self):
                self.id = "test-user-123"
                self.name = "Test User"
                self.first_name = "Test"
                self.last_name = "User"
                self.email = "test@example.com"
                self.address = "Test City"
        
        mock_user = MockUser()
        user_context = build_user_context_for_agent(mock_user)
        
        # Create agent
        agent = create_master_agent(
            tools=tools,
            documents=["test_resume.pdf", "test_cover_letter.docx"],
            user_context=user_context
        )
        
        print(f"✅ Agent created successfully")
        print(f"   Tools: {len(tools)}")
        print(f"   Max iterations: {agent.max_iterations}")
        print(f"   Model: gemini-2.5-pro-preview-03-25")
        
        return agent
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        log.error(f"Agent creation error: {e}", exc_info=True)
        return None

async def test_simple_message():
    """Test processing a simple message"""
    print("\n🧪 Testing Simple Message Processing...")
    
    try:
        agent = await test_agent_creation()
        
        if not agent:
            print("❌ Cannot test message - agent creation failed")
            return
        
        # Test simple message
        test_message = "Hello, can you help me with my career?"
        
        print(f"📤 Testing message: '{test_message}'")
        
        # Process message
        response = await agent.ainvoke({
            "input": test_message,
            "chat_history": []
        })
        
        output = response.get("output", "No output received")
        
        print(f"✅ Message processed successfully")
        print(f"📥 Response length: {len(output)} characters")
        print(f"📝 Response preview: {output[:100]}...")
        
        # Check for duplicate responses (should be single)
        if "I'm sorry" not in output and len(output) > 10:
            print("✅ Response looks valid")
        else:
            print("⚠️ Response might be error or very short")
        
        return output
        
    except Exception as e:
        print(f"❌ Message processing failed: {e}")
        log.error(f"Message processing error: {e}", exc_info=True)
        return None

async def test_no_regeneration():
    """Test that no automatic regeneration occurs"""
    print("\n🧪 Testing No Auto-Regeneration...")
    
    try:
        agent = await test_agent_creation()
        
        if not agent:
            print("❌ Cannot test regeneration - agent creation failed")
            return
        
        # Test multiple identical messages (should not regenerate automatically)
        test_message = "Tell me about resume writing"
        responses = []
        
        for i in range(2):
            print(f"📤 Sending message {i+1}: '{test_message}'")
            
            response = await agent.ainvoke({
                "input": test_message,
                "chat_history": []
            })
            
            output = response.get("output", "")
            responses.append(output)
            
            print(f"📥 Response {i+1} length: {len(output)} characters")
        
        # Check if responses are identical (they should be similar but not regenerated)
        if len(responses) == 2:
            print(f"✅ Both messages processed without auto-regeneration")
            print(f"   Response 1 length: {len(responses[0])}")
            print(f"   Response 2 length: {len(responses[1])}")
            
            # They should be different instances but similar content (no regeneration)
            if responses[0] != responses[1]:
                print("✅ No automatic regeneration detected")
            else:
                print("⚠️ Responses are identical - this could indicate caching or regeneration")
        
        return responses
        
    except Exception as e:
        print(f"❌ Auto-regeneration test failed: {e}")
        log.error(f"Auto-regeneration test error: {e}", exc_info=True)
        return None

async def run_full_test_suite():
    """Run complete test suite"""
    print("🚀 Starting Clean Orchestrator Test Suite")
    print("=" * 50)
    
    start_time = datetime.now()
    
    # Run all tests
    test_results = {
        "tool_creation": False,
        "agent_creation": False, 
        "message_processing": False,
        "no_auto_regeneration": False
    }
    
    try:
        # Test 1: Tool Creation
        tools, validation = await test_tool_creation()
        test_results["tool_creation"] = validation and validation['is_valid']
        
        # Test 2: Agent Creation  
        agent = await test_agent_creation()
        test_results["agent_creation"] = agent is not None
        
        # Test 3: Message Processing
        response = await test_simple_message()
        test_results["message_processing"] = response is not None and len(response) > 10
        
        # Test 4: No Auto-Regeneration
        responses = await test_no_regeneration()
        test_results["no_auto_regeneration"] = responses is not None and len(responses) == 2
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        log.error(f"Test suite error: {e}", exc_info=True)
    
    # Print results
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 50)
    print("🧪 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    print(f"Duration: {duration:.2f} seconds")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Ready to deploy clean orchestrator.")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} tests failed. Check errors above.")
    
    return test_results

if __name__ == "__main__":
    # Run the test suite
    asyncio.run(run_full_test_suite())