import json
import os
from llama_cpp import Llama
from FileMode import FileMode
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.addLevelName(5, "TRACE") # for logging the prompt...

# Adjust your translation target here
translation_main_goal =  os.getenv("TRANSLATION_MAIN_GOAL")
logging.debug(f"translation_main_goal: {translation_main_goal}")

# Add more details. 
# I experienced that llama3 will be heavily influenced by a dialoge example so make sure it's very well and representative
# The quality of your output depends on the prompt, your details and on the model you use.
additional_details = os.getenv("TRANSLATION_DETAILS")
logging.debug(f"additional_details: {additional_details}")

# NOTICE THESE ARE RELATIVE PATHS FROM YOUR CURRENT LOCAL PATH!
base_name =  os.getenv("TRANSLATED_TRANSCRIPT_NAME")
result_json_file_path = f'./translations/{base_name}.json'
log_file_path = f'./translations/{base_name}.log'
original_transcript_path=os.getenv("ORIGINAL_TRANSCRIPT_PATH")

# There are two file modes. 
# APPEND to continue translation or NEW_FILE to clear the current result and start over
file_mode = FileMode.APPEND
logging.debug(f"file_mode: {file_mode}")

# llama.cpp supports response_format and I think it has been pretty reliable so far, so I'll keep it.
response_format = {
    "type": "json_object",
    "schema": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "original_transcript": {"type": "string"},
            "translated_transcript": {"type": "string"},
            "translated_segments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "number"},
                        "end": {"type": "number"},
                        "text": {"type": "string"},
                        "speaker": {"type": "string"}
                    },
                    "required": ["start", "end", "text", "speaker", ]
                }
            }
        },
        "required": ["filename", "original_transcript", "translated_segments", "translated_transcript"]
    },
}

input_scheme= """{
        "filename": "V001_03.WAV",
        "transcript": " What is that? I'll go and check. Okay, Jill and I will stay in the hall in case of an emergency.",
        "segments": [
            {
                "start": 0.0,
                "end": 1.0,
                "text": " What is that?",
                "speaker": "JILL"
            },
            {
                "start": 1.0,
                "end": 3.0,
                "text": " I'll go and check.",
                "speaker": "CHRIS"
            },
            {
                "start": 3.0,
                "end": 6.08,
                "text": " Okay, Jill and I will stay in the hall in case of an emergency.",
                "speaker": "WRESKER"
            }
        ]
    },"""

# Actually I'm not sure if we really need this output example, since we already have the response_format...
# Nontheless the model must insert the values to the correct fields so I guess it can't hurt adding the output scheme to the prompt...
output_scheme= """{
        "filename": "V001_03.WAV",
        "transcript": " {this is where THE ORIGINAL TEXT MUST BE KEPT}",
        "translated_transcript": " {this is where to put your translated text. Must be as long as the original text}",
        "segments": [
            {
                "start": 0.0,
                "end": 1.0,
                "text": " {this is where to put your translated segment, must be as long as the original segment}",
                "speaker": "{THE ORIGINAL SPEAKER}"
            },
            {
                "start": 1.0,
                "end": 3.0,
                "text": " {this is where to put your translated segment, must be as long as the original segment}",
                "speaker": "{THE ORIGINAL SPEAKER}"
            },
            {
                "start": 3.0,
                "end": 6.08,
                "text": " {this is where to put your translated segment, must be as long as the original segment}",
                "speaker": "{THE ORIGINAL SPEAKER}"
            }
        ]
    }"""

def execute(transcript, previous_results):
   
    content_system=f"""You will be provided with the following inputs to translate the dialogue of the 1996 video game Resident Evil. You must translate (or better transform) all Dialogs, so they will all fulfill the main goal: {translation_main_goal}
        You must respect the length of the original transcription and MAKE SURE THE TEXT YOU TRANSLATE IS OF THE SAME LENGTH THAN THE ORIGINAL! NEVER ADD TOO MUCH TEXT , NEVER SKIP TOO MUCH TEXT! The Text will later be transformed into audio and must be of the same length.
        Also, respect the following additional details in your translation output: {additional_details}

        You will receive a JSON file, containing the original game transcript, with this structure:
        {input_scheme}

    Also you will receive the previous results you have generated. Only check the generated text and speaker of the previous result, so you can create a proper new spoken dialog. Do not include the previous results directly into your answer.
    The previous results are only passed to you, so you can generate text which makes sense in the context.

    YOUR TASK IS TO TRANSFORM THE DIALOGUE IN THE TEXT FIELD, while preserving the original speaker labels and order of lines. 
    PRESERVE THE LENGTH OF THE CURRENT TRANSCRIPT AND CURRENT SEGMENT-TEXT AT ALL COSTS!!!!
    Do not modify the "speaker" or any other fields. Focus on the speaker labels, to match up who says each line.
    When you create a new line and there was a previous line, make sure to respect it in your translation of the new line, but only if it makes sense in the context of the sentence.
    Return the translated game transcript in this JSON format: 
    {output_scheme}


    Ensure the speaker labels match the original and the lines remain in the same order. 
    FOCUS ON TRANSFORMING THE DIALOGUE TEXT.
    """
    content_user = f"""
        PREVIOUS RESULT (just for your information): {previous_results if previous_results else "none"}
        TRANSCRIPT TO TRANSLATE: {transcript}
        """

    messages = [
        {"role": "system", "content": content_system},
        {"role": "user", "content": content_user},
        ]

    llm_chat_result = llm.create_chat_completion( 
        messages=messages, 
        response_format=response_format,
        temperature=0.8
        )
    logging.debug(f"llm_chat_result: {llm_chat_result}")
    generated_text = llm_chat_result["choices"][0]['message']['content']
    logging.debug(f"generated_text: {generated_text}")
    return generated_text
  
transcript = """{
        "filename": "V001_01.WAV",
        "transcript": " Barry, where's Barry? Well, I'm sorry, but he's probably...",
        "segments": [
            {
                "start": 0.0,
                "end": 2.0,
                "text": " Barry, where's Barry?",
                "speaker": "CHRIS"
            },
            {
                "start": 2.88,
                "end": 5.5200000000000005,
                "text": " Well, I'm sorry, but he's probably...",
                "speaker": "WRESKER"
            }
        ]
    },"""


def get_transcript(filename):
    with open('./transcripts/re_1996_transcript_with_speakers.json', 'r') as file:
        transcript_data = json.load(file)
    
    for entry in transcript_data:
        if entry['filename'] == filename:
            return json.dumps(entry)
    
    return None

def process_files():
    translated_results=[]

    with open('./transcripts/re_1996_transcript_with_speakers.json', 'r') as file:
        transcript_data = json.load(file)
    
    for entry in transcript_data:
        filename = entry['filename']
        logging.debug(f"filename: {filename}")
       
        try:
            with open(result_json_file_path, 'r') as file:
                current_persisted_result = json.load(file)
                logging.log(5,f"current_persisted_result: {current_persisted_result}")
                if 'translated_results' not in current_persisted_result:
                        current_persisted_result['translated_results'] = []
                
                if file_mode == FileMode.APPEND:
                    is_entry_existing_in_result_json = any(entry["filename"] == filename for entry in current_persisted_result['translated_results'])
                    logging.log(5,f"is_entry_existing_in_result_json: {is_entry_existing_in_result_json} ({filename})")
                    if is_entry_existing_in_result_json:
                        logging.info(f"filename {filename} is already in resultset. Continue with next filename...")
                        continue

                transcript_json = get_transcript(filename)
                logging.debug(f"transcript_json: {transcript_json}")
                previous_results = filter_previous_ai_results_for_file(filename, translated_results)
                logging.log(5,f"previous_results: {previous_results}")
                translated_json_ai_response = execute(transcript_json, previous_results)
                translated_results.append(translated_json_ai_response)
                
                converted_ai_output = json.loads(translated_json_ai_response)
                logging.debug(f"converted_ai_output: {converted_ai_output}")
                current_persisted_result['translated_results'].append(converted_ai_output)

                with open(result_json_file_path, 'w') as file:
                    json.dump(current_persisted_result, file, indent=4)
                    logging.info(f"translated: {filename}")

        except Exception as e:
                logging.error(f"error: {e}. converted_ai_output: {converted_ai_output}")

# we will pass previous results so the ai can return a better dialog
def filter_previous_ai_results_for_file(filename, previous_results):
    logging.debug("filter_previous_ai_results_for_file")
    dialog_prefix = filename.split("_")[0]
    logging.log(5,f"dialog_prefix: {dialog_prefix}")
    dict_results = [json.loads(item) for item in previous_results]
    logging.log(5,f"dict_results: {dict_results}")
    filtered_results = [item for item in dict_results if item['filename'].startswith(dialog_prefix)]
    logging.debug(f"filtered_results: {filtered_results}")
    return filtered_results


# Clearing the result json or create new file.
if file_mode == FileMode.NEW_FILE or not os.path.exists(result_json_file_path):
    logging.debug(f"clearing fFile: {result_json_file_path}")
    with open(result_json_file_path, 'w') as file:
        json.dump({}, file, indent=4)
model_path=os.getenv("LLAMA_CPP_MODEL_PATH")

# check llama.cpp docs if you want or need to adjust
llm = Llama(
      model_path,
      n_gpu_layers=42,
      n_ctx=4200 
)


process_files()