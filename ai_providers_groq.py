"""
Groq API Provider
Handles all Groq-specific logic (via groq.com)
"""
from typing import List, Dict
import requests


def call_groq_api(api_key: str, messages: List[Dict], system_prompt: str, user_query: str) -> str:
    """Call Groq API via groq.com with llama-3.3-70b-versatile model"""
    try:
        if not api_key:
            print("❌ Groq API key not configured!")
            return "⚠️ Groq API is not configured. Please add your Groq API key to config.json or environment variables."
        
        print(f"\n🦅 USING GROQ")
        print(f"   Calling Groq API via groq.com...")
        print(f"   API Key Preview: {api_key[:20]}...{api_key[-4:]}")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1200
        }
        
        # Groq API endpoint
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data['choices'][0]['message']['content']
            print(f"✨ Response Generated Successfully from Groq")
            print(f"   Model: llama-3.3-70b-versatile")
            return ai_response
        else:
            error_detail = response.text
            print(f"❌ Groq API Error: {response.status_code}")
            print(f"   Details: {error_detail}")
            
            # Return graceful fallback
            return "⚠️ Groq API temporarily unavailable. Please check your API key and try again."
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Groq API Error: {error_msg}")
        
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            print(f"⚠️ Groq authentication failed. Check your API key...")
            return "❌ Groq authentication failed. Please verify your API key."
        elif "429" in error_msg or "rate" in error_msg.lower():
            print(f"⚠️ Groq rate limit exceeded...")
            return "⚠️ Groq rate limit exceeded. Please try again later."
        
        print(f"Error details: {error_msg}")
        return "⚠️ Groq API is currently unavailable. Please try again later."
