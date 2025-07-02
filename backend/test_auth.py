#!/usr/bin/env python3
"""
Quick test script for authentication
"""
import asyncio
import httpx
import json
from datetime import datetime

API_URL = "http://localhost:8000/api/v1"

async def test_auth():
    async with httpx.AsyncClient() as client:
        print("🧪 Testing BMA Social Authentication\n")
        
        # 1. Register a new user
        print("1️⃣ Registering new user...")
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123",
            "full_name": "Test User"
        }
        
        try:
            response = await client.post(f"{API_URL}/auth/register", json=register_data)
            if response.status_code == 201:
                user = response.json()
                print(f"✅ User registered: {user['username']} ({user['email']})")
            else:
                print(f"❌ Registration failed: {response.text}")
        except Exception as e:
            print(f"❌ Registration error: {e}")
        
        # 2. Login
        print("\n2️⃣ Logging in...")
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = await client.post(
            f"{API_URL}/auth/login",
            data=login_data,  # OAuth2 uses form data
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            tokens = response.json()
            print(f"✅ Login successful!")
            print(f"   Access Token: {tokens['access_token'][:50]}...")
            access_token = tokens['access_token']
        else:
            print(f"❌ Login failed: {response.text}")
            return
        
        # 3. Get current user
        print("\n3️⃣ Getting current user info...")
        response = await client.get(
            f"{API_URL}/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Current user: {user['username']} - {user['role']}")
        else:
            print(f"❌ Failed to get user: {response.text}")
        
        # 4. Test protected endpoint
        print("\n4️⃣ Testing protected endpoint (users list)...")
        response = await client.get(
            f"{API_URL}/users/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            print(f"✅ Access granted to protected endpoint")
        else:
            print(f"❌ Access denied: {response.status_code}")
        
        print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_auth())