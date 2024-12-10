import anthropic
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize client with API key
client = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {
            "role": "user", 
            "content": "Analyze this financial statement and provide key metrics and insights. Format your response as JSON."
        }
    ]
)
print(message.content)
