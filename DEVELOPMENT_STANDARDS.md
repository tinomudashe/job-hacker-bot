# Job Hacker Bot - Development Standards

## 🚀 **QUICK START GUIDE**

### **Repository Setup**

```bash
# Clone and setup
git clone git@github.com:tinomudashe/job-hacker-bot.git
cd job-hacker-bot

# Install dependencies
cd Frontend && npm install
cd ../backend && pip install -r requirements.txt

# Setup environment
cp .env.example .env  # Configure your environment variables
cd backend && alembic upgrade head  # Run database migrations

# Start development
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd Frontend && npm run dev
```

### **Branch Strategy**

```bash
# Always create feature/fix branches from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
# or
git checkout -b fix/specific-issue-only

# Never work directly on main
# Never mix multiple features in one branch
```

## 📋 **CODE STANDARDS**

### **TypeScript/React Patterns**

```typescript
// ✅ Component Structure
import { useState, useCallback, memo } from "react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface ComponentProps {
  id: string;
  onUpdate: (data: UpdateData) => Promise<void>;
}

export const Component = memo(({ id, onUpdate }: ComponentProps) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpdate = useCallback(
    async (data: UpdateData) => {
      setLoading(true);
      setError(null);

      try {
        await onUpdate(data);
        toast.success("Updated successfully");
      } catch (err) {
        const message = err instanceof Error ? err.message : "Update failed";
        setError(message);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    },
    [onUpdate]
  );

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  return (
    <Button
      onClick={() => handleUpdate(data)}
      disabled={loading}
      className="..."
    >
      {loading ? "Updating..." : "Update"}
    </Button>
  );
});

Component.displayName = "Component";
```

### **Python/FastAPI Patterns**

```python
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models_db import User, ChatMessage

router = APIRouter(prefix="/api/messages", tags=["messages"])

# ✅ Request/Response Models
class MessageRequest(BaseModel):
    content: str
    page_id: Optional[str] = None

    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) > 10000:
            raise ValueError('Content too long')
        return v.strip()

class MessageResponse(BaseModel):
    id: str
    content: str
    is_user_message: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ✅ Endpoint Structure
@router.post("/", response_model=MessageResponse)
async def create_message(
    request: MessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """Create a new chat message."""

    try:
        # Validate permissions
        if request.page_id:
            # Check if user owns the page
            page = await db.get(Page, request.page_id)
            if not page or page.user_id != user.id:
                raise HTTPException(status_code=404, detail="Page not found")

        # Create message
        message = ChatMessage(
            user_id=user.id,
            page_id=request.page_id,
            content=request.content,
            is_user_message=True
        )

        db.add(message)
        await db.commit()
        await db.refresh(message)

        log.info(f"Created message {message.id} for user {user.id}")
        return MessageResponse.from_orm(message)

    except Exception as e:
        await db.rollback()
        log.error(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail="Failed to create message")
```

### **Database Operations**

```python
# ✅ Proper Transaction Handling
async def update_message_with_cleanup(
    db: AsyncSession,
    message_id: str,
    new_content: str,
    user_id: str
) -> ChatMessage:
    """Update message and clean up subsequent messages."""

    try:
        async with db.begin():
            # Get original message
            message = await db.get(ChatMessage, message_id)
            if not message or message.user_id != user_id:
                raise ValueError("Message not found or unauthorized")

            # Update content
            message.content = new_content
            message.updated_at = datetime.utcnow()

            # Delete subsequent messages
            subsequent = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.page_id == message.page_id)
                .where(ChatMessage.created_at > message.created_at)
            )

            for sub_msg in subsequent.scalars():
                await db.delete(sub_msg)

            await db.flush()  # Ensure changes are written
            return message

    except Exception as e:
        # Rollback happens automatically with async context manager
        log.error(f"Error updating message: {e}")
        raise
```

## 🎯 **TESTING STANDARDS**

### **Frontend Testing**

```typescript
// ✅ Component Testing
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MessageComponent } from "./MessageComponent";

describe("MessageComponent", () => {
  it("should handle edit message successfully", async () => {
    const mockOnEdit = jest.fn().mockResolvedValue(undefined);

    render(<MessageComponent message={mockMessage} onEdit={mockOnEdit} />);

    // Trigger edit
    fireEvent.click(screen.getByRole("button", { name: /edit/i }));

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "New content" } });
    fireEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(mockOnEdit).toHaveBeenCalledWith(mockMessage.id, "New content");
    });

    expect(screen.getByText("Updated successfully")).toBeInTheDocument();
  });
});
```

### **Backend Testing**

```python
# ✅ API Testing
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_message_success(
    client: AsyncClient,
    authenticated_headers: dict,
    test_user: User
):
    """Test successful message creation."""

    payload = {
        "content": "Test message content",
        "page_id": None
    }

    response = await client.post(
        "/api/messages/",
        json=payload,
        headers=authenticated_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["content"] == payload["content"]
    assert data["is_user_message"] is True
    assert "id" in data
    assert "created_at" in data

@pytest.mark.asyncio
async def test_websocket_message_flow(
    client: AsyncClient,
    test_user: User,
    auth_token: str
):
    """Test complete WebSocket message flow."""

    with client.websocket_connect(f"/api/ws/orchestrator?token={auth_token}") as websocket:
        # Send message
        test_content = "Hello, test message"
        websocket.send_text(test_content)

        # Should receive AI response
        response = websocket.receive_text()
        assert response is not None
        assert len(response) > 0

        # Verify message saved to database
        # ... database verification logic
```

## 🔒 **SECURITY STANDARDS**

### **Input Validation**

```python
# ✅ Always validate and sanitize inputs
from pydantic import BaseModel, validator, Field
import bleach

class UserInput(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)

    @validator('content')
    def sanitize_content(cls, v):
        # Remove dangerous HTML/JS
        clean_content = bleach.clean(
            v,
            tags=[],
            attributes={},
            strip=True
        )
        return clean_content.strip()
```

### **Authentication Checks**

```python
# ✅ Always verify user permissions
async def verify_resource_ownership(
    resource_id: str,
    user: User,
    db: AsyncSession,
    resource_type: str = "page"
) -> bool:
    """Verify user owns the requested resource."""

    if resource_type == "page":
        resource = await db.get(Page, resource_id)
        return resource and resource.user_id == user.id

    elif resource_type == "message":
        resource = await db.get(ChatMessage, resource_id)
        return resource and resource.user_id == user.id

    return False
```

## 📊 **LOGGING STANDARDS**

### **Structured Logging**

```python
import structlog
from typing import Any, Dict

# ✅ Consistent logging format
log = structlog.get_logger()

async def process_user_message(
    user_id: str,
    content: str,
    page_id: Optional[str] = None
) -> Dict[str, Any]:
    """Process user message with proper logging."""

    log.info(
        "Processing user message",
        user_id=user_id,
        page_id=page_id,
        content_length=len(content),
        timestamp=datetime.utcnow().isoformat()
    )

    try:
        result = await agent.process(content)

        log.info(
            "Message processed successfully",
            user_id=user_id,
            page_id=page_id,
            response_length=len(result.get("output", "")),
            processing_time=result.get("duration", 0)
        )

        return result

    except Exception as e:
        log.error(
            "Failed to process message",
            user_id=user_id,
            page_id=page_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

## 🛠️ **DEVELOPMENT TOOLS**

### **Pre-commit Hooks**

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        args: [--line-length=88]

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        args: [--max-line-length=88]

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v2.6.2
    hooks:
      - id: prettier
        files: \.(js|ts|jsx|tsx|json|css|md)$
```

### **Environment Setup**

```bash
# Development environment
export DEBUG=true
export LOG_LEVEL=DEBUG
export DATABASE_URL="sqlite:///./dev.db"

# Testing environment
export TESTING=true
export DATABASE_URL="sqlite:///./test.db"

# Production environment
export DEBUG=false
export LOG_LEVEL=INFO
export DATABASE_URL="postgresql://..."
```

## 📈 **PERFORMANCE STANDARDS**

### **Frontend Performance**

```typescript
// ✅ Component optimization
import { memo, useMemo, useCallback } from "react";

const ExpensiveComponent = memo(({ data, onUpdate }: Props) => {
  // Memoize expensive calculations
  const processedData = useMemo(() => {
    return data.map((item) => expensiveProcessing(item));
  }, [data]);

  // Memoize callbacks
  const handleUpdate = useCallback(
    (id: string) => {
      onUpdate(id);
    },
    [onUpdate]
  );

  return (
    <div>
      {processedData.map((item) => (
        <Item key={item.id} data={item} onClick={handleUpdate} />
      ))}
    </div>
  );
});
```

### **Backend Performance**

```python
# ✅ Database optimization
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def get_user_with_messages(
    db: AsyncSession,
    user_id: str,
    limit: int = 50
) -> User:
    """Get user with recent messages efficiently."""

    # Use eager loading to avoid N+1 queries
    stmt = (
        select(User)
        .options(
            selectinload(User.messages)
            .selectinload(ChatMessage.page)
        )
        .where(User.id == user_id)
    )

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        # Limit messages in memory instead of additional query
        user.messages = sorted(
            user.messages,
            key=lambda m: m.created_at,
            reverse=True
        )[:limit]

    return user
```

## 🎯 **SUCCESS CRITERIA**

### **Quality Gates**

```
✅ All tests pass
✅ Code coverage > 80%
✅ No TypeScript errors
✅ No ESLint errors
✅ Black formatting applied
✅ No security vulnerabilities
✅ Performance metrics within acceptable range
✅ Documentation updated
```

### **Definition of Done**

```
✅ Feature works as specified
✅ Edge cases handled
✅ Error scenarios tested
✅ Responsive design verified
✅ Accessibility standards met
✅ Performance optimized
✅ Security review completed
✅ Documentation written
✅ Code reviewed and approved
```

---

## 🎯 **REMEMBER**

> **"Code is read more often than it's written. Write code that your future self will thank you for."**

_Last Updated: 2024-06-29_
_Version: 1.0_
