import requests
import os
from dotenv import load_dotenv

load_dotenv()
XI_API_KEY = os.getenv('XI_API_KEY')

headers = {
  "Accept": "application/json",
  "xi-api-key": XI_API_KEY,
  "Content-Type": "application/json"
}

response = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers)

data = response.json()

for voice in data['voices']:
  print(f"{voice['name']}; {voice['voice_id']}")
