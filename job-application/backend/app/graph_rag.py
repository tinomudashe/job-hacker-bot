import logging
from typing import List, Dict, Optional, Any
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document as LCDocument
from langchain_graph_retriever import GraphRetriever
from graph_retriever.strategies import Eager
# from langchain_graph_retriever.transformers import ShreddingTransformer  # Optional, not needed for basic functionality
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models_db import Document, User
from app.enhanced_memory import AsyncSafeEnhancedMemoryManager
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

class EnhancedGraphRAG:
    """
    Graph RAG system that creates intelligent connections between documents, 
    job requirements, skills, and user experiences for smarter agent reasoning.
    """
    
    def __init__(self, user_id: str, db: AsyncSession):
        self.user_id = user_id
        self.db = db
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        self.llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash')
        self.vector_store = None
        self.graph_retriever = None
        
    async def initialize(self):
        """Initialize the Graph RAG system with user documents"""
        try:
            # Get user and their documents
            user_result = await self.db.execute(select(User).where(User.id == self.user_id))
            user = user_result.scalar_one()
            
            doc_result = await self.db.execute(
                select(Document).where(Document.user_id == self.user_id)
            )
            documents = doc_result.scalars().all()
            
            # Initialize memory manager for learning context
            memory_manager = AsyncSafeEnhancedMemoryManager(self.db, user)
            user_profile = await memory_manager._get_user_learning_profile_safe()
            
            # Create enhanced documents with graph metadata
            enhanced_docs = await self._create_enhanced_documents(documents, user, user_profile)
            
            if not enhanced_docs:
                logger.warning(f"No documents available for Graph RAG initialization for user {self.user_id}")
                return False
            
            # Create vector store with graph-compatible documents
            self.vector_store = InMemoryVectorStore.from_documents(
                documents=enhanced_docs,
                embedding=self.embeddings,
            )
            
            # Create graph retriever with intelligent traversal strategies
            self.graph_retriever = GraphRetriever(
                store=self.vector_store,
                edges=self._define_graph_edges(),
                strategy=Eager(k=8, start_k=2, max_depth=3),  # More comprehensive retrieval
            )
            
            logger.info(f"Graph RAG initialized for user {self.user_id} with {len(enhanced_docs)} enhanced documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Graph RAG for user {self.user_id}: {e}")
            return False
    
    async def _create_enhanced_documents(self, documents: List[Document], user: User, user_profile) -> List[LCDocument]:
        """Create enhanced documents with rich metadata for graph traversal"""
        enhanced_docs = []
        
        try:
            # Add user profile document as foundation
            user_doc = self._create_user_profile_document(user, user_profile)
            enhanced_docs.append(user_doc)
            
            # Process each user document
            for doc in documents:
                if not doc.content:
                    continue
                
                # Extract metadata from document content
                metadata = await self._extract_document_metadata(doc, user_profile)
                
                # Split document into semantic chunks with preserved context
                chunks = await self._create_semantic_chunks(doc, metadata)
                enhanced_docs.extend(chunks)
            
            # Add synthetic knowledge documents
            knowledge_docs = await self._create_knowledge_documents(user_profile)
            enhanced_docs.extend(knowledge_docs)
            
            return enhanced_docs
            
        except Exception as e:
            logger.error(f"Error creating enhanced documents: {e}")
            return []
    
    def _create_user_profile_document(self, user: User, user_profile) -> LCDocument:
        """Create a comprehensive user profile document for graph connections"""
        
        # Extract skills and preferences
        skills = []
        industries = []
        job_titles = []
        
        if user_profile and user_profile.preferences:
            skills = [key.replace("cv_skill_", "").replace("_", " ").title() 
                     for key in user_profile.preferences.keys() 
                     if key.startswith("cv_skill_")]
            
            preferred_industry = user_profile.preferences.get("preferred_industry")
            if preferred_industry:
                industries.append(preferred_industry)
        
        if user_profile and user_profile.job_search_patterns:
            job_titles = user_profile.job_search_patterns.get("common_job_titles", [])
        
        # Create rich user context
        content = f"""
        Professional Profile: {user.name or 'Professional'}
        Email: {user.email or 'N/A'}
        Location: {user.address or 'N/A'}
        LinkedIn: {user.linkedin or 'N/A'}
        
        Core Technical Skills: {', '.join(skills[:10]) if skills else 'General Skills'}
        Target Industries: {', '.join(industries) if industries else 'Technology'}
        Career Focus: {', '.join(job_titles[:5]) if job_titles else 'Software Engineering'}
        
        Professional Summary: Experienced professional seeking opportunities in {', '.join(industries[:2]) if industries else 'technology sector'} 
        with expertise in {', '.join(skills[:5]) if skills else 'software development'}.
        """
        
        return LCDocument(
            page_content=content.strip(),
            metadata={
                "document_type": "user_profile",
                "skills": skills[:10],
                "industries": industries,
                "job_titles": job_titles[:5],
                "location": user.address or "remote",
                "experience_level": user_profile.preferences.get("experience_years", "mid") if user_profile and user_profile.preferences else "mid",
                "document_id": "user_profile"
            }
        )
    
    async def _extract_document_metadata(self, doc: Document, user_profile) -> Dict[str, Any]:
        """Extract rich metadata from document content using AI"""
        
        try:
            # Use LLM to extract structured metadata
            extraction_prompt = f"""
            Analyze this {doc.type} document and extract structured metadata.
            Return a JSON object with the following fields:
            - skills: list of technical skills mentioned
            - industries: list of industries/sectors mentioned  
            - job_titles: list of job titles/roles mentioned
            - experience_level: estimated experience level (entry/mid/senior)
            - technologies: list of technologies/tools mentioned
            - achievements: list of key achievements or accomplishments
            - education: educational background mentioned
            - certifications: any certifications mentioned
            
            Document content:
            {doc.content[:2000]}  # Limit content for processing
            
            Return only valid JSON:
            """
            
            result = await self.llm.ainvoke(extraction_prompt)
            
            try:
                metadata = json.loads(result.content)
            except json.JSONDecodeError:
                # Fallback to basic extraction
                metadata = self._extract_metadata_fallback(doc.content)
            
            # Add document-specific metadata
            metadata.update({
                "document_type": doc.type,
                "document_id": doc.id,
                "document_name": doc.name,
                "upload_date": doc.date_created.isoformat() if doc.date_created else None,
                "content_length": len(doc.content) if doc.content else 0
            })
            
            return metadata
            
        except Exception as e:
            logger.warning(f"AI metadata extraction failed for doc {doc.id}: {e}")
            return self._extract_metadata_fallback(doc.content)
    
    def _extract_metadata_fallback(self, content: str) -> Dict[str, Any]:
        """Fallback metadata extraction using pattern matching"""
        
        # Common tech skills patterns
        tech_skills = []
        skill_patterns = [
            r'\b(Python|Java|JavaScript|TypeScript|React|Node\.js|Angular|Vue|C\+\+|C#|Go|Rust|Swift|Kotlin)\b',
            r'\b(AWS|Azure|GCP|Docker|Kubernetes|Git|Linux|SQL|NoSQL|MongoDB|PostgreSQL)\b',
            r'\b(Machine Learning|AI|Data Science|Analytics|Cloud Computing|DevOps|API|REST|GraphQL)\b'
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            tech_skills.extend([match.title() for match in matches])
        
        # Experience level indicators
        experience_level = "mid"
        if any(term in content.lower() for term in ["senior", "lead", "principal", "architect", "manager"]):
            experience_level = "senior"
        elif any(term in content.lower() for term in ["entry", "junior", "graduate", "intern"]):
            experience_level = "entry"
        
        return {
            "skills": list(set(tech_skills)),
            "industries": ["Technology"],
            "job_titles": [],
            "experience_level": experience_level,
            "technologies": list(set(tech_skills)),
            "achievements": [],
            "education": [],
            "certifications": []
        }
    
    async def _create_semantic_chunks(self, doc: Document, metadata: Dict[str, Any]) -> List[LCDocument]:
        """Create semantic chunks that preserve context and relationships"""
        
        chunks = []
        content = doc.content
        
        # Split into logical sections
        sections = self._split_into_sections(content)
        
        for i, section in enumerate(sections):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "section_type": self._identify_section_type(section),
                "chunk_id": f"{doc.id}_chunk_{i}"
            })
            
            chunk = LCDocument(
                page_content=section,
                metadata=chunk_metadata
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_into_sections(self, content: str) -> List[str]:
        """Split content into logical sections"""
        
        # Split by common resume/document sections
        section_patterns = [
            r'\n\s*(?:EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT)\s*\n',
            r'\n\s*(?:EDUCATION|ACADEMIC BACKGROUND)\s*\n',
            r'\n\s*(?:SKILLS|TECHNICAL SKILLS|COMPETENCIES)\s*\n',
            r'\n\s*(?:PROJECTS|PROJECT EXPERIENCE)\s*\n',
            r'\n\s*(?:CERTIFICATIONS|CERTIFICATES)\s*\n',
            r'\n\s*(?:SUMMARY|PROFILE|OBJECTIVE)\s*\n'
        ]
        
        # Try to split by sections first
        for pattern in section_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                sections = re.split(pattern, content, flags=re.IGNORECASE)
                return [section.strip() for section in sections if section.strip()]
        
        # Fallback to paragraph splitting
        paragraphs = content.split('\n\n')
        return [para.strip() for para in paragraphs if len(para.strip()) > 50]
    
    def _identify_section_type(self, section: str) -> str:
        """Identify the type of document section"""
        
        section_lower = section.lower()
        
        if any(keyword in section_lower for keyword in ["experience", "work", "employment", "position"]):
            return "experience"
        elif any(keyword in section_lower for keyword in ["education", "degree", "university", "college"]):
            return "education"
        elif any(keyword in section_lower for keyword in ["skills", "technical", "programming", "tools"]):
            return "skills"
        elif any(keyword in section_lower for keyword in ["project", "developed", "built", "created"]):
            return "projects"
        elif any(keyword in section_lower for keyword in ["summary", "profile", "objective"]):
            return "summary"
        else:
            return "general"
    
    async def _create_knowledge_documents(self, user_profile) -> List[LCDocument]:
        """Create synthetic knowledge documents to enhance graph connectivity"""
        
        knowledge_docs = []
        
        # Industry knowledge document
        if user_profile and user_profile.preferences:
            industry = user_profile.preferences.get("preferred_industry", "Technology")
            
            industry_content = f"""
            Industry Focus: {industry}
            
            Key trends and requirements in {industry}:
            - Digital transformation initiatives
            - Cloud-native architectures
            - Agile development methodologies
            - Data-driven decision making
            - User experience optimization
            - Security and compliance standards
            
            Common roles in {industry}:
            - Software Engineer / Developer
            - DevOps Engineer
            - Data Scientist / Analyst
            - Product Manager
            - Technical Lead / Architect
            """
            
            knowledge_docs.append(LCDocument(
                page_content=industry_content,
                metadata={
                    "document_type": "industry_knowledge",
                    "industries": [industry],
                    "document_id": f"industry_{industry.lower().replace(' ', '_')}"
                }
            ))
        
        return knowledge_docs
    
    def _define_graph_edges(self) -> List[tuple]:
        """Define how documents connect to each other in the graph"""
        
        return [
            # Connect by skills
            ("skills", "skills"),
            # Connect by industries
            ("industries", "industries"),
            # Connect by job titles/roles
            ("job_titles", "job_titles"),
            # Connect by experience level
            ("experience_level", "experience_level"),
            # Connect by document type
            ("document_type", "document_type"),
            # Connect by technologies
            ("technologies", "technologies"),
            # Connect by section type
            ("section_type", "section_type")
        ]
    
    async def intelligent_search(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[LCDocument]:
        """Perform intelligent graph-based search with context awareness"""
        
        if not self.graph_retriever:
            logger.error("Graph retriever not initialized")
            return []
        
        try:
            # Enhance query with context
            enhanced_query = await self._enhance_search_query(query, context)
            
            # Perform graph traversal search
            results = self.graph_retriever.invoke(enhanced_query)
            
            # Track search for learning
            await self._track_search_behavior(query, enhanced_query, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            return []
    
    async def _enhance_search_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance search query with contextual information"""
        
        query_parts = [query]
        
        if context:
            # Add job-specific context
            if "job_title" in context:
                query_parts.append(f"role: {context['job_title']}")
            
            if "company" in context:
                query_parts.append(f"company: {context['company']}")
            
            if "required_skills" in context:
                skills_str = " ".join(context["required_skills"][:3])
                query_parts.append(f"skills: {skills_str}")
            
            if "industry" in context:
                query_parts.append(f"industry: {context['industry']}")
        
        return " ".join(query_parts)
    
    async def _track_search_behavior(self, original_query: str, enhanced_query: str, results: List[LCDocument]):
        """Track search behavior for continuous learning"""
        
        try:
            user_result = await self.db.execute(select(User).where(User.id == self.user_id))
            user = user_result.scalar_one()
            
            memory_manager = AsyncSafeEnhancedMemoryManager(self.db, user)
            
            await memory_manager.save_user_behavior_safe(
                action_type="graph_rag_search",
                context={
                    "original_query": original_query,
                    "enhanced_query": enhanced_query,
                    "results_count": len(results),
                    "retrieved_doc_types": list(set([doc.metadata.get("document_type", "unknown") for doc in results])),
                    "timestamp": datetime.utcnow().isoformat()
                },
                success=len(results) > 0
            )
            
        except Exception as e:
            logger.warning(f"Failed to track search behavior: {e}")
    
    async def get_contextualized_information(self, job_description: str, form_questions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get contextualized information for job applications using Graph RAG"""
        
        try:
            # Extract key information from job description
            job_context = await self._analyze_job_description(job_description)
            
            # Search for relevant user information
            user_info_results = await self.intelligent_search(
                "professional experience skills achievements",
                context=job_context
            )
            
            # Get specific answers for form questions
            form_answers = []
            if form_questions:
                for question in form_questions:
                    answer_results = await self.intelligent_search(
                        question,
                        context=job_context
                    )
                    
                    # Generate contextualized answer
                    answer = await self._generate_contextualized_answer(
                        question, job_description, answer_results
                    )
                    
                    form_answers.append({
                        "question": question,
                        "answer": answer
                    })
            
            # Generate personalized cover letter content
            cover_letter_results = await self.intelligent_search(
                "professional summary achievements relevant experience",
                context=job_context
            )
            
            cover_letter = await self._generate_smart_cover_letter(
                job_description, job_context, cover_letter_results
            )
            
            # Generate optimized resume content
            resume_results = await self.intelligent_search(
                "work experience education skills projects",
                context=job_context
            )
            
            optimized_resume = await self._generate_optimized_resume(
                job_description, job_context, resume_results
            )
            
            return {
                "job_analysis": job_context,
                "form_answers": form_answers,
                "cover_letter": cover_letter,
                "optimized_resume": optimized_resume,
                "relevant_experience": [doc.page_content for doc in user_info_results[:3]],
                "confidence_score": self._calculate_confidence_score(job_context, user_info_results)
            }
            
        except Exception as e:
            logger.error(f"Error getting contextualized information: {e}")
            return {}
    
    async def _analyze_job_description(self, job_description: str) -> Dict[str, Any]:
        """Analyze job description to extract key requirements and context"""
        
        analysis_prompt = f"""
        Analyze this job description and extract key information as JSON:
        
        {{
            "job_title": "extracted job title",
            "company": "company name if mentioned",
            "required_skills": ["skill1", "skill2"],
            "preferred_skills": ["skill1", "skill2"],
            "industry": "industry/sector",
            "experience_level": "entry/mid/senior",
            "technologies": ["tech1", "tech2"],
            "key_responsibilities": ["resp1", "resp2"],
            "qualifications": ["qual1", "qual2"]
        }}
        
        Job Description:
        {job_description}
        
        Return only valid JSON:
        """
        
        try:
            result = await self.llm.ainvoke(analysis_prompt)
            return json.loads(result.content)
        except:
            # Fallback analysis
            return {
                "job_title": "Software Engineer",
                "required_skills": ["Programming", "Problem Solving"],
                "industry": "Technology",
                "experience_level": "mid"
            }
    
    async def _generate_contextualized_answer(self, question: str, job_description: str, relevant_docs: List[LCDocument]) -> str:
        """Generate a contextualized answer using Graph RAG results"""
        
        context = "\n".join([doc.page_content for doc in relevant_docs[:3]])
        
        answer_prompt = f"""
        Based on the following user information and job context, provide a concise, relevant answer to the application question.
        
        User Information:
        {context}
        
        Job Description:
        {job_description[:500]}...
        
        Question: {question}
        
        Provide a professional, specific answer that highlights relevant experience and skills:
        """
        
        try:
            result = await self.llm.ainvoke(answer_prompt)
            return result.content.strip()
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "Please refer to my resume for detailed information about my qualifications."
    
    async def _generate_smart_cover_letter(self, job_description: str, job_context: Dict, relevant_docs: List[LCDocument]) -> str:
        """Generate an intelligent cover letter using Graph RAG insights"""
        
        user_context = "\n".join([doc.page_content for doc in relevant_docs[:4]])
        
        cover_letter_prompt = f"""
        Create a compelling, personalized cover letter based on the user's background and this job opportunity.
        
        User Background:
        {user_context}
        
        Job Context:
        - Title: {job_context.get('job_title', 'Position')}
        - Company: {job_context.get('company', 'Company')}
        - Required Skills: {', '.join(job_context.get('required_skills', [])[:5])}
        - Industry: {job_context.get('industry', 'Technology')}
        
        Job Description:
        {job_description[:800]}...
        
        Write a professional cover letter that:
        1. Shows genuine interest in the specific role and company
        2. Highlights most relevant skills and experiences from the user's background
        3. Demonstrates understanding of the job requirements
        4. Uses specific examples and achievements where possible
        5. Maintains a professional, enthusiastic tone
        
        Cover Letter:
        """
        
        try:
            result = await self.llm.ainvoke(cover_letter_prompt)
            return result.content.strip()
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return "Thank you for considering my application. I am excited about this opportunity and believe my background would be a great fit for this role."
    
    async def _generate_optimized_resume(self, job_description: str, job_context: Dict, relevant_docs: List[LCDocument]) -> str:
        """Generate an optimized resume section using Graph RAG"""
        
        user_context = "\n".join([doc.page_content for doc in relevant_docs])
        
        resume_prompt = f"""
        Based on the user's background and this job opportunity, suggest optimizations for their resume.
        
        User Background:
        {user_context}
        
        Job Requirements:
        - Skills: {', '.join(job_context.get('required_skills', []))}
        - Experience Level: {job_context.get('experience_level', 'mid')}
        - Industry: {job_context.get('industry', 'Technology')}
        
        Provide specific recommendations for:
        1. Professional summary optimization
        2. Skills section adjustments
        3. Experience highlighting
        4. Key achievements to emphasize
        
        Optimization Suggestions:
        """
        
        try:
            result = await self.llm.ainvoke(resume_prompt)
            return result.content.strip()
        except Exception as e:
            logger.error(f"Error generating resume optimization: {e}")
            return "Consider highlighting relevant technical skills and quantifiable achievements that align with the job requirements."
    
    def _calculate_confidence_score(self, job_context: Dict, user_results: List[LCDocument]) -> float:
        """Calculate confidence score for job application success"""
        
        try:
            score = 0.0
            
            # Skill matching
            required_skills = [skill.lower() for skill in job_context.get('required_skills', [])]
            user_skills = []
            
            for doc in user_results:
                if 'skills' in doc.metadata:
                    user_skills.extend([skill.lower() for skill in doc.metadata['skills']])
            
            if required_skills:
                skill_matches = len(set(required_skills) & set(user_skills))
                score += (skill_matches / len(required_skills)) * 0.6
            
            # Experience level matching
            job_level = job_context.get('experience_level', 'mid')
            user_levels = [doc.metadata.get('experience_level', 'mid') for doc in user_results if 'experience_level' in doc.metadata]
            
            if user_levels and job_level in user_levels:
                score += 0.2
            
            # Document completeness
            doc_types = set([doc.metadata.get('document_type') for doc in user_results])
            if 'experience' in [doc.metadata.get('section_type') for doc in user_results]:
                score += 0.1
            if 'skills' in [doc.metadata.get('section_type') for doc in user_results]:
                score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5  # Default moderate confidence

    async def generate_personalized_advice(self, job_description: str, advice_type: str = "cv_improvement") -> str:
        """Generate deeply personalized advice that shows intimate knowledge of the user's background"""
        
        try:
            # Get comprehensive user context
            context = await self.get_job_application_context(job_description)
            job_analysis = context.get("job_analysis", {})
            
            # Get user's actual background
            user_background_search = await self.intelligent_search(
                "work experience projects achievements education background",
                context=job_analysis
            )
            
            # Get current skills from user documents  
            skills_search = await self.intelligent_search(
                "technical skills programming languages frameworks tools",
                context=job_analysis
            )
            
            # Extract user's actual background details
            user_details = self._extract_user_specifics(user_background_search, skills_search)
            
            if advice_type == "cv_improvement":
                return await self._generate_personalized_cv_advice(
                    user_details, job_analysis, job_description
                )
            elif advice_type == "interview_prep":
                return await self._generate_personalized_interview_advice(
                    user_details, job_analysis, job_description
                )
            else:
                return await self._generate_personalized_general_advice(
                    user_details, job_analysis, job_description
                )
                
        except Exception as e:
            logger.error(f"Personalized advice generation failed: {e}")
            return "I'd love to give you personalized advice, but I need to analyze your documents first. Please upload your resume or CV!"
    
    def _extract_user_specifics(self, background_docs: List[LCDocument], skills_docs: List[LCDocument]) -> Dict[str, Any]:
        """Extract specific details about the user from their documents"""
        
        user_specifics = {
            "companies": [],
            "roles": [],
            "technologies": [],
            "achievements": [],
            "projects": [],
            "experience_years": "mid",
            "education": [],
            "current_level": "mid"
        }
        
        # Analyze background documents
        for doc in background_docs:
            content = doc.page_content.lower()
            
            # Extract company names (common patterns)
            company_patterns = [
                r'at ([A-Z][a-zA-Z\s&]+)(?:\s|,|\.)',
                r'worked at ([A-Z][a-zA-Z\s&]+)',
                r'employed by ([A-Z][a-zA-Z\s&]+)'
            ]
            
            for pattern in company_patterns:
                matches = re.findall(pattern, doc.page_content, re.IGNORECASE)
                user_specifics["companies"].extend([m.strip() for m in matches[:3]])
            
            # Extract achievements (quantifiable results)
            achievement_patterns = [
                r'(improved|increased|reduced|built|developed|led|managed).*?(\d+%|\d+x|\$\d+)',
                r'(\d+%|\d+x|\$\d+).*?(improvement|increase|reduction|growth)',
            ]
            
            for pattern in achievement_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches[:2]:
                    if isinstance(match, tuple):
                        achievement = ' '.join(match).strip()
                        user_specifics["achievements"].append(achievement)
            
            # Extract specific technologies from metadata
            if 'skills' in doc.metadata:
                user_specifics["technologies"].extend(doc.metadata['skills'])
                
            if 'experience_level' in doc.metadata:
                user_specifics["experience_years"] = doc.metadata['experience_level']
        
        # Clean and deduplicate
        user_specifics["companies"] = list(set([c for c in user_specifics["companies"] if len(c) > 2]))[:3]
        user_specifics["technologies"] = list(set(user_specifics["technologies"]))[:10]
        user_specifics["achievements"] = list(set(user_specifics["achievements"]))[:5]
        
        return user_specifics
    
    async def _generate_personalized_cv_advice(self, user_details: Dict, job_analysis: Dict, job_description: str) -> str:
        """Generate CV advice that shows intimate knowledge of user's background"""
        
        user_name = "Professional"  # Could extract from user profile
        companies = user_details.get("companies", [])
        technologies = user_details.get("technologies", [])
        achievements = user_details.get("achievements", [])
        
        required_skills = job_analysis.get("required_skills", [])
        job_title = job_analysis.get("job_title", "target role")
        
        # Find skill overlaps and gaps
        user_skills_lower = [skill.lower() for skill in technologies]
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        matching_skills = [skill for skill in required_skills if skill.lower() in user_skills_lower]
        missing_skills = [skill for skill in required_skills if skill.lower() not in user_skills_lower]
        
        advice_prompt = f"""
        Create deeply personalized CV advice for someone with this SPECIFIC background:
        
        THEIR ACTUAL BACKGROUND:
        - Companies: {', '.join(companies) if companies else 'Various companies'}
        - Current Tech Stack: {', '.join(technologies[:8]) if technologies else 'General programming'}
        - Achievements: {'; '.join(achievements[:3]) if achievements else 'Various accomplishments'}
        
        TARGET ROLE: {job_title}
        Required Skills: {', '.join(required_skills)}
        
        MATCHING SKILLS (highlight these): {', '.join(matching_skills)}
        SKILL GAPS (suggest learning): {', '.join(missing_skills)}
        
        Write personalized advice that:
        1. Shows you KNOW their specific background and companies
        2. Connects their ACTUAL experience to the target role
        3. Provides specific next steps based on their current skills
        4. Mentions their real achievements and how to leverage them
        
        Make it feel like advice from someone who knows them personally, not a generic template.
        Start with acknowledging their specific background.
        """
        
        try:
            result = await self.llm.ainvoke(advice_prompt)
            return result.content.strip()
        except Exception as e:
            logger.error(f"CV advice generation failed: {e}")
            return f"Based on your background with {', '.join(companies[:2]) if companies else 'your experience'}, here are tailored recommendations for the {job_title} role..." 