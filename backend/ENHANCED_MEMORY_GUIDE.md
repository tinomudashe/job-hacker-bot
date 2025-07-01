# Enhanced Memory & Learning System for Job Hacker Bot

## Overview

The Enhanced Memory System addresses context loss and improves user experience by implementing:

1. **Conversation Summarization** - Automatically summarizes long conversations to maintain context
2. **User Behavior Learning** - Tracks and learns from user actions and preferences
3. **Persistent Memory** - Maintains context across sessions with vector storage
4. **Smart Context Management** - Trims conversation history intelligently to avoid token limits
5. **Personalized Responses** - Adapts system prompt based on user learning profile

## Key Components

### 1. Enhanced Memory Manager (`enhanced_memory.py`)

**ConversationContext Class:**

- Stores recent messages, conversation summary, and total message count
- Provides structured access to conversation state

**UserLearningProfile Class:**

- Tracks user preferences, interaction patterns, and success metrics
- Enables personalized recommendations based on behavior

**EnhancedMemoryManager Class:**

- Main orchestrator for memory operations
- Handles conversation summarization with configurable triggers
- Manages user behavior tracking and preference learning
- Generates contextual system prompts with user-specific information

### 2. Database Models (`models_db.py`)

**UserPreference Model:**

- Stores key-value pairs of user preferences
- Tracks preference evolution over time
- Examples: preferred_location, job_type, communication_style

**UserBehavior Model:**

- Logs user actions with context and success metrics
- Enables pattern analysis and learning
- Tracks: chat_message, job_search, agent_response, tool_usage

### 3. Integration Points

**Orchestrator Updates:**

- Enhanced system prompt generation with user context
- Conversation history loading with summarization
- Behavior tracking for all user interactions
- Preference learning from search patterns

## Key Features

### Conversation Summarization

- **Trigger**: When conversation exceeds configurable message count (default: 20)
- **Method**: LangChain ConversationSummaryBufferMemory with Gemini
- **Benefits**: Maintains context while staying within token limits
- **Storage**: Summaries stored and retrieved from vector store

### User Behavior Learning

```python
# Example: Track job search patterns
await memory_manager.save_user_behavior(
    action_type="job_search",
    context={
        "query": "software engineer",
        "location": "Poland",
        "results_count": 15,
        "search_method": "basic_api"
    },
    success=True
)
```

### Preference Learning

```python
# Example: Learn location preferences
await memory_manager.save_user_preference("preferred_location", "Warsaw")
```

### Contextual System Prompts

The system now generates dynamic prompts that include:

- User's job search patterns and preferences
- Communication style preferences
- Success metrics and feedback history
- Skill interests and career goals
- Interaction patterns (peak hours, preferred detail level)

## Implementation Benefits

### 1. Context Preservation

- **Problem**: Long conversations lose context, bot forgets earlier interactions
- **Solution**: Intelligent summarization maintains relevant context while trimming old messages
- **Result**: Bot remembers important details across extended conversations

### 2. Personalized Experience

- **Problem**: Generic responses don't adapt to user preferences
- **Solution**: Learning system tracks user behavior and preferences
- **Result**: Increasingly personalized recommendations and communication style

### 3. Improved Efficiency

- **Problem**: Token limits cause conversation truncation
- **Solution**: Smart context management with summarization
- **Result**: Optimal use of available context window

### 4. Learning from Feedback

- **Problem**: Bot doesn't improve from user interactions
- **Solution**: Behavior tracking with success metrics
- **Result**: System learns what works for each user

## Usage Examples

### Enhanced Chat Experience

```
User: "Find software engineering jobs in Poland"
Bot: [Learns: user prefers "Poland" location, "software engineering" roles]

Later conversation:
User: "Show me more jobs"
Bot: [Uses learned preferences] "Here are more software engineering positions in Poland based on your preferences..."
```

### Adaptive Communication

```
User consistently asks for detailed explanations
Bot learns: preferred_detail_level = "detailed"
Future responses: Automatically provides comprehensive explanations
```

### Pattern Recognition

```
User searches jobs at 9 AM daily
User prefers remote work
User clicks on senior-level positions
Bot learns these patterns and adapts recommendations
```

## Configuration

### Memory Thresholds

- `summary_trigger_length`: 20 messages (trigger summarization)
- `max_recent_messages`: 10 (keep in recent context)
- `context_trim_threshold`: 4000 tokens (trim if exceeded)

### Learning Parameters

- Behavior retention: 30 days for analysis
- Preference updates: Real-time with fallback values
- Success metrics: Rolling 7-day windows

## Database Migration

Run the migration to create new tables:

```bash
cd backend
alembic upgrade head
```

This creates:

- `user_preferences` table for preference storage
- `user_behaviors` table for behavior tracking

## Error Handling

The system includes comprehensive fallbacks:

- If enhanced memory fails, falls back to basic chat history
- If preference tracking fails, operation continues normally
- If summarization fails, uses recent messages only
- All errors are logged but don't break core functionality

## Future Enhancements

1. **Advanced Analytics Dashboard**

   - User behavior insights
   - Success rate tracking
   - Preference evolution visualization

2. **Proactive Suggestions**

   - Job recommendations based on learned patterns
   - Timing suggestions for job applications
   - Skill development recommendations

3. **Cross-Session Learning**

   - Learn from successful patterns across all users (anonymized)
   - Best practice recommendations
   - Industry trend integration

4. **Enhanced Feedback Loop**
   - Explicit user feedback collection
   - A/B testing for response strategies
   - Continuous improvement algorithms

## Performance Considerations

- **Vector Store**: Uses FAISS for efficient similarity search
- **Caching**: User profiles cached for session duration
- **Async Operations**: All database operations are asynchronous
- **Memory Management**: Automatic cleanup of old behavior data
- **Token Optimization**: Smart context trimming prevents API limits

## Monitoring

Key metrics to monitor:

- Conversation summary success rate
- User preference update frequency
- Behavior tracking coverage
- Context window utilization
- Response personalization effectiveness

The enhanced memory system transforms Job Hacker Bot from a stateless assistant into a learning, adaptive career companion that improves with every interaction.
