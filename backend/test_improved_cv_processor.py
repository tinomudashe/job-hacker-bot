#!/usr/bin/env python3
"""Test the improved CV processor with structured output"""

import asyncio
import json
from pathlib import Path
from app.cv_processor import CVProcessor

async def test_improved_cv_processing():
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
        print(f"Testing Improved CV Processor: {cv_file.name}")
        print('='*60)
        
        try:
            # Process the CV
            result = await processor.extract_cv_information(cv_file)
            
            # Convert to dict for JSON serialization
            result_dict = result.dict()
            
            # Print formatted JSON
            print("\n📋 Extracted Information (Structured Output):")
            print(json.dumps(result_dict, indent=2, ensure_ascii=False))
            
            # Validation checks
            print("\n✅ Validation Results:")
            print(f"  - Name extracted: {'✓' if result.personal_info.full_name else '✗'}")
            print(f"  - Email extracted: {'✓' if result.personal_info.email else '✗'}")
            print(f"  - Email valid: {'✓' if result.personal_info.email and '@' in result.personal_info.email else '✗'}")
            print(f"  - Phone extracted: {'✓' if result.personal_info.phone else '✗'}")
            print(f"  - Experience count: {len(result.experience)} (max 20 enforced)")
            print(f"  - Education count: {len(result.education)} (max 20 enforced)")
            print(f"  - Projects count: {len(result.projects)} (max 20 enforced)")
            print(f"  - Technical skills: {len(result.skills.technical_skills)}")
            print(f"  - Confidence score: {result.confidence_score:.2f}")
            
            # Check for potential hallucinations
            print("\n🔍 Hallucination Checks:")
            
            # Check if email has @ symbol
            if result.personal_info.email and '@' not in result.personal_info.email:
                print("  ⚠️  Invalid email format detected (no @ symbol)")
            
            # Check if LinkedIn URL is valid
            if result.personal_info.linkedin and 'linkedin.com' not in result.personal_info.linkedin.lower():
                print("  ⚠️  Invalid LinkedIn URL detected")
            
            # Check for suspiciously high number of entries
            if len(result.experience) > 15:
                print("  ⚠️  Unusually high number of experiences (>15)")
            
            if len(result.education) > 10:
                print("  ⚠️  Unusually high number of education entries (>10)")
            
            print("\n✅ Structured output validation complete!")
                
        except Exception as e:
            print(f"\n❌ Error processing {cv_file.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_improved_cv_processing())