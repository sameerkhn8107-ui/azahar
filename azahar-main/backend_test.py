import requests
import sys
import json
from datetime import datetime

class NexAIBackendTester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_health_endpoint(self):
        """Test the health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        success, response = self.run_test(
            "Root API",
            "GET",
            "api/",
            200
        )
        return success

    def test_chat_stream_endpoint(self):
        """Test the chat stream endpoint structure (not full streaming)"""
        test_data = {
            "messages": [
                {"role": "user", "content": "Hello, this is a test message"}
            ],
            "user_name": "test_user",
            "conversation_id": "test_conversation"
        }
        
        success, response = self.run_test(
            "Chat Stream Endpoint (Default Mode)",
            "POST",
            "api/chat/stream",
            200,
            data=test_data
        )
        
        if success and response:
            # Check if it's a streaming response
            content_type = response.headers.get('content-type', '')
            if 'text/event-stream' in content_type:
                print(f"   ✅ Correct streaming content type: {content_type}")
                return True
            else:
                print(f"   ❌ Expected streaming content type, got: {content_type}")
                return False
        
        return success

    def test_chat_stream_with_learn_mode(self):
        """Test the chat stream endpoint with learn mode"""
        test_data = {
            "messages": [
                {"role": "user", "content": "Explain photosynthesis"}
            ],
            "user_name": "test_user",
            "conversation_id": "test_conversation",
            "active_mode": "learn"
        }
        
        success, response = self.run_test(
            "Chat Stream with Learn Mode",
            "POST",
            "api/chat/stream",
            200,
            data=test_data
        )
        
        if success and response:
            content_type = response.headers.get('content-type', '')
            if 'text/event-stream' in content_type:
                print(f"   ✅ Learn mode accepted, streaming response received")
                return True
            else:
                print(f"   ❌ Expected streaming content type, got: {content_type}")
                return False
        
        return success

    def test_chat_stream_with_english_mode(self):
        """Test the chat stream endpoint with english mode"""
        test_data = {
            "messages": [
                {"role": "user", "content": "I am going to store yesterday"}
            ],
            "user_name": "test_user", 
            "conversation_id": "test_conversation",
            "active_mode": "english"
        }
        
        success, response = self.run_test(
            "Chat Stream with English Mode",
            "POST",
            "api/chat/stream",
            200,
            data=test_data
        )
        
        if success and response:
            content_type = response.headers.get('content-type', '')
            if 'text/event-stream' in content_type:
                print(f"   ✅ English mode accepted, streaming response received")
                return True
            else:
                print(f"   ❌ Expected streaming content type, got: {content_type}")
                return False
        
        return success

    def test_chat_stream_with_startup_mode(self):
        """Test the chat stream endpoint with startup mode"""
        test_data = {
            "messages": [
                {"role": "user", "content": "spin"}
            ],
            "user_name": "test_user",
            "conversation_id": "test_conversation",
            "active_mode": "startup"
        }
        
        success, response = self.run_test(
            "Chat Stream with Startup Mode",
            "POST",
            "api/chat/stream",
            200,
            data=test_data
        )
        
        if success and response:
            content_type = response.headers.get('content-type', '')
            if 'text/event-stream' in content_type:
                print(f"   ✅ Startup mode accepted, streaming response received")
                return True
            else:
                print(f"   ❌ Expected streaming content type, got: {content_type}")
                return False
        
        return success

    def test_memory_extract_endpoint(self):
        """Test the memory extract endpoint"""
        test_data = {
            "messages": [
                {"role": "user", "content": "My name is John and I love programming"},
                {"role": "assistant", "content": "Nice to meet you John! Programming is great."}
            ],
            "current_memory": {
                "preferred_name": None,
                "interests": [],
                "goals": []
            }
        }
        
        success, response = self.run_test(
            "Memory Extract Endpoint",
            "POST",
            "api/memory/extract",
            200,
            data=test_data
        )
        
        if success and response:
            try:
                response_data = response.json()
                if 'updated_memory' in response_data and 'extracted_facts' in response_data:
                    print(f"   ✅ Memory extraction response structure correct")
                    return True
                else:
                    print(f"   ❌ Missing expected fields in response")
                    return False
            except:
                print(f"   ❌ Invalid JSON response")
                return False
        
        return success

def main():
    print("🚀 Starting Nex.AI Backend API Tests")
    print("=" * 50)
    
    tester = NexAIBackendTester()
    
    # Run all tests
    tests = [
        tester.test_health_endpoint,
        tester.test_root_endpoint,
        tester.test_chat_stream_endpoint,
        tester.test_chat_stream_with_startup_mode,
        tester.test_memory_extract_endpoint,
        tester.test_chat_stream_with_learn_mode,
        tester.test_chat_stream_with_english_mode
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            tester.tests_run += 1

    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Backend API Test Results:")
    print(f"   Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"   Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend tests passed!")
        return 0
    else:
        print("⚠️  Some backend tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())