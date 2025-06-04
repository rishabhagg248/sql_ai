# debug_google_genai.py
import sys
import subprocess

def check_installation():
    print("=== Debugging langchain-google-genai installation ===\n")
    
    # 1. Check Python version
    print(f"Python version: {sys.version}")
    
    # 2. Check what's installed
    print("\n=== Installed packages ===")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                              capture_output=True, text=True)
        installed_packages = result.stdout
        
        # Filter for relevant packages
        for line in installed_packages.split('\n'):
            if any(keyword in line.lower() for keyword in ['langchain', 'google', 'genai']):
                print(line)
    except Exception as e:
        print(f"Error checking packages: {e}")
    
    # 3. Try different import approaches
    print("\n=== Testing imports ===")
    
    # Test 1: Basic import
    try:
        import langchain_google_genai
        print("✅ langchain_google_genai module imported successfully")
        print(f"   Module file: {langchain_google_genai.__file__}")
        print(f"   Module version: {getattr(langchain_google_genai, '__version__', 'Unknown')}")
    except ImportError as e:
        print(f"❌ Failed to import langchain_google_genai: {e}")
        return False
    
    # Test 2: Check what's available in the module
    try:
        print(f"   Available in module: {dir(langchain_google_genai)}")
    except Exception as e:
        print(f"   Error checking module contents: {e}")
    
    # Test 3: Try importing ChatGoogleGenerativeAI
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✅ ChatGoogleGenerativeAI imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ChatGoogleGenerativeAI: {e}")
        
        # Try alternative approaches
        try:
            from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
            print("✅ ChatGoogleGenerativeAI imported via chat_models")
        except ImportError as e2:
            print(f"❌ Alternative import also failed: {e2}")
            return False
    
    # Test 4: Check Google AI package
    try:
        import google.generativeai as genai
        print("✅ google.generativeai imported successfully")
    except ImportError as e:
        print(f"❌ google.generativeai not available: {e}")
        print("   Try: pip install google-generativeai")
    
    # Test 5: Try creating an instance (without API key)
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key="test")
        print("✅ ChatGoogleGenerativeAI instance created successfully")
    except Exception as e:
        print(f"⚠️ Instance creation failed (expected without valid API key): {e}")
    
    return True

def fix_installation():
    print("\n=== Attempting to fix installation ===")
    
    commands = [
        # Uninstall potentially conflicting packages
        [sys.executable, "-m", "pip", "uninstall", "-y", "langchain-google-genai"],
        # Install core dependency
        [sys.executable, "-m", "pip", "install", "google-generativeai"],
        # Install langchain-google-genai
        [sys.executable, "-m", "pip", "install", "langchain-google-genai"],
        # Upgrade to latest
        [sys.executable, "-m", "pip", "install", "--upgrade", "langchain-google-genai"]
    ]
    
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Success")
            else:
                print(f"❌ Failed: {result.stderr}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    if not check_installation():
        print("\n=== Installation issues detected ===")
        fix_installation()
        print("\n=== Re-testing after fix ===")
        check_installation()
    else:
        print("\n✅ All imports working correctly!")