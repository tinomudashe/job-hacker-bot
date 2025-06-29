# 🧹 Orchestrator Refactoring Guide

## 🎯 Goal: Reduce orchestrator.py from 3178 lines → ~500 lines

---

## 📊 Current State

### ✅ **What You Already Have (Great Job!)**
- **Specialized Files**: You've created excellent file organization
- **Working System**: Regeneration, chat switching, Graph RAG all working
- **Clean Architecture**: Separate modules for different concerns

### ❌ **The Problem**
- **25+ tools still defined in orchestrator.py** (lines 484-2573)
- **Orchestrator is 3178 lines** (should be ~500)
- **Hard to maintain** and debug specific tools

---

## 🗂️ Your Existing Files → Tool Categories

| **Your File** | **Move These Tools From Orchestrator** |
|---------------|----------------------------------------|
| `job_search.py` | `search_jobs_tool`, `search_jobs_with_browser` |
| `resume_generator.py` | `generate_tailored_resume`, `create_resume_from_scratch` |
| `cv_generator.py` | `refine_cv_for_role`, `enhance_resume_section` |
| `cover_letter_generator.py` | `generate_cover_letter`, `generate_cover_letter_from_url` |
| `pdf_generator.py` | `generate_resume_pdf`, `show_resume_download_options` |
| `documents.py` | `enhanced_document_search`, `analyze_specific_document`, `get_document_insights`, `list_documents`, `read_document` |

### 🆕 **New Files Needed**
- `career_tools.py` → `get_interview_preparation_guide`, `get_salary_negotiation_advice`, `create_career_development_plan`, `get_cv_best_practices`, `analyze_skills_gap`, `get_ats_optimization_tips`
- `profile_tools.py` → `update_personal_information`, `add_work_experience`, `add_education`, `set_skills`

---

## 🔄 Safe Refactoring Steps

### **Step 1: Backup First** 
```bash
cp orchestrator.py orchestrator_backup.py
```

### **Step 2: Move Tools ONE Category at a Time**

#### **Example: Move Job Search Tools**
1. **Cut from orchestrator.py** (lines ~484-680):
   ```python
   @tool
   async def search_jobs_tool(...):
       # function body
   
   @tool  
   async def search_jobs_with_browser(...):
       # function body
   ```

2. **Add to `job_search.py`**:
   ```python
   # Add at end of job_search.py
   from langchain.tools import tool
   
   @tool
   async def search_jobs_tool(...):
       # paste function body here
   
   @tool
   async def search_jobs_with_browser(...):
       # paste function body here
   ```

3. **Update orchestrator.py imports**:
   ```python
   # Add to imports section
   from app.job_search import search_jobs_tool, search_jobs_with_browser
   
   # Update tools list
   tools = [
       search_jobs_tool,
       search_jobs_with_browser,
       # ... other tools
   ]
   ```

4. **Test**: Verify regeneration and job search still work

### **Step 3: Repeat for Each Category**
- Move one category at a time
- Test after each move
- Don't touch WebSocket logic

---

## 🚨 **DON'T TOUCH** (Keep in orchestrator.py)

### **WebSocket Handling** ✅ Keep
```python
@router.websocket("/ws/orchestrator")
async def orchestrator_websocket(...):
    # All the WebSocket message handling logic
    # Regeneration logic 
    # Page switching logic
```

### **Agent Setup** ✅ Keep  
```python
def create_master_agent(tools: List, ...):
    # Agent creation logic
    # Prompt setup
    # LLM configuration
```

### **Helper Functions** ✅ Keep
```python
async def get_or_create_resume():
    # Resume helper functions used by WebSocket
```

---

## 📋 Tool Inventory (25 tools to move)

### **Job Search** (2 tools)
- [ ] `search_jobs_tool` → `job_search.py`
- [ ] `search_jobs_with_browser` → `job_search.py`

### **Resume/CV** (8 tools)  
- [ ] `generate_tailored_resume` → `resume_generator.py`
- [ ] `enhance_resume_section` → `cv_generator.py`
- [ ] `create_resume_from_scratch` → `resume_generator.py`
- [ ] `refine_cv_for_role` → `cv_generator.py`
- [ ] `get_cv_best_practices` → `career_tools.py` (new)
- [ ] `analyze_skills_gap` → `career_tools.py` (new)
- [ ] `get_ats_optimization_tips` → `career_tools.py` (new)
- [ ] `show_resume_download_options` → `pdf_generator.py`

### **Documents** (5 tools)
- [ ] `enhanced_document_search` → `documents.py`
- [ ] `analyze_specific_document` → `documents.py` 
- [ ] `get_document_insights` → `documents.py`
- [ ] `list_documents` → `documents.py`
- [ ] `read_document` → `documents.py`

### **Cover Letters** (2 tools)
- [ ] `generate_cover_letter_from_url` → `cover_letter_generator.py`
- [ ] `generate_cover_letter` → `cover_letter_generator.py`

### **Career Guidance** (3 tools)
- [ ] `get_interview_preparation_guide` → `career_tools.py` (new)
- [ ] `get_salary_negotiation_advice` → `career_tools.py` (new) 
- [ ] `create_career_development_plan` → `career_tools.py` (new)

### **Profile Management** (4 tools)
- [ ] `update_personal_information` → `profile_tools.py` (new)
- [ ] `add_work_experience` → `profile_tools.py` (new)
- [ ] `add_education` → `profile_tools.py` (new)
- [ ] `set_skills` → `profile_tools.py` (new)

### **PDF Generation** (1 tool)
- [ ] `generate_resume_pdf` → `pdf_generator.py`

---

## 🧪 **Testing Checklist** (After Each Move)

- [ ] ✅ Regeneration button works 
- [ ] ✅ Chat switching preserves messages
- [ ] ✅ New messages appear correctly
- [ ] ✅ The moved tool category still works
- [ ] ✅ WebSocket connection stable
- [ ] ✅ No import errors

---

## 🎉 **Expected Results**

### **Before Refactoring**
```
orchestrator.py: 3178 lines (BLOATED)
├── WebSocket logic: ~800 lines
├── Tool definitions: ~2300 lines ❌ 
└── Agent setup: ~100 lines
```

### **After Refactoring** 
```
orchestrator.py: ~500 lines (CLEAN)
├── WebSocket logic: ~800 lines ✅
├── Tool imports: ~50 lines ✅
└── Agent setup: ~100 lines ✅

+ 8 specialized tool files with organized functions
```

---

## 🚀 **Quick Start**

1. **Read** `REGENERATION_FIX_DOCUMENTATION.md` first
2. **Backup** orchestrator.py  
3. **Start small**: Move job search tools first (2 tools only)
4. **Test thoroughly** before moving next category
5. **One category at a time** until all 25 tools moved

**Remember**: The goal is cleaner code, not breaking working functionality! 🎯 