## Resident Evil 1996 - Full Transcript and AI Tools to Translate and generate Voices
A segmented transcript of the video game Resident Evil 1996 and some AI tools to change the transcript using llm and clone voices.

## Translate the Transcript using Llama.cpp or huggingface transformers directly
This project contains python scripts to either directly translate the transcript with huggingface transformer pipeline or use llama.cpp.
All you have to do is create an .env file (see the example .env in the script folder), define your prompts and start

## Voice Cloning Scripts
There are scripts to segment the audiofiles by speaker, to make voice cloning easy (You need permission to clone voices. USE THIS ON YOUR OWN RISK!)

## Manual for Voice Cloning
You need an ElevenLabs account and an API Token.
The Elevenlabs voices must have the same name as in the Speaker Script (JILL, WRESKER, CHRIS, BARRY, REBECCA, BRAD, ANNOUNCER, EDWARD, ENRICO)

## Issues and Problems
- Some audio files in RE1 have multiple speakers. In this case the scripts will create multipe MP3 Files and merge them with a pause of 1 second. This does not always match so audio will be out of sync with subtitles and movements of characters. I will fix this in near future...
- Generated JSON is sometimes broken, double check all entries are valid
- Depending on the llm you are using, results are likely to have errors (wrong speakers, invalid fieldnames etc.), you will have to check all results for errros and fix them manually.
- Voice clone results might sound bad
