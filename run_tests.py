import subprocess
import sys

def run_tests():
    cmd = ["python", "-m", "pytest", "tests/", "-v"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(f"Return code: {result.returncode}")
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
