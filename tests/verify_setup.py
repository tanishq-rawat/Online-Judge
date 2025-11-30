#!/usr/bin/env python3
# filepath: /home/tanishq/Tanishq/OnlineJudge/verify_setup.py
"""
Verify that all dependencies and services are properly set up
"""
import sys
import subprocess
import importlib

def check_python_version():
    """Check Python version >= 3.8"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, got {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    required = [
        "fastapi", "uvicorn", "redis", "celery", 
        "pydantic", "docker"
    ]
    
    missing = []
    for package in required:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    return True

def check_redis():
    """Check if Redis is accessible"""
    try:
        result = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and "PONG" in result.stdout:
            print("✅ Redis is running")
            return True
        else:
            print("❌ Redis not responding")
            print("Run: docker-compose up -d")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Redis not accessible")
        print("Run: docker-compose up -d")
        return False

def check_docker():
    """Check if Docker is accessible"""
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            print("✅ Docker is running")
            return True
        else:
            print("❌ Docker not running")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker not installed or not accessible")
        return False

def check_docker_image():
    """Check if sandbox image exists"""
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "oj-python-runner"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.stdout.strip():
            print("✅ Docker image 'oj-python-runner' exists")
            return True
        else:
            print("❌ Docker image 'oj-python-runner' not found")
            print("Run: cd python-oj && docker build -t oj-python-runner .")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def main():
    print("=" * 60)
    print("🔍 Online Judge Setup Verification")
    print("=" * 60)
    print()
    
    print("📦 Checking Python...")
    python_ok = check_python_version()
    print()
    
    print("📦 Checking Python Dependencies...")
    deps_ok = check_dependencies()
    print()
    
    print("🔧 Checking Redis...")
    redis_ok = check_redis()
    print()
    
    print("🐳 Checking Docker...")
    docker_ok = check_docker()
    print()
    
    print("📦 Checking Docker Image...")
    image_ok = check_docker_image()
    print()
    
    print("=" * 60)
    if all([python_ok, deps_ok, redis_ok, docker_ok, image_ok]):
        print("✅ All checks passed! You're ready to go!")
        print()
        print("Start the system:")
        print("  Terminal 1: uvicorn main:app --reload")
        print("  Terminal 2: celery -A celery_app.celery_app worker --loglevel=info")
        print("  Terminal 3: python client_example.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
