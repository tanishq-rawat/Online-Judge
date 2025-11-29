import requests
import time

BASE_URL = "http://localhost:8000"

def test_code_execution():
    """Test the async code execution workflow"""
    
    # Test 1: Successful execution
    print("=== Test 1: Successful Execution ===")
    response = requests.post(
        f"{BASE_URL}/execute",
        json={
            "source_code": "n = int(input())\nprint(n * 2)",
            "stdin_data": "5\n",
            "time_limit_sec": 2.0,
        }
    )
    
    assert response.status_code == 202
    submission_id = response.json()["submission_id"]
    print(f"Submission ID: {submission_id}")
    
    # Poll for result
    max_attempts = 20
    for i in range(max_attempts):
        result = requests.get(f"{BASE_URL}/result/{submission_id}").json()
        print(f"  Attempt {i+1}: Status = {result['status']}")
        
        if result["status"] not in ["PENDING", "PROCESSING"]:
            print(f"  Final Result: {result}")
            assert result["status"] == "OK"
            assert "10" in result["stdout"]
            break
        
        time.sleep(0.5)
    
    # Test 2: Time Limit Exceeded
    print("\n=== Test 2: Time Limit Exceeded ===")
    response = requests.post(
        f"{BASE_URL}/execute",
        json={
            "source_code": "while True:\n    pass",
            "stdin_data": "",
            "time_limit_sec": 1.0,
        }
    )
    
    submission_id = response.json()["submission_id"]
    print(f"Submission ID: {submission_id}")
    
    for i in range(max_attempts):
        result = requests.get(f"{BASE_URL}/result/{submission_id}").json()
        print(f"  Attempt {i+1}: Status = {result['status']}")
        
        if result["status"] not in ["PENDING", "PROCESSING"]:
            print(f"  Final Result: {result}")
            assert result["status"] == "TLE"
            break
        
        time.sleep(0.5)
    
    # Test 3: Runtime Error
    print("\n=== Test 3: Runtime Error ===")
    response = requests.post(
        f"{BASE_URL}/execute",
        json={
            "source_code": "x = 1 / 0",
            "stdin_data": "",
        }
    )
    
    submission_id = response.json()["submission_id"]
    print(f"Submission ID: {submission_id}")
    
    for i in range(max_attempts):
        result = requests.get(f"{BASE_URL}/result/{submission_id}").json()
        print(f"  Attempt {i+1}: Status = {result['status']}")
        
        if result["status"] not in ["PENDING", "PROCESSING"]:
            print(f"  Final Result: {result}")
            assert result["status"] == "RE"
            break
        
        time.sleep(0.5)
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_code_execution()
