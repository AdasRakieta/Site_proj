#!/usr/bin/env python3
"""
Environment Configuration Validator
====================================
This script validates your .env configuration and checks for common issues.
Run this before deploying to catch configuration problems early.

Usage:
    python validate_env.py [--file .env]
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(message: str, color: str):
    """Print colored message to terminal."""
    print(f"{color}{message}{Colors.END}")

def load_env_file(filepath: Path) -> Dict[str, str]:
    """Load environment variables from file."""
    env_vars = {}
    if not filepath.exists():
        return env_vars
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars

def check_required_variables(env_vars: Dict[str, str]) -> List[Tuple[str, str]]:
    """Check for required environment variables."""
    required = {
        'DB_HOST': 'Database host address',
        'DB_NAME': 'Database name',
        'DB_USER': 'Database user',
        'DB_PASSWORD': 'Database password',
        'SECRET_KEY': 'Flask secret key (min 32 chars)',
        'SMTP_SERVER': 'SMTP server address',
        'SMTP_USERNAME': 'Email username',
        'SMTP_PASSWORD': 'Email password',
        'ADMIN_EMAIL': 'Admin email address',
    }
    
    issues = []
    for var, description in required.items():
        if var not in env_vars or not env_vars[var]:
            issues.append((var, f"Missing or empty: {description}"))
        elif env_vars[var] in ['change_this', 'your_', 'example', 'localhost'] and var != 'DB_HOST':
            issues.append((var, f"Still has placeholder value: {description}"))
    
    return issues

def check_security_issues(env_vars: Dict[str, str]) -> List[Tuple[str, str]]:
    """Check for common security issues."""
    issues = []
    
    # Check SECRET_KEY strength
    if 'SECRET_KEY' in env_vars:
        secret_key = env_vars['SECRET_KEY']
        if len(secret_key) < 32:
            issues.append(('SECRET_KEY', f'Too short ({len(secret_key)} chars). Minimum 32 recommended.'))
        if secret_key in ['change_this_to_random_secret_key', 'secret', 'key']:
            issues.append(('SECRET_KEY', 'Using default/weak secret key. Generate a random one!'))
    
    # Check DB_PASSWORD strength
    if 'DB_PASSWORD' in env_vars:
        password = env_vars['DB_PASSWORD']
        if len(password) < 12:
            issues.append(('DB_PASSWORD', f'Weak password ({len(password)} chars). Use 12+ characters.'))
        if password.lower() in ['password', 'admin', '123456', 'change_this']:
            issues.append(('DB_PASSWORD', 'Using common/default password. Change immediately!'))
    
    # Check FLASK_ENV for production
    if env_vars.get('FLASK_ENV') == 'development':
        issues.append(('FLASK_ENV', 'Set to "development". Use "production" for deployment!'))
    
    # Check SECURE_COOKIES for production
    if env_vars.get('FLASK_ENV') == 'production':
        if env_vars.get('SECURE_COOKIES', '').lower() != 'true':
            issues.append(('SECURE_COOKIES', 'Should be "true" in production for security'))
    
    return issues

def check_optional_recommendations(env_vars: Dict[str, str]) -> List[Tuple[str, str]]:
    """Check optional but recommended settings."""
    recommendations = []
    
    # Redis configuration
    if 'REDIS_HOST' not in env_vars and 'REDIS_URL' not in env_vars:
        recommendations.append(('REDIS_HOST', 'Consider using Redis for production caching'))
    
    # Port configuration
    if 'SERVER_PORT' in env_vars:
        try:
            port = int(env_vars['SERVER_PORT'])
            if port < 1024 and port != 80 and port != 443:
                recommendations.append(('SERVER_PORT', f'Port {port} requires root privileges'))
        except ValueError:
            recommendations.append(('SERVER_PORT', 'Invalid port number'))
    
    # Database port
    if 'DB_PORT' in env_vars:
        try:
            port = int(env_vars['DB_PORT'])
            if port != 5432:
                recommendations.append(('DB_PORT', f'Non-standard PostgreSQL port: {port}'))
        except ValueError:
            recommendations.append(('DB_PORT', 'Invalid port number'))
    
    return recommendations

def validate_env_file(filepath: Path) -> bool:
    """Validate environment file and return True if valid."""
    print_colored(f"\n{'='*60}", Colors.BLUE)
    print_colored(f"🔍 Validating: {filepath}", Colors.BOLD)
    print_colored(f"{'='*60}\n", Colors.BLUE)
    
    # Load environment variables
    env_vars = load_env_file(filepath)
    
    if not env_vars:
        print_colored(f"❌ ERROR: File not found or empty: {filepath}", Colors.RED)
        return False
    
    print_colored(f"✓ Loaded {len(env_vars)} environment variables\n", Colors.GREEN)
    
    # Run checks
    has_errors = False
    has_warnings = False
    
    # 1. Required variables
    print_colored("📋 Checking required variables...", Colors.BOLD)
    required_issues = check_required_variables(env_vars)
    if required_issues:
        has_errors = True
        for var, issue in required_issues:
            print_colored(f"  ❌ {var}: {issue}", Colors.RED)
    else:
        print_colored("  ✓ All required variables present", Colors.GREEN)
    print()
    
    # 2. Security issues
    print_colored("🔐 Checking security configuration...", Colors.BOLD)
    security_issues = check_security_issues(env_vars)
    if security_issues:
        has_warnings = True
        for var, issue in security_issues:
            print_colored(f"  ⚠️  {var}: {issue}", Colors.YELLOW)
    else:
        print_colored("  ✓ No security issues detected", Colors.GREEN)
    print()
    
    # 3. Recommendations
    print_colored("💡 Recommendations...", Colors.BOLD)
    recommendations = check_optional_recommendations(env_vars)
    if recommendations:
        for var, recommendation in recommendations:
            print_colored(f"  ℹ️  {var}: {recommendation}", Colors.BLUE)
    else:
        print_colored("  ✓ Configuration looks optimal", Colors.GREEN)
    print()
    
    # Summary
    print_colored(f"{'='*60}", Colors.BLUE)
    if has_errors:
        print_colored("❌ VALIDATION FAILED - Fix errors before deploying!", Colors.RED)
        return False
    elif has_warnings:
        print_colored("⚠️  VALIDATION PASSED WITH WARNINGS - Review security issues", Colors.YELLOW)
        return True
    else:
        print_colored("✅ VALIDATION PASSED - Configuration looks good!", Colors.GREEN)
        return True

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate SmartHome environment configuration')
    parser.add_argument('--file', default='.env', help='Path to .env file (default: .env)')
    args = parser.parse_args()
    
    filepath = Path(args.file)
    success = validate_env_file(filepath)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
