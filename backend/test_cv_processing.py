#!/usr/bin/env python3
"""Test CV processing with test CV files"""

import asyncio
import json
from pathlib import Path
from app.cv_processor import CVProcessor

async def test_cv_processing():
    processor = CVProcessor()
    
    # Test CV files
    test_files = [
        Path("testCv/Hapson_Marecha CV.pdf"),
        Path("testCv/Tinomudashe_cv (5).pdf")
    ]
    
    for cv_file in test_files:
        if not cv_file.exists():
            print(f"❌ File not found: {cv_file}")
            continue
            
        print(f"\n{'='*60}")
        print(f"Testing: {cv_file.name}")
        print('='*60)
        
        try:
            # Process the CV
            result = await processor.extract_cv_information(cv_file)
            
            # Convert to dict for JSON serialization
            result_dict = {
                "personal_info": result.personal_info.dict(),
                "experience": [exp.dict() for exp in result.experience],
                "education": [edu.dict() for edu in result.education],
                "projects": [proj.dict() for proj in result.projects],
                "skills": result.skills.dict(),
                "confidence_score": result.confidence_score,
                "raw_text_length": len(result.raw_text)
            }
            
            # Print formatted JSON
            print("\n📋 Extracted Information:")
            print(json.dumps(result_dict, indent=2, ensure_ascii=False))
            
            # Validate key fields
            print("\n✅ Validation Results:")
            print(f"  - Name extracted: {'✓' if result.personal_info.full_name else '✗'}")
            print(f"  - Email extracted: {'✓' if result.personal_info.email else '✗'}")
            print(f"  - Phone extracted: {'✓' if result.personal_info.phone else '✗'}")
            print(f"  - Experience count: {len(result.experience)}")
            print(f"  - Education count: {len(result.education)}")
            print(f"  - Projects count: {len(result.projects)}")
            print(f"  - Technical skills: {len(result.skills.technical_skills)}")
            print(f"  - Confidence score: {result.confidence_score:.2f}")
            
            # Check for data completeness
            if result.confidence_score < 0.5:
                print("\n⚠️  Warning: Low confidence score - extraction may have failed")
            
            if not result.personal_info.full_name and not result.personal_info.email:
                print("\n⚠️  Warning: Critical personal info missing")
                
        except Exception as e:
            print(f"\n❌ Error processing {cv_file.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cv_processing())