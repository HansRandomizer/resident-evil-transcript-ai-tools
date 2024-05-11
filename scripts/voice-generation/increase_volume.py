# Generated voices may be hard to understand when background music is playing. 
# With this script you can update the voice volume. 
# I found 9 decibels to be a good value since you can understand the voices while music is playing and the quality is still good enough
# But feel free to try it out

# REMEMBER TO MAKE A BACKUP OF YOUR VOICES BEFORE USING THIS SCRIPT. IT WILL OVERWRITE YOUR EXISTING FILES....
import os
import logging
from pydub import AudioSegment

# location of your generated voices...
directory = "d:/codeProjects/mod_teenage-mutant-ninja-stars/voice"

def increase_volume(file_path, volume_increase):
    audio = AudioSegment.from_file(file_path)
    louder_audio = audio + volume_increase

   # this will overwrite your existing files....
    louder_audio.export(file_path, format=file_path.split(".")[-1])

    logging.info(f"Volume increased by {volume_increase} dB for file: {file_path}")



# Specify the volume increase in decibels (dB)
volume_increase = 9

for filename in os.listdir(directory):
    file_path = os.path.join(directory, filename)
    if file_path.endswith(".WAV") or file_path.endswith(".wav"):
        increase_volume(file_path, volume_increase)