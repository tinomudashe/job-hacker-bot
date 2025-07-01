#!/usr/bin/env python3
"""
Security validation script to ensure all endpoints are properly protected.
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Set
import re

class EndpointSecurityValidator:
    """Validates that all API endpoints are properly protected with authentication."""
    
    def __init__(self, backend_path: str = "app"):
        self.backend_path = Path(backend_path)
        self.protected_patterns = {
            "get_current_active_user",
            "get_current_user", 
            "get_current_active_user_ws"
        }
        self.unprotected_allowed = {
            # Webhook endpoints that should NOT be protected
            "stripe-webhook",
            "webhook",
            # Health check endpoints
            "health",
            "",  # Root path
            # Public endpoints (if any)
        }
        
    def extract_router_endpoints(self, file_path: Path) -> List[Dict]:
        """Extract all router endpoints from a Python file."""
        endpoints = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # More flexible pattern to catch different router decorators
            patterns = [
                r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']*)["\'].*?\)\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\((.*?)\):',
                r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']*)["\'].*?\)\s*(?:\n.*?)*?\n\s*(?:async\s+)?def\s+(\w+)\s*\((.*?)\):'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                
                for match in matches:
                    method = match.group(1).upper()
                    path = match.group(2)
                    function_name = match.group(3)
                    
                    # Get the parameters - might be in different group depending on pattern
                    if len(match.groups()) >= 4:
                        parameters = match.group(4)
                    else:
                        parameters = ""
                    
                    # Check if endpoint uses authentication
                    is_protected = any(pattern in parameters for pattern in self.protected_patterns)
                    
                    # Also check the function body for authentication (some might be manual)
                    function_start = match.end()
                    function_body = content[function_start:function_start + 500]  # First 500 chars
                    if not is_protected:
                        is_protected = any(pattern in function_body for pattern in self.protected_patterns)
                    
                    endpoints.append({
                        'file': file_path.name,
                        'method': method,
                        'path': path,
                        'function': function_name,
                        'is_protected': is_protected,
                        'parameters': parameters.strip()
                    })
                    
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
        return endpoints
    
    def scan_all_endpoints(self) -> List[Dict]:
        """Scan all Python files in the backend for router endpoints."""
        all_endpoints = []
        
        print(f"Scanning directory: {self.backend_path.absolute()}")
        
        # Scan main app directory
        py_files = list(self.backend_path.glob("*.py"))
        print(f"Found {len(py_files)} Python files in main directory")
        
        for py_file in py_files:
            if py_file.name.startswith("__"):
                continue
            print(f"Processing {py_file.name}...")
            endpoints = self.extract_router_endpoints(py_file)
            if endpoints:
                print(f"  Found {len(endpoints)} endpoints")
            all_endpoints.extend(endpoints)
        
        # Scan routers subdirectory
        routers_path = self.backend_path / "routers"
        if routers_path.exists():
            router_files = list(routers_path.glob("*.py"))
            print(f"Found {len(router_files)} Python files in routers directory")
            
            for py_file in router_files:
                if py_file.name.startswith("__"):
                    continue
                print(f"Processing routers/{py_file.name}...")
                endpoints = self.extract_router_endpoints(py_file)
                if endpoints:
                    print(f"  Found {len(endpoints)} endpoints")
                all_endpoints.extend(endpoints)
        
        print(f"Total endpoints found: {len(all_endpoints)}")
        return all_endpoints
    
    def validate_security(self) -> Dict:
        """Validate the security of all endpoints."""
        endpoints = self.scan_all_endpoints()
        
        unprotected = []
        protected = []
        allowed_unprotected = []
        
        for endpoint in endpoints:
            full_path = endpoint['path']
            
            if endpoint['is_protected']:
                protected.append(endpoint)
            elif any(allowed in full_path for allowed in self.unprotected_allowed):
                allowed_unprotected.append(endpoint)
            else:
                unprotected.append(endpoint)
        
        return {
            'total_endpoints': len(endpoints),
            'protected': protected,
            'unprotected': unprotected,
            'allowed_unprotected': allowed_unprotected,
            'security_score': len(protected) / len(endpoints) * 100 if endpoints else 100
        }
    
    def generate_security_report(self) -> str:
        """Generate a comprehensive security report."""
        results = self.validate_security()
        
        report = [
            "🔒 ENDPOINT SECURITY VALIDATION REPORT",
            "=" * 50,
            f"Total Endpoints Scanned: {results['total_endpoints']}",
            f"Protected Endpoints: {len(results['protected'])}",
            f"Unprotected Endpoints: {len(results['unprotected'])}",
            f"Allowed Unprotected: {len(results['allowed_unprotected'])}",
            f"Security Score: {results['security_score']:.1f}%",
            "",
        ]
        
        if results['unprotected']:
            report.extend([
                "🚨 UNPROTECTED ENDPOINTS (SECURITY RISK):",
                "-" * 40
            ])
            for endpoint in results['unprotected']:
                report.append(f"❌ {endpoint['method']} {endpoint['path']} in {endpoint['file']} ({endpoint['function']})")
            report.append("")
        
        if results['allowed_unprotected']:
            report.extend([
                "✅ INTENTIONALLY UNPROTECTED ENDPOINTS:",
                "-" * 40
            ])
            for endpoint in results['allowed_unprotected']:
                report.append(f"ℹ️  {endpoint['method']} {endpoint['path']} in {endpoint['file']} ({endpoint['function']})")
            report.append("")
        
        if results['protected']:
            report.extend([
                "✅ PROTECTED ENDPOINTS:",
                "-" * 20
            ])
            for endpoint in results['protected']:
                report.append(f"🔒 {endpoint['method']} {endpoint['path']} in {endpoint['file']}")
        
        return "\n".join(report)

def main():
    """Run the security validation."""
    validator = EndpointSecurityValidator()
    report = validator.generate_security_report()
    print(report)
    
    # Check if there are any unprotected endpoints
    results = validator.validate_security()
    if results['unprotected']:
        print("\n🚨 WARNING: Unprotected endpoints found! Please review and secure them.")
        return False
    else:
        print("\n✅ All endpoints are properly secured!")
        return True

if __name__ == "__main__":
    main() 