# This will put copy audiofiles for these each speaker in the transcript, for voicecloning. 

import json
import os
import shutil
from dotenv import load_dotenv

load_dotenv()
base_dir = os.getenv("VOICE_CLONE_ORIGIN_AUDIO_PATH")
root_folder = os.path.join(base_dir, "voiceclone")
os.makedirs(root_folder, exist_ok=True)

with open('pyannote_results.json') as f:
    data = json.load(f)

for sound_file, segments in data.items():
    speakers = set(segment['speaker'] for segment in segments)
    if len(speakers) == 1:
        speaker = speakers.pop()
        
        speaker_folder = os.path.join(root_folder, speaker)
        os.makedirs(speaker_folder, exist_ok=True)
        
        src_file = os.path.join(base_dir, sound_file)
        dst_file = os.path.join(speaker_folder, sound_file)
        shutil.copy(src_file, dst_file)