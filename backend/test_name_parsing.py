#!/usr/bin/env python3
"""Test script to verify name parsing logic"""

def test_name_parsing():
    """Test the name parsing logic"""
    
    test_names = [
        "John Smith",
        "Mary Jane Doe", 
        "Jean-Pierre Martin",
        "Robert James Wilson",
        "Ana Garcia Lopez",
        "Li Wei",
        "Muhammad Ali Khan"
    ]
    
    print("Testing name parsing logic:\n")
    
    for full_name in test_names:
        print(f"Full Name: {full_name}")
        
        # Test first name extraction
        # First name = first word/part (handling hyphens)
        parts = full_name.split()
        if '-' in parts[0]:
            first_name = parts[0]  # Keep hyphenated first names together
        else:
            first_name = parts[0]
        
        # Test last name extraction  
        # Last name = everything after the first name
        first_name_end = len(first_name)
        last_name = full_name[first_name_end:].strip()
        
        print(f"  First Name: {first_name}")
        print(f"  Last Name: {last_name}")
        print()
    
    # Test with the prompt logic
    print("\nExample prompt for 'John Smith':")
    print("---")
    context = "Full Name: John Smith"
    print(f"Context: {context}")
    print("\nFor First Name field:")
    print("Extract ONLY the FIRST name from 'Full Name: John Smith'")
    print("Expected: 'John' (NOT 'Smith')")
    print("\nFor Last Name field:")
    print("Extract ONLY the LAST name from 'Full Name: John Smith'")  
    print("Expected: 'Smith' (NOT 'John')")

if __name__ == "__main__":
    test_name_parsing()