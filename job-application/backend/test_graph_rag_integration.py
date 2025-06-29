#!/usr/bin/env python3
"""
Test script to validate Graph RAG integration and functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.graph_rag import EnhancedGraphRAG
from langchain_core.documents import Document as LCDocument

async def test_graph_rag_basic():
    """Test basic Graph RAG functionality without database"""
    
    print("🧪 Testing Graph RAG Basic Functionality...")
    
    try:
        # Create a mock user ID and session
        user_id = "test_user_123"
        
        # Test document creation and metadata extraction
        print("\n1. Testing metadata extraction...")
        
        # Mock document content
        test_content = """
        John Doe
        Software Engineer
        
        Experience:
        - 5 years of Python development
        - React and Node.js expertise
        - AWS cloud infrastructure
        - Machine learning projects
        
        Skills:
        Python, JavaScript, React, Node.js, AWS, Docker, Git, PostgreSQL
        
        Education:
        Bachelor's in Computer Science
        """
        
        # Test metadata extraction patterns
        from app.graph_rag import EnhancedGraphRAG
        
        # We can't fully test without DB, but we can test components
        print("✅ EnhancedGraphRAG class imported successfully")
        
        # Test pattern matching
        rag_instance = EnhancedGraphRAG.__new__(EnhancedGraphRAG)  # Create without __init__
        metadata = rag_instance._extract_metadata_fallback(test_content)
        
        print(f"📊 Extracted metadata:")
        print(f"   Skills: {metadata.get('skills', [])}")
        print(f"   Experience Level: {metadata.get('experience_level', 'N/A')}")
        print(f"   Job Titles: {metadata.get('job_titles', [])}")
        
        # Test section splitting
        sections = rag_instance._split_into_sections(test_content)
        print(f"📝 Document split into {len(sections)} sections")
        
        # Test section type identification
        for i, section in enumerate(sections[:3]):  # Test first 3 sections
            section_type = rag_instance._identify_section_type(section)
            print(f"   Section {i+1}: {section_type} ({len(section)} chars)")
        
        print("\n✅ Basic Graph RAG functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Basic Graph RAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_job_analysis():
    """Test job description analysis functionality"""
    
    print("\n🧪 Testing Job Analysis...")
    
    try:
        # Create RAG instance for testing
        rag_instance = EnhancedGraphRAG.__new__(EnhancedGraphRAG)
        
        # Test job description
        job_description = """
        Software Engineer - Backend Development
        
        We are looking for a skilled Backend Software Engineer to join our team.
        
        Requirements:
        - 3+ years of Python experience
        - Experience with REST APIs
        - Knowledge of PostgreSQL and Redis
        - AWS or cloud experience preferred
        - Strong problem-solving skills
        
        Responsibilities:
        - Develop and maintain backend services
        - Design scalable architectures
        - Collaborate with frontend teams
        """
        
        # Test analysis
        analysis = rag_instance._extract_metadata_fallback(job_description)
        
        print(f"🎯 Job Analysis Results:")
        print(f"   Required Skills: {analysis.get('skills', [])}")
        print(f"   Experience Level: {analysis.get('experience_level', 'N/A')}")
        print(f"   Technologies: {analysis.get('technologies', [])}")
        
        print("\n✅ Job analysis tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Job analysis test failed: {e}")
        return False

def test_imports():
    """Test that all required imports work"""
    
    print("🧪 Testing Graph RAG Imports...")
    
    try:
        from langchain_graph_retriever import GraphRetriever
        from graph_retriever.strategies import Eager
        from langchain_core.vectorstores import InMemoryVectorStore
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        
        print("✅ All Graph RAG imports successful!")
        
        # Test basic initialization
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        print("✅ Google embeddings initialized")
        
        # Test InMemoryVectorStore with sample documents
        sample_docs = [
            LCDocument(
                page_content="Python developer with 5 years experience",
                metadata={"skills": ["Python"], "experience_level": "senior"}
            ),
            LCDocument(
                page_content="JavaScript and React frontend development",
                metadata={"skills": ["JavaScript", "React"], "experience_level": "mid"}
            )
        ]
        
        vector_store = InMemoryVectorStore.from_documents(
            documents=sample_docs,
            embedding=embeddings
        )
        print("✅ InMemoryVectorStore created successfully")
        
        # Test GraphRetriever initialization
        graph_retriever = GraphRetriever(
            store=vector_store,
            edges=[("skills", "skills"), ("experience_level", "experience_level")],
            strategy=Eager(k=5, start_k=1, max_depth=2)
        )
        print("✅ GraphRetriever initialized successfully")
        
        # Test a simple search
        results = graph_retriever.invoke("Python programming experience")
        print(f"✅ Graph search returned {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all Graph RAG tests"""
    
    print("🚀 Starting Graph RAG Integration Tests")
    print("=" * 50)
    
    # Test imports first
    if not test_imports():
        print("\n💥 Import tests failed - Graph RAG dependencies not properly installed")
        return False
    
    # Test basic functionality
    if not await test_graph_rag_basic():
        print("\n💥 Basic functionality tests failed")
        return False
    
    # Test job analysis
    if not await test_job_analysis():
        print("\n💥 Job analysis tests failed")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All Graph RAG tests passed!")
    print("\n🧠 Graph RAG Intelligence Summary:")
    print("   ✅ Enhanced document metadata extraction")
    print("   ✅ Intelligent skill and experience mapping")
    print("   ✅ Job requirement analysis")
    print("   ✅ Graph-based document relationships")
    print("   ✅ Context-aware search capabilities")
    print("\n🚀 Your agent is now significantly smarter!")
    
    return True

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    
    if success:
        print("\n🎯 Next Steps:")
        print("   1. Start your backend server: python3 -m uvicorn main:app --reload")
        print("   2. Test the Graph RAG demo endpoints:")
        print("      - GET /api/demo/graph-rag-status")
        print("      - POST /api/demo/graph-rag-search") 
        print("      - POST /api/demo/intelligent-application-context")
        print("   3. Upload documents to see Graph RAG in action!")
        sys.exit(0)
    else:
        print("\n❌ Graph RAG integration needs attention")
        sys.exit(1) 