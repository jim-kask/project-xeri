#!/usr/bin/env python3
"""
A script to set up the test environment for the xeri chat application.
This will install test dependencies and verify the setup is correct.
"""
import sys
import subprocess
import os

def main():
    """Install required test dependencies and verify setup."""
    print("Setting up test environment for xeri chat app...")
    
    # Install test dependencies
    requirements = [
        "pytest",
        "pytest-flask",
        "pytest-socket",
        "pytest-cov",
        "pytest-mock",
    ]
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + requirements)
        print("✅ Test dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install test dependencies")
        return False
    
    # Verify pytest is available
    try:
        subprocess.check_call([sys.executable, "-m", "pytest", "--version"])
        print("✅ Pytest is available")
    except subprocess.CalledProcessError:
        print("❌ Pytest is not available")
        return False
    
    print("\nTest environment setup completed successfully!")
    print("\nRun tests with: python -m pytest")
    print("Run tests with coverage: python -m pytest --cov=xeri")
    
    return True

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
