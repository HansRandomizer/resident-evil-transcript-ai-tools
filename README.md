# Resident Evil 1996 - Full Transcript and AI Tools to Translate and Generate Voices

A segmented transcript of the video game Resident Evil 1996 along with AI tools to modify the transcript using LLM and clone voices.

## Translate the Transcript using Llama.cpp or Hugging Face Transformers Directly

This project contains Python scripts to either directly translate the transcript with Hugging Face Transformer pipeline or use Llama.cpp. All you have to do is create an `.env` file (see the example `.env` in the script folder), define your prompts, and start.

## Voice Cloning Scripts

There are scripts to segment the audio files by speaker to facilitate voice cloning (You need permission to clone voices. USE AT YOUR OWN RISK!).

## Manual for Voice Cloning

You need an ElevenLabs account and an API Token. The ElevenLabs voices must have the same names as those in the Speaker Script (JILL, WESKER, CHRIS, BARRY, REBECCA, BRAD, ANNOUNCER, EDWARD, ENRICO).

## Issues and Problems

- Some audio files in RE1 have multiple speakers. In this case, the scripts will create multiple MP3 files and merge them with a pause of 1 second. This does not always match, so audio may be out of sync with subtitles and movements of characters. I plan to fix these issues soon.
- The generated JSON is sometimes broken; double-check that all entries are valid.
- Depending on the LLM you are using, results are likely to have errors (wrong speakers, invalid fieldnames, etc.). You will have to check all results for errors and fix them manually.
- Voice clone results might sound bad. In this case you can update single files or whole batches by selecting a proper filename REGEX e.g. (``` filename_regex = r".*\.WAV" -> filename_regex = r"V001_..\.WAV"```)
