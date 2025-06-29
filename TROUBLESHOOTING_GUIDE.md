# Job Hacker Bot - Troubleshooting Guide

## 🚨 **CRITICAL ISSUES - IMMEDIATE ACTION REQUIRED**

### **Duplicate Messages Appearing**

**Symptoms:**

- Messages appear multiple times in chat
- Refreshing page shows duplicate messages
- Regeneration creates additional copies

**Root Causes & Solutions:**

1. **Frontend Deduplication Issue**

   ```typescript
   // ❌ Wrong: No duplicate checking
   setMessages((prev) => [...prev, newMessage]);

   // ✅ Correct: With duplicate prevention
   setMessages((prev) => {
     const contentString =
       typeof content === "string" ? content : JSON.stringify(content);
     const isDuplicate = prev.some(
       (msg) =>
         !msg.isUser &&
         (typeof msg.content === "string"
           ? msg.content
           : JSON.stringify(msg.content)) === contentString
     );
     if (isDuplicate) return prev;
     return [...prev, { id: uuidv4(), content, isUser: false }];
   });
   ```

2. **Backend Database Issue**

   ```python
   # ❌ Wrong: Save without checking/cleaning
   new_message = ChatMessage(...)
   db.add(new_message)
   await db.commit()

   # ✅ Correct: Clean old message first
   last_ai_message = await db.execute(
       select(ChatMessage)
       .where(ChatMessage.page_id == page_id)
       .where(ChatMessage.is_user_message == False)
       .order_by(ChatMessage.created_at.desc())
       .limit(1)
   )
   last_ai_msg = last_ai_message.scalars().first()
   if last_ai_msg:
       await db.delete(last_ai_msg)

   new_message = ChatMessage(...)
   db.add(new_message)
   await db.commit()
   ```

### **Regeneration Button Stuck/Not Working**

**Symptoms:**

- Regeneration button shows loading spinner indefinitely
- No response from backend
- Frontend becomes unresponsive

**Root Causes & Solutions:**

1. **Backend Timeout Issue**

   ```python
   # ❌ Wrong: No timeout handling
   response = await master_agent.ainvoke({...})

   # ✅ Correct: With timeout
   try:
       response = await asyncio.wait_for(
           master_agent.ainvoke({...}),
           timeout=30.0
       )
   except asyncio.TimeoutError:
       await websocket.send_text("Request timed out. Please try again.")
   ```

2. **Mixed Message Formats**

   ```python
   # ❌ Wrong: Mixing dictionary and LangChain formats
   current_chat_history.append({"role": "user", "content": content})

   # ✅ Correct: Consistent LangChain format
   current_chat_history.append(HumanMessage(content=content))
   ```

### **Edit Bubble Broken/Not Appearing**

**Symptoms:**

- Message edit functionality doesn't work
- Edit bubble doesn't appear on hover
- Changes don't save

**Root Causes & Solutions:**

1. **Missing Edit Handler**
   ```typescript
   // ✅ Ensure edit handler is properly implemented
   const editMessage = useCallback(
     async (id: string, newContent: string) => {
       // Preview immediately
       const previewMessages = [...messagesToKeep, editedMessage];
       setMessages(previewMessages);

       // Save to backend with proper error handling
       const editPromise = async () => {
         // Update message + delete subsequent + continue conversation
       };

       toast.promise(editPromise(), {
         loading: "Saving changes...",
         success: (data) => data,
         error: (err) => {
           setMessages(originalMessages); // Revert on error
           return `Edit failed: ${err.message}`;
         },
       });
     },
     [messages, getToken]
   );
   ```

## 🔧 **COMMON DEVELOPMENT ISSUES**

### **WebSocket Connection Issues**

**Symptoms:**

- WebSocket frequently disconnects
- Messages not sending/receiving
- Connection errors in console

**Debugging Steps:**

1. Check browser dev tools → Network → WS tab
2. Verify authentication token is valid
3. Check backend logs for WebSocket errors
4. Ensure proper URL format: `ws://localhost:8000/api/ws/orchestrator?token=...`

**Common Fixes:**

```typescript
// Check connection before sending
if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
  await connect(); // Reconnect if needed
}

// Proper error handling
newSocket.onerror = (error) => {
  console.error("WebSocket error:", error);
  setError("WebSocket connection failed. Retrying...");
  setTimeout(() => connect(), 3000); // Retry after 3 seconds
};
```

### **Database Transaction Failures**

**Symptoms:**

- "Database is locked" errors
- Transaction rollback messages
- Data not saving properly

**Solutions:**

```python
# Always use proper transaction handling
try:
    async with db.begin():
        # Your database operations here
        result = await db.execute(query)
        # Commit happens automatically
except Exception as e:
    # Rollback happens automatically
    log.error(f"Database error: {e}")
    raise
```

### **Authentication Issues**

**Symptoms:**

- 401 Unauthorized errors
- User not found errors
- Token validation failures

**Debugging:**

1. Check Clerk dashboard for user status
2. Verify JWT token format and expiration
3. Check environment variables for Clerk keys
4. Test token with `/api/auth/me` endpoint

### **Graph RAG Not Working**

**Symptoms:**

- Generic responses instead of personalized ones
- "Graph RAG not available" messages
- Context not being used

**Solutions:**

1. Check Graph RAG initialization in backend
2. Verify vector store is properly loaded
3. Check user document uploads
4. Test with Graph RAG demo endpoints

## 🐛 **DEBUGGING WORKFLOWS**

### **Frontend Debugging**

```bash
# 1. Check browser console for errors
# 2. Use React DevTools to inspect component state
# 3. Check Network tab for failed API calls
# 4. Use WebSocket inspection tools

# Useful browser debugging:
localStorage.clear() // Clear cached data
sessionStorage.clear() // Clear session data
```

### **Backend Debugging**

```bash
# 1. Check server logs
tail -f backend/logs/app.log

# 2. Test API endpoints directly
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/messages

# 3. Check database state
sqlite3 backend/database.db "SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT 10;"

# 4. Test WebSocket connection
python backend/ws_client.py
```

### **Database Debugging**

```sql
-- Check for duplicate messages
SELECT page_id, message, COUNT(*) as count
FROM chat_messages
WHERE is_user_message = false
GROUP BY page_id, message
HAVING count > 1;

-- Check message sequence
SELECT id, is_user_message, created_at, LEFT(message, 50) as preview
FROM chat_messages
WHERE page_id = 'your-page-id'
ORDER BY created_at;

-- Clear duplicate messages (careful!)
DELETE FROM chat_messages
WHERE id NOT IN (
  SELECT MIN(id)
  FROM chat_messages
  GROUP BY page_id, message, is_user_message
);
```

## 🔥 **EMERGENCY RECOVERY PROCEDURES**

### **Complete System Reset**

```bash
# 1. Stop all services
pkill -f uvicorn
pkill -f "npm run dev"

# 2. Clear caches
rm -rf Frontend/.next
rm -rf backend/__pycache__
rm -rf backend/uploads/temp/*

# 3. Restart database (if needed)
# For SQLite: backup and restore clean database
# For PostgreSQL: restart service

# 4. Restart services
cd backend && uvicorn app.main:app --reload
cd Frontend && npm run dev
```

### **Database Recovery**

```bash
# 1. Backup current database
cp backend/database.db backend/database.db.backup

# 2. Run migrations to fix schema issues
cd backend && alembic upgrade head

# 3. If corrupted, restore from backup
# cp backend/database.db.backup backend/database.db
```

### **Git Recovery**

```bash
# Revert to last working commit
git log --oneline -10  # Find last good commit
git reset --hard <commit-hash>

# Or create hotfix branch
git checkout -b hotfix/emergency-fix
# Make minimal fix
git commit -m "Emergency fix for critical issue"
```

## 📋 **PREVENTION CHECKLIST**

### **Before Making Changes**

```
□ Identify exact issue and root cause
□ Create reproduction steps
□ Test current behavior thoroughly
□ Plan minimal fix strategy
□ Create focused branch name
□ Set clear success criteria
```

### **During Development**

```
□ Make one small change at a time
□ Test after each change
□ Keep backups of working code
□ Don't touch unrelated code
□ Document what you're changing and why
```

### **Before Committing**

```
□ Test all affected functionality
□ Check for console errors
□ Verify no regressions introduced
□ Review code diff carefully
□ Write clear commit message
□ Check for sensitive data in commit
```

### **Before Deploying**

```
□ All tests pass
□ Manual testing completed
□ Database migrations tested
□ Environment variables updated
□ Monitoring alerts configured
□ Rollback plan prepared
```

## 📞 **GETTING HELP**

### **When to Ask for Help**

- Issue persists after following this guide
- Multiple systems are affected
- Data integrity is at risk
- Security concerns arise
- Performance significantly degrades

### **Information to Provide**

```
□ Exact error messages (copy/paste)
□ Steps to reproduce the issue
□ What you expected vs what happened
□ Browser/environment details
□ Recent changes made
□ Relevant logs and stack traces
```

### **Quick Debug Commands**

```bash
# Backend health check
curl http://localhost:8000/health

# Database connection test
python -c "from backend.app.db import engine; print('DB OK')"

# Frontend build test
cd Frontend && npm run build

# WebSocket test
python backend/ws_client.py
```

---

## 🎯 **REMEMBER**

> **"When debugging, change only one thing at a time and test immediately. If you change multiple things and something breaks, you won't know which change caused the issue."**

_Last Updated: 2024-06-29_
_Version: 1.0_
