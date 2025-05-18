import httpx
import json
import os
import sys
import subprocess

def run_pytest_with_output():
    """Run pytest with output captured to a file."""
    output_file = "test_output.log"
    
    cmd = ["python", "-m", "pytest", "tests/test_functional.py::test_credit_card_management", "-v"]
    
    try:
        with open(output_file, "w") as f:
            result = subprocess.run(cmd, stdout=f, stderr=f, text=True)
        
        with open(output_file, "r") as f:
            content = f.read()
            
        # Print the content to terminal
        print(content)
        
        # Return true if tests passed (returncode 0)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_pytest_with_output()
    print(f"Test execution {'succeeded' if success else 'failed'}")
    if not success:
        sys.exit(1)
