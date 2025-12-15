"""
OpenAI API Provider
Handles all OpenAI-specific logic
"""
from typing import List, Dict
from openai import OpenAI


def get_openai_client(api_key: str) -> OpenAI:
    """Get OpenAI client instance"""
    if api_key:
        return OpenAI(api_key=api_key)
    return None


def call_openai_api(api_key: str, messages: List[Dict], user_query: str) -> str:
    """Call OpenAI API with gpt-3.5-turbo model"""
    try:
        client = get_openai_client(api_key)
        if not client:
            return "⚠️ OpenAI API is not configured. Please add your OpenAI API key to config.json or environment variables."
        
        print(f"\n🤖 USING OPENAI")
        print(f"   Calling OpenAI API with gpt-3.5-turbo...")
        print(f"   API Key Preview: {api_key[:20]}...{api_key[-4:]}")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1200,
            top_p=0.9
        )
        
        ai_response = response.choices[0].message.content
        print(f"✨ Response Generated Successfully from OpenAI")
        print(f"   Tokens Used: {response.usage.total_tokens}")
        return ai_response
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ OpenAI API Error: {error_msg}")
        
        if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
            print(f"⚠️ OpenAI quota exceeded. Check your billing at https://platform.openai.com/account/billing/overview")
            return "⚠️ OpenAI quota has been exceeded. Please check your billing details or switch to Groq."
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            print(f"⚠️ OpenAI authentication failed. Check your API key...")
            return "❌ OpenAI authentication failed. Please verify your API key."
        
        print(f"Error details: {error_msg}")
        return "⚠️ OpenAI API is currently unavailable. Please try again later."
