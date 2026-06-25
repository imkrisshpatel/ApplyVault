import os
from dotenv import load_dotenv
from anthropic import Anthropic

# 1. Load the environment file
load_dotenv()

# 2. Initialize the client safely
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

print("📡 Sending test request to current flagship model...")

try:
    # 3. Requesting the standard active 2026 model ID
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say hello"}]
    )
    print(f"\n🎉 Success! Response: {response.content[0].text}")
except Exception as e:
    print(f"\n❌ Error encountered: {e}")