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
async def get_ats_optimization_tips(
        file_format: str = "PDF",
        industry: str = ""
    ) -> str:
    """Get specific tips for optimizing your CV to pass Applicant Tracking Systems (ATS).
    
    Args:
        file_format: CV file format you're using (PDF, DOCX, TXT)
        industry: Target industry for specific ATS considerations
    
    Returns:
        Comprehensive ATS optimization guide with actionable tips
    """
    try:
        prompt = ChatPromptTemplate.from_template(
            """You are an ATS optimization expert. Provide comprehensive, technical guidance for passing modern ATS systems.

TARGET CONTEXT:
- File Format: {file_format}
- Industry: {industry}

Provide detailed ATS optimization guidance:

## 🤖 **Understanding ATS Systems**
- How modern ATS systems work
- What ATS algorithms look for
- Common ATS software types and their quirks
- Industry-specific ATS considerations

## 📄 **File Format Optimization**
- Best practices for {file_format} format
- Formatting do's and don'ts
- Font and layout recommendations
- File naming conventions

## 🔍 **Keyword Optimization**
### Keyword Research
- How to identify relevant keywords
- Where to find industry-specific terms
- Balancing keyword density naturally
- Using variations and synonyms

### Keyword Placement
- Strategic locations for keywords
- Section headers and their importance
- Natural integration techniques
- Avoiding keyword stuffing

## 📋 **Structure & Formatting**
### Section Organization
- ATS-friendly section headers
- Optimal section ordering
- Contact information formatting
- Date formats that ATS systems prefer

### Content Formatting
- Bullet points vs. paragraphs
- Special characters to avoid
- Table and column usage
- Header and footer limitations

## ✅ **Technical Best Practices**
- Font choices that scan well
- Margins and spacing guidelines
- Graphics and images considerations
- Links and hypertext handling

## 🧪 **Testing Your CV**
- Free ATS testing tools
- How to interpret ATS scan results
- Common parsing errors to fix
- Quality assurance checklist

## 📊 **Tracking & Iteration**
- Metrics to monitor application success
- When and how to update your CV
- A/B testing different versions
- Industry benchmarks for response rates

Provide specific, technical advice that ensures maximum ATS compatibility."""
        )
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-preview-03-25",
            temperature=0.6,
            callbacks=[tracer]
        )
        
        chain = prompt | llm | StrOutputParser()
        
        tips = await chain.ainvoke({
            "file_format": file_format,
            "industry": industry or "general"
        })
        
        return f"""## 🤖 **ATS Optimization Guide**

📁 **Format:** {file_format} | 🏢 **Industry:** {industry or 'General'}

{tips}

---

**🔧 Immediate Actions:**
1. **Test Your Current CV**: Use Jobscan or similar ATS checker tools
2. **Review Keywords**: Compare your CV against 2-3 target job postings
3. **Fix Formatting Issues**: Address any parsing problems identified
4. **Create ATS Version**: Keep a simplified version specifically for ATS systems

**⚠️ Quick Checklist:**
- ✅ Uses standard section headers (Experience, Education, Skills)
- ✅ No graphics, tables, or complex formatting
- ✅ Keywords appear naturally throughout content
- ✅ Consistent date formatting (MM/YYYY)
- ✅ Contact info in simple text format
- ✅ File saved with professional naming convention

**🔗 Related Tools:**
- `generate tailored resume` - Create ATS-optimized content
- `enhance my resume section` - Improve keyword density"""
        
    except Exception as e:
        log.error(f"Error getting ATS optimization tips: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error while getting ATS tips: {str(e)}. Please try again."