"""
Simple client example for the Online Judge API
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def submit_and_wait(source_code: str, stdin_data: str = "", time_limit_sec: float = 2.0):
    """
    Submit code and wait for result
    """
    # Submit code
    print(f"📤 Submitting code...")
    response = requests.post(
        f"{BASE_URL}/execute",
        json={
            "source_code": source_code,
            "stdin_data": stdin_data,
            "time_limit_sec": time_limit_sec,
        }
    )
    
    if response.status_code != 202:
        print(f"❌ Error: {response.text}")
        return None
    
    submission_id = response.json()["submission_id"]
    print(f"✅ Submission ID: {submission_id}")
    print(f"⏳ Waiting for result...\n")
    
    # Poll for result
    max_attempts = 30
    for attempt in range(max_attempts):
        result_response = requests.get(f"{BASE_URL}/result/{submission_id}")
        
        if result_response.status_code != 200:
            print(f"❌ Error fetching result: {result_response.text}")
            return None
        
        result = result_response.json()
        
        if result["status"] not in ["PENDING", "PROCESSING"]:
            # Execution completed
            print("=" * 60)
            print(f"📊 RESULT")
            print("=" * 60)
            print(f"Status: {result['status']}")
            print(f"Execution Time: {result['time_sec']} seconds")
            print(f"Exit Code: {result['exit_code']}")
            
            if result['stdout']:
                print(f"\n📤 STDOUT:")
                print("-" * 60)
                print(result['stdout'])
            
            if result['stderr']:
                print(f"\n⚠️  STDERR:")
                print("-" * 60)
                print(result['stderr'])
            
            print("=" * 60)
            return result
        
        # Still processing
        print(f"  [{attempt+1}/{max_attempts}] Status: {result['status']}")
        time.sleep(0.5)
    
    print(f"⏰ Timeout waiting for result")
    return None


if __name__ == "__main__":
    print("🎯 Online Judge Client Example\n")
    
    # Example 1: Simple addition
    print("\n" + "=" * 60)
    print("Example 1: Sum of Array")
    print("=" * 60)
    code1 = """
n = int(input())
arr = list(map(int, input().split()))
print(f"Sum: {sum(arr)}")
print(f"Average: {sum(arr)/n}")
"""
    submit_and_wait(code1, "5\n1 2 3 4 5\n")
    
    # Example 2: Fibonacci
    print("\n" + "=" * 60)
    print("Example 2: Fibonacci")
    print("=" * 60)
    code2 = """
n = int(input())

def fib(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

print(f"Fibonacci({n}) = {fib(n)}")
"""
    submit_and_wait(code2, "10\n")
    
    # Example 3: Time Limit Exceeded
    print("\n" + "=" * 60)
    print("Example 3: Time Limit Exceeded (Infinite Loop)")
    print("=" * 60)
    code3 = """
while True:
    pass
"""
    submit_and_wait(code3, "", time_limit_sec=1.0)
    
    # Example 4: Runtime Error
    print("\n" + "=" * 60)
    print("Example 4: Runtime Error (Division by Zero)")
    print("=" * 60)
    code4 = """
x = 1 / 0
print(x)
"""
    submit_and_wait(code4, "")
