# This script is generating voices using ElevenLabs api. You need an Elevenlabs account and a token...

# The VOICES MUST HAVE THE SAME NAME AS THE SPEAKERS IN THE TRANSCRIPT! (ANNOUNCER, JILL, CHRIS, REBECCA, WRESKER...)
# OR IT WON'T WORK! There is no mapping of voices supported atm. You can rename your voices in the Voice-Settings!

# Remember, you need a ElevenLabs API KEY and setup your .env file...
import os
import requests 
import json
import re
import time

from pydub import AudioSegment
from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()
CHUNK_SIZE = 1024  # Size of chunks to read/write at a time
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY") # Your ElevenLabs API key for authentication
VOICE_CLONE_OUTPUT_BASE_PATH = os.getenv("VOICE_CLONE_OUTPUT_BASE_PATH")  # Path to save the output audio file
VOICE_CLONE_ORIGIN_AUDIO_PATH = os.getenv("VOICE_CLONE_ORIGIN_AUDIO_PATH") # original audio files, since we have to extend results to the original runtime (or else there will be issues during playback...)
VOICE_LIST_URL = "https://api.elevenlabs.io/v1/voices"

# This is the original audio framerate of the pc version.
AUDIO_FRAMERATE = 22050

input_transcript_path = os.getenv("VOICE_TRANSLATED_TRANSCRIPT_PATH")
# sometimes you just want to select certain files or a range (like all entries starting with V001_)
# regex will alawys be caseinsensitive because they are randomly using lowercase names.
filename_regex = r".*\.WAV"

headers = {
    "Accept": "application/json",
    "xi-api-key": ELEVENLABS_API_KEY
}

headers_voicelist = {
  "Accept": "application/json",
  "xi-api-key": ELEVENLABS_API_KEY,
  "Content-Type": "application/json"
}

def init_voicelist():
    response = requests.get(
            VOICE_LIST_URL, 
            headers=headers
        )

    voice_data = response.json()
    return voice_data["voices"]

def createVoice(text_to_speak, speaker_name, filename):
    data = {
        "text": text_to_speak,
        "model_id": "eleven_multilingual_v2",
        # I had good results with these settings but feel free to adjust or create a setup with individual settings for each character
        "voice_settings": {
            "stability": 1.0,
            "similarity_boost": 1.0,
            "style": 0.3,
            "use_speaker_boost": False,
            "output_format": "mp3_22050_32"
        }
    }

    speaker_id = get_voice_id_for_speaker_name(speaker_name)
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{speaker_id}/stream"
    response = requests.post(tts_url, headers=headers, json=data, stream=True)
 

    if response.ok:
        output_path = os.path.join(VOICE_CLONE_OUTPUT_BASE_PATH)
        os.makedirs(output_path, exist_ok=True)
        with open(f"{VOICE_CLONE_OUTPUT_BASE_PATH}/{filename}.mp3", "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)
        logging.info(f"{filename} generated")
    else:
        logging.error(f"error generating {filename}: response.text")
    return

def get_voice_id_for_speaker_name(speaker_name):
   found_voice_id = [voice for voice in voices if voice["name"] == speaker_name]

   if not found_voice_id:
       raise ValueError(f"found no voice id for speaker_name: {speaker_name}")
   
   return found_voice_id[0]["voice_id"]

def translate(source_file, filename_regex):
    with open(source_file, 'r') as file:
        transcript_data = json.load(file)
    
    relevant_entries = get_relevant_transcript_entries(transcript_data, filename_regex)
    logging.debug(f"relevant_entries: {relevant_entries}")
    for entry in relevant_entries:
        time.sleep(2)
        if not is_multi_speaker(entry):
            generate_single_speaker_voice(entry)            
        else:
            generate_each_segment_seperately(entry)

def generate_single_speaker_voice(
        entry 
        ):
    createVoice(
        entry['translated_transcript'],
        entry['translated_segments'][0]['speaker'],
        entry['filename']
        )
    
    convert_mp3_to_re_compatible_audio_file(
        f"{VOICE_CLONE_OUTPUT_BASE_PATH}\\{entry['filename']}.mp3", 
        f"{VOICE_CLONE_OUTPUT_BASE_PATH}\\{entry['filename']}",
        entry['filename']
        )

def generate_each_segment_seperately(
        entry
):
    logging.debug(f"multi generation for file {entry['filename']}")
    segment_voice_filenames = []
    segments = entry['translated_segments']
    segment_count = 0
    
    for segment in segments:
        segment_filename = f"segment_{segment_count}_{entry['filename']}"
        segment_target_path = f"{VOICE_CLONE_OUTPUT_BASE_PATH}\\{segment_filename}.mp3"
        segment_voice_filenames.append(segment_target_path)

        createVoice(
            text_to_speak = segment['text'],
            speaker_name = segment['speaker'],
            filename = segment_filename
        )
        segment_count += 1

    logging.debug(f"merging {segment_voice_filenames}")
    merge_mp3(segment_voice_filenames, os.path.join(VOICE_CLONE_OUTPUT_BASE_PATH, entry['filename']), entry['filename'])

def get_relevant_transcript_entries(transcript_data, filename_regex):
    found_entries = []
    
    for entry in transcript_data["translated_results"]:
        if is_match(entry['filename'],regex=filename_regex):
            found_entries.append(entry)
        
    return found_entries

def is_match(string, regex):
    return bool(re.match(regex, string, re.IGNORECASE))

def is_multi_speaker(entry):
    segments = entry['translated_segments']
    speakers = set(segment['speaker'] for segment in segments)
    return len(speakers) > 1

def merge_mp3(mp3_files, output_wav, filename):
    combined = AudioSegment.from_file(mp3_files[0], format='mp3')
    silence_part = AudioSegment.silent(1000, AUDIO_FRAMERATE)
    for mp3_file in mp3_files[1:]:
        next_audio = AudioSegment.from_file(mp3_file, format='mp3')
        combined += next_audio 
        combined += silence_part 

    combined = combined.set_frame_rate(AUDIO_FRAMERATE)
    combined = extend_to_original_length(combined, filename)
    combined.export(output_wav, format='wav')
    for mp3_file in mp3_files:
        os.remove(mp3_file)

def convert_mp3_to_re_compatible_audio_file(mp3_file, output_wav, filename):
    audio_segment = AudioSegment.from_file(mp3_file, format='mp3')
    audio_segment = audio_segment.set_frame_rate(AUDIO_FRAMERATE)
    audio_segment = extend_to_original_length(audio_segment, filename)
    audio_segment.export(output_wav, format='wav')
    os.remove(mp3_file)    
    
def extend_to_original_length(audio_segment, filename):
    original_audio = AudioSegment.from_file(f"{VOICE_CLONE_ORIGIN_AUDIO_PATH}\\{filename}")
    original_duration = len(original_audio)
    new_duration = len(audio_segment)
    if original_duration > new_duration:
        silence_duration_ms = original_duration - new_duration
        silence_part = AudioSegment.silent(silence_duration_ms, AUDIO_FRAMERATE)
        extend_audio_segment = audio_segment + silence_part
        return extend_audio_segment.set_frame_rate(AUDIO_FRAMERATE)
    return audio_segment

transcript_data = {}
relevant_entries = []
voices = init_voicelist()

translate(input_transcript_path, filename_regex)

