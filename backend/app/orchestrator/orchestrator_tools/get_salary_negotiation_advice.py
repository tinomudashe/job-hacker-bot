from langchain_core.tools import tool
import logging
from langchain.callbacks import LangChainTracer
from langsmith import Client

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)
tracer = LangChainTracer(client=Client())

@tool
async def get_salary_negotiation_advice(
        job_title: str,
        experience_level: str = "mid-level", 
        location: str = "",
        industry: str = ""
    ) -> str:
    """Get comprehensive salary negotiation strategies and market data insights.
    
    Args:
        job_title: Position you're negotiating for
        experience_level: Your experience level (entry-level, mid-level, senior, executive)
        location: Job location for market rate context
        industry: Industry for sector-specific advice
    
    Returns:
        Detailed salary negotiation guide with strategies and market insights
    """
    try:
        prompt = ChatPromptTemplate.from_template(
            """You are a compensation and career negotiation expert. Provide comprehensive salary negotiation guidance.

NEGOTIATION CONTEXT:
- Job Title: {job_title}
- Experience Level: {experience_level}
- Location: {location}
- Industry: {industry}

Provide detailed negotiation strategy and advice:

## 💰 **Market Research & Benchmarking**
### Salary Research Sources
- Best websites and tools for salary data
- How to interpret salary ranges accurately
- Geographic and industry adjustments
- Experience level modifiers

### Compensation Package Components
- Base salary considerations
- Bonus and incentive structures
- Benefits and perquisites
- Equity and stock options
- Remote work and flexibility value

## 🎯 **Negotiation Strategy**
### Preparation Phase
- How to determine your target range
- Building your value proposition
- Documentation of achievements and impact
- Market rate justification techniques

### Timing Considerations
- When to bring up compensation
- How to respond to salary questions
- Negotiating after offer receipt
- Multiple offer leverage strategies

### Communication Tactics
- Scripts and language for negotiations
- How to present counter-offers professionally
- Negotiating non-salary benefits
- Handling objections and pushback

## 📋 **Negotiation Framework**
### Initial Offer Response
- How to buy time for consideration
- Expressing enthusiasm while negotiating
- Questions to ask about the offer
- Professional response templates

### Counter-Offer Strategy
- How to structure compelling counter-offers
- Supporting your requests with data
- Prioritizing different compensation elements
- Alternative proposals if budget is fixed

### Closing the Deal
- Finalizing agreed terms professionally
- Getting offers in writing
- Graceful acceptance or decline
- Maintaining relationships regardless of outcome

## 🎭 **Common Scenarios & Responses**
### Difficult Situations
- "Our budget is fixed" responses
- Geographic pay differences
- Internal equity concerns
- First-time negotiator anxiety

### Advanced Strategies
- Multiple offer negotiations
- Retention counter-offers
- Promotion and raise requests
- Contract vs. full-time considerations

## ⚠️ **Pitfalls to Avoid**
### Negotiation Mistakes
- Red flags that hurt your chances
- Overplaying your hand
- Burning bridges unnecessarily
- Focusing only on salary

### Professional Etiquette
- Maintaining positive relationships
- Respecting company constraints
- Being prepared to walk away
- Following up appropriately

## 📊 **Market Insights**
- Typical salary ranges for {experience_level} {job_title} roles
- Industry-specific compensation trends
- Geographic variations and cost of living
- Emerging benefits and perks trends
- Economic factors affecting compensation

Provide specific, actionable negotiation advice with realistic expectations."""
        )
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-preview-03-25",
            temperature=0.7,
            callbacks=[tracer]
        )
        
        chain = prompt | llm | StrOutputParser()
        
        advice = await chain.ainvoke({
            "job_title": job_title,
            "experience_level": experience_level,
            "location": location or "general market",
            "industry": industry or "general"
        })
        
        return f"""## 💰 **Salary Negotiation Strategy Guide**

**Role:** {job_title} | **Level:** {experience_level} | **Market:** {location or 'General'}

{advice}

---

**🚀 Action Plan:**
1. **Research Phase** (Before applying): Gather market data and set target range
2. **Application Phase**: Avoid early salary discussions, focus on fit
3. **Interview Phase**: Demonstrate value, delay compensation talks
4. **Offer Phase**: Evaluate total package, prepare counter-offer
5. **Negotiation Phase**: Present professional counter with justification
6. **Decision Phase**: Make informed choice aligned with career goals

**📊 Negotiation Checklist:**
- ✅ Researched market rates from multiple sources
- ✅ Calculated total compensation package value
- ✅ Prepared specific examples of your value/impact
- ✅ Determined acceptable range and walk-away point
- ✅ Practiced negotiation conversations
- ✅ Ready to discuss non-salary benefits

**⚡ Key Reminders:**
- **Be Professional**: Maintain positive tone throughout
- **Focus on Value**: Emphasize what you bring to the role
- **Consider Total Package**: Look beyond just base salary
- **Know Your Worth**: But be realistic about market conditions
- **Have Alternatives**: Negotiate from position of choice, not desperation

**🔗 Related Tools:**
- `search jobs for [role]` - Research current market opportunities
- `get interview preparation guide` - Prepare to demonstrate value"""
        
    except Exception as e:
        log.error(f"Error getting salary negotiation advice: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error while getting negotiation advice: {str(e)}. Please try again."
