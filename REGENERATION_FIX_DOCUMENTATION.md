# 🔄 Job Application Agent - Regeneration System Documentation

## 📋 Overview

This document serves as a reference guide for the regeneration functionality and system architecture. **READ THIS BEFORE MAKING ANY CHANGES** to avoid breaking working functionality.

---

## 🚨 CRITICAL: What NOT to Touch

### ✅ **Working Systems (DO NOT MODIFY)**

1. **Regeneration Logic** - Currently working properly
2. **Page/Chat switching** - Messages stay in correct conversations
3. **WebSocket message handling** - Clean separation of concerns
4. **Message loading for specific pages** - Uses page change effect only

### ❌ **Recent Issues Fixed (Don't Reintroduce)**

1. ~~Regeneration button infinite loading~~ ✅ FIXED
2. ~~Messages from other chats being deleted~~ ✅ FIXED
3. ~~Duplicate messages during regeneration~~ ✅ FIXED
4. ~~Backend not loading page history for regeneration~~ ✅ FIXED

---

## 🏗️ System Architecture

### **Frontend Architecture**

```
frontend/
├── lib/hooks/use-websocket.ts          # Main WebSocket logic - WORKING, DON'T TOUCH
├── components/chat/chat-message.tsx     # Message UI with regenerate button
├── components/chat/chat-container.tsx   # Chat container - passes regenerate handler
└── app/page.tsx                        # Main page - connects everything
```

### **Backend Architecture**

```
backend/app/
├── orchestrator.py                     # MAIN AGENT - GETTING BLOATED ⚠️
├── enhanced_memory.py                  # Memory management
├── graph_rag.py                       # Graph RAG implementation
├── agent.py                           # Agent logic
└── rag.py                             # RAG endpoints
```

---

## 🔄 Regeneration Flow (WORKING - DON'T BREAK)

### **Frontend Flow**

1. User clicks regenerate button (🔄) on AI message
2. `regenerateMessage(id)` in `use-websocket.ts`:
   - Finds message to regenerate
   - Finds last human message before it
   - Removes all messages after last human message: `setMessages(messagesToRegenerate)`
   - Sends regenerate request: `{type: 'regenerate', content: lastHumanMessage, page_id: currentPageId}`

### **Backend Flow**

1. Orchestrator receives regenerate request in `orchestrator.py`
2. **KEY FIX**: If chat history empty, loads page history from database
3. Removes last AI message from history
4. Regenerates response using last human message
5. Sends new response via WebSocket
6. Saves to database with correct page_id

### **Message Handling**

- **WebSocket Connection**: Only handles connection, NO automatic history loading
- **Page Changes**: `useEffect` with `currentPageId` loads history for specific conversations
- **Clean Separation**: Connection logic ≠ Message loading logic

---

## 🛠️ Key Functions & Files

### **Frontend: `use-websocket.ts`**

```typescript
// WORKING - DON'T MODIFY THESE
const connect()                    // Only WebSocket connection
const fetchMessagesForPage()      // Loads messages for specific page
const regenerateMessage()         // Handles regenerate button clicks

// Page change effect - ONLY place that loads message history
useEffect(() => {
  loadPageMessages()
}, [currentPageId])
```

### **Backend: `orchestrator.py`**

```python
# WORKING - DON'T MODIFY THESE
elif message_data.get("type") == "regenerate":
    # Loads page history if chat_history empty (KEY FIX)
    # Removes last AI message
    # Regenerates response
```

---

## 📁 File Organization Issues

### **PROBLEM: Orchestrator.py is TOO BLOATED** ⚠️

The orchestrator currently contains 3135 lines with ALL tools and functions mixed together.

### **SUGGESTED REFACTORING**

Move functions to dedicated files:

```
backend/app/
├── tools/
│   ├── __init__.py
│   ├── job_search_tools.py         # search_jobs_tool, search_jobs_with_browser
│   ├── resume_tools.py             # generate_tailored_resume, enhance_resume_section, etc.
│   ├── document_tools.py           # enhanced_document_search, analyze_specific_document
│   ├── career_tools.py             # get_cv_best_practices, analyze_skills_gap, etc.
│   └── cover_letter_tools.py       # generate_cover_letter, generate_cover_letter_from_url
├── orchestrator.py                 # ONLY WebSocket handling + agent setup
└── tool_registry.py               # Imports and registers all tools
```

### **Benefits of Refactoring**

- ✅ Easier to maintain individual tool categories
- ✅ Reduced orchestrator complexity
- ✅ Better organization for Graph RAG integration
- ✅ Easier to debug specific functionality
- ✅ Cleaner separation of concerns

---

## 🚨 Rules for Future Changes

### **BEFORE Making Changes**

1. **READ THIS DOCUMENTATION FIRST**
2. Test regeneration functionality to ensure it's still working
3. Test chat switching to ensure messages don't get mixed up
4. Make minimal, targeted changes
5. Test thoroughly before committing

### **When Adding New Tools**

1. **DON'T add to orchestrator.py** - Create separate tool files
2. Import tools in orchestrator, don't define them there
3. Keep WebSocket logic separate from tool logic

### **When Debugging Issues**

1. Check if regeneration still works first
2. Check if chat switching preserves messages
3. Look at console logs for debugging info
4. Don't modify working WebSocket logic

---

## 🔧 Recent Fixes Applied

### **Backend Fix (orchestrator.py)**

```python
# Auto-load page history if chat_history empty during regeneration
if len(current_chat_history) == 0 and regenerate_page_id:
    log.info(f"🔄 Chat history empty, loading history for page {regenerate_page_id}")
    # Load page history from database
```

### **Frontend Fix (use-websocket.ts)**

```typescript
// Removed automatic history loading from connect()
const connect = useCallback(async () => {
  // Only WebSocket connection, NO history loading
}, [getToken]); // Removed fetchMessagesForPage dependency
```

---

## 📊 System Health Checklist

Before deploying any changes, verify:

- [ ] ✅ Regeneration button works (no infinite loading)
- [ ] ✅ Chat switching preserves messages in correct conversations
- [ ] ✅ New messages appear correctly
- [ ] ✅ Message editing works
- [ ] ✅ Message deletion works
- [ ] ✅ WebSocket connection is stable
- [ ] ✅ Graph RAG integration still functional

---

## 💡 Future Improvements

### **Immediate**

1. **Refactor orchestrator.py** - Move tools to separate files
2. Create `tool_registry.py` for clean tool imports
3. Add better error boundaries for tool failures

### **Medium Term**

1. Implement tool caching for better performance
2. Add tool-specific logging and monitoring
3. Create tool-specific tests

### **Long Term**

1. Microservices architecture for different tool categories
2. Tool marketplace/plugin system
3. Advanced Graph RAG optimizations

---

## 📞 Emergency Contacts

If regeneration breaks again:

1. Check this documentation first
2. Verify WebSocket connection logs
3. Check page history loading in backend
4. Test with simple regeneration request

**Remember: Regeneration was working before - don't over-engineer the fix!**

---

_Last Updated: 2025-06-29_
_Status: Regeneration ✅ Working | Chat Switching ✅ Working | System ⚠️ Needs Refactoring_
