#!/usr/bin/env python3
"""Test the CV upload with different file encodings"""

import sys
from pathlib import Path

# Test reading a file with different encodings
test_files = [
    Path("testCv/Hapson_Marecha CV.pdf"),
    Path("testCv/Tinomudashe_cv (5).pdf"),
]

for file_path in test_files:
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        continue
    
    print(f"\n{'='*60}")
    print(f"Testing: {file_path.name}")
    print('='*60)
    
    # Test PDF reading
    if file_path.suffix.lower() == '.pdf':
        try:
            from pypdf import PdfReader
            pdf = PdfReader(str(file_path))
            text = "".join(page.extract_text() or "" for page in pdf.pages)
            print(f"✅ PDF read successfully, extracted {len(text)} characters")
            # Check for problematic characters
            if any(ord(char) > 127 for char in text[:100]):
                print("⚠️  Contains non-ASCII characters (this is normal for PDFs)")
        except Exception as e:
            print(f"❌ Error reading PDF: {e}")
    
    # Test DOCX reading
    elif file_path.suffix.lower() in ['.docx', '.doc']:
        try:
            import docx
            doc = docx.Document(str(file_path))
            text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
            print(f"✅ Word document read successfully, extracted {len(text)} characters")
        except Exception as e:
            print(f"❌ Error reading Word document: {e}")
    
    # Test text file with different encodings
    else:
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        success = False
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    text = f.read()
                print(f"✅ Text file read successfully with {encoding} encoding, {len(text)} characters")
                success = True
                break
            except UnicodeDecodeError:
                continue
        if not success:
            print(f"❌ Unable to read text file with any common encoding")

print("\n✅ Encoding test complete!")