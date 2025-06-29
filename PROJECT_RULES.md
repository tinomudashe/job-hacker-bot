# Job Hacker Bot - Project Development Rules

## 🚨 **CRITICAL RULES - NEVER BREAK THESE**

### **Rule #1: The One-Issue-One-Change Principle**

- **NEVER** attempt to fix multiple unrelated issues in a single change
- **ALWAYS** create separate branches for separate problems
- **NEVER** say "while I'm here, let me also fix..." - resist scope creep
- **Example**: If fixing duplicate messages, do NOT also refactor message editing

### **Rule #2: Surgical Changes Only**

- **IDENTIFY** the exact lines/functions causing the issue
- **CHANGE** only what's necessary to fix that specific issue
- **PRESERVE** all existing working functionality
- **TEST** that your change doesn't break anything else

### **Rule #3: Test Before You Touch**

- **ALWAYS** test current functionality before making changes
- **DOCUMENT** what works and what doesn't
- **CREATE** a minimal reproduction case
- **VERIFY** your fix actually solves the problem

## 🔧 **DEVELOPMENT WORKFLOW RULES**

### **Pre-Development Checklist**

```
□ Understand the exact issue being reported
□ Identify the root cause (not just symptoms)
□ Create a focused branch name (e.g., fix/duplicate-messages-only)
□ Test current behavior thoroughly
□ Plan minimal changes needed
```

### **During Development**

```
□ Make changes in small, incremental steps
□ Test after each small change
□ Commit frequently with clear messages
□ If something breaks, immediately revert and try differently
□ NEVER continue if you've broken existing functionality
```

### **Post-Development Checklist**

```
□ Test all related functionality
□ Verify no regressions introduced
□ Check that original issue is actually fixed
□ Review code changes for unintended side effects
□ Create clear documentation of what was changed and why
```

## 🏗️ **ARCHITECTURE PRESERVATION RULES**

### **WebSocket System - CRITICAL PATTERNS**

1. **Message Format Consistency**

   - Backend MUST use LangChain format: `HumanMessage()`, `AIMessage()`
   - Frontend MUST use object format: `{id, content, isUser}`
   - **NEVER** mix dictionary and LangChain formats in the same context

2. **Database Synchronization**

   - **ALWAYS** delete old messages before saving regenerated ones
   - **ALWAYS** use transactions with proper rollback
   - **NEVER** save without checking for existing records

3. **Duplicate Prevention**
   - Frontend checks for content duplicates before adding
   - Backend ensures database consistency
   - **NEVER** rely on only one layer for deduplication

### **State Management Rules**

1. **Frontend State**

   - Page changes load messages via API calls, not WebSocket
   - WebSocket only adds new messages in real-time
   - **NEVER** reload entire message history through WebSocket

2. **Backend Context**
   - Load page history only when context is empty
   - Maintain separate WebSocket context vs API context
   - **NEVER** assume context is synchronized between API and WebSocket

## 🔒 **SECURITY & SAFETY RULES**

### **Credentials & Secrets**

```
NEVER commit:
□ API keys, tokens, passwords
□ Database connection strings with credentials
□ Service account files (*.json)
□ .env files with secrets
□ Personal or client data

ALWAYS:
□ Use .gitignore for sensitive files
□ Use environment variables for secrets
□ Scan commits before pushing
□ Use git hooks to prevent accidental commits
```

### **Code Safety**

```
NEVER:
□ Remove error handling without replacement
□ Skip input validation
□ Use raw SQL without parameterization
□ Expose internal system details in responses
□ Log sensitive information

ALWAYS:
□ Validate all inputs with Pydantic
□ Use proper exception handling
□ Sanitize database queries
□ Log errors for debugging but not secrets
```

## 🐛 **ISSUE RESOLUTION PROTOCOL**

### **Step 1: Issue Analysis**

```
1. Reproduce the issue reliably
2. Identify the exact symptoms vs root cause
3. Trace the data flow to find where it breaks
4. Document current behavior vs expected behavior
5. Check if it's a frontend, backend, or sync issue
```

### **Step 2: Solution Planning**

```
1. Identify the minimal change needed
2. Consider impact on other components
3. Plan testing strategy
4. Create branch with descriptive name
5. Set success criteria
```

### **Step 3: Implementation**

```
1. Make the smallest possible change first
2. Test immediately after each change
3. If anything breaks, revert and try different approach
4. NEVER continue development with broken functionality
5. Document changes as you go
```

### **Step 4: Validation**

```
1. Test the original issue is fixed
2. Test all related functionality still works
3. Test edge cases and error scenarios
4. Get peer review if possible
5. Document the fix for future reference
```

## 📝 **CODE QUALITY RULES**

### **TypeScript/React Rules**

```
□ Use proper TypeScript types, avoid 'any'
□ Prefer functional components with hooks
□ Use React.memo() for expensive components
□ Handle loading and error states properly
□ Use consistent naming conventions
□ Add proper error boundaries
```

### **Python/FastAPI Rules**

```
□ Use type hints for all function signatures
□ Use async/await consistently
□ Proper exception handling with try/catch
□ Use Pydantic for request/response validation
□ Add comprehensive logging
□ Follow dependency injection patterns
```

### **Database Rules**

```
□ Use transactions for multi-step operations
□ Always handle rollback scenarios
□ Use proper indexing for performance
□ Validate foreign key relationships
□ Use migrations for schema changes
□ Test database operations thoroughly
```

## 🚀 **PRODUCTIVITY ENHANCEMENT RULES**

### **Communication Rules**

```
□ Document decisions and trade-offs
□ Use clear, descriptive commit messages
□ Create issues for bugs before fixing them
□ Update documentation when changing behavior
□ Share learnings with the team
```

### **Tool Usage Rules**

```
□ Use provided debug configurations
□ Leverage development tasks in VSCode
□ Use linting and formatting tools
□ Take advantage of AI assistance with proper context
□ Use browser dev tools for frontend debugging
```

### **Testing Rules**

```
□ Test manually before automated tests
□ Write tests for critical business logic
□ Test WebSocket functionality thoroughly
□ Validate API endpoints with proper error cases
□ Test UI components with user interactions
```

## ⚠️ **EMERGENCY PROTOCOLS**

### **When Things Go Wrong**

```
1. STOP - Don't make more changes
2. ASSESS - What exactly is broken?
3. REVERT - Go back to last working state
4. ANALYZE - What caused the issue?
5. PLAN - How to fix without breaking more?
6. IMPLEMENT - Make minimal targeted fix
7. VERIFY - Test thoroughly before continuing
```

### **Red Flags - Stop Immediately If:**

```
□ Multiple features break after your change
□ Database transactions start failing
□ WebSocket connections drop frequently
□ Authentication stops working
□ The frontend won't load
□ Backend throws unhandled exceptions
```

## 📊 **SUCCESS METRICS**

### **Quality Indicators**

```
✅ Changes fix only the intended issue
✅ No new bugs introduced
✅ All existing functionality preserved
✅ Code follows established patterns
✅ Performance doesn't degrade
✅ Security standards maintained
```

### **Productivity Indicators**

```
✅ Issues resolved in single PR
✅ Clear, understandable code changes
✅ Minimal back-and-forth in reviews
✅ Fast, reliable testing process
✅ Efficient debugging workflow
✅ Knowledge sharing and documentation
```

---

## 🎯 **GOLDEN RULE**

> **"When in doubt, make the smallest possible change that fixes the exact issue reported. Nothing more, nothing less. Test thoroughly. Document clearly."**

Remember: It's better to make multiple small, safe changes than one large, risky change that breaks everything.

---

_Last Updated: 2024-06-29_
_Version: 1.0_
