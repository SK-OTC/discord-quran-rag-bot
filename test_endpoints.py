#!/usr/bin/env python3
"""
Test script for FastAPI backend endpoints
"""
import asyncio
import aiohttp

async def test_endpoints():
    """Test the FastAPI endpoints"""
    base_url = "http://127.0.0.1:8000"

    print("🧪 Testing FastAPI Endpoints")
    print("=" * 50)
    async with aiohttp.ClientSession() as session:
        # Test /health endpoint
        print("0. Testing /health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print("✅ /health endpoint working")
                    print(f"   Status: {health_data.get('status')}")
                else:
                    print(f"❌ /health failed with status {response.status}")
        except Exception as e:
            print(f"❌ /health error: {e}")

        # Test /metrics endpoint
        print("1. Testing /metrics endpoint...")
        try:
            async with session.get(f"{base_url}/metrics") as response:
                if response.status == 200:
                    metrics_text = await response.text()
                    print("✅ /metrics endpoint working")
                    print(f"   Response length: {len(metrics_text)} characters")
                    # Check for our custom metrics
                    if 'discord_commands_total' in metrics_text:
                        print("   ✅ Custom Discord metrics found")
                    else:
                        print("   ⚠️  Custom Discord metrics not found (may not have been triggered yet)")
                else:
                    print(f"❌ /metrics failed with status {response.status}")
        except Exception as e:
            print(f"❌ /metrics error: {e}")

        # Test /feedback endpoint
        print("\n2. Testing /feedback endpoint...")
        feedback_data = {
            "user_id": "test_user_123",
            "username": "testuser",
            "rating": 5,
            "comments": "Great bot!"
        }
        try:
            async with session.post(f"{base_url}/feedback", json=feedback_data) as response:
                result = await response.json()
                if response.status == 200:
                    print("✅ /feedback endpoint working")
                    print(f"   Response: {result}")
                else:
                    print(f"❌ /feedback failed with status {response.status}")
                    print(f"   Error: {result}")
        except Exception as e:
            print(f"❌ /feedback error: {e}")

        # Test /ask endpoint (this might fail without proper setup)
        print("\n3. Testing /ask endpoint...")
        ask_data = {
            "user_id": 12345,
            "question": "What is the meaning of life?"
        }
        try:
            async with session.post(f"{base_url}/ask", json=ask_data) as response:
                result = await response.json()
                if response.status == 200:
                    print("✅ /ask endpoint working")
                    print(f"   Response: {result}")
                else:
                    print(f"⚠️  /ask returned status {response.status}")
                    print(f"   Response: {result}")
        except Exception as e:
            print(f"❌ /ask error: {e}")

    print("\n" + "=" * 50)
    print("✅ Endpoint testing completed!")

if __name__ == "__main__":
    # Run tests (assuming server is already running)
    asyncio.run(test_endpoints())