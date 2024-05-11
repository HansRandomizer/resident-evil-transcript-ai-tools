import transformers
import torch
import json
import os
import logging
from FileMode import FileMode
from dotenv import load_dotenv

load_dotenv()
# uncomment the following two lines, to login to https://huggingface.co/, in case the model is not locally available
# remember you will need a HuggingFace account and a token to proceed.
# from huggingface_hub import login
#login()

# There are two file modes. 
# APPEND to continue translation or NEW_FILE to clear the current result and start over
file_mode = FileMode.APPEND
logging.debug(f"file_mode: {file_mode}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.addLevelName(5, "TRACE") # for logging the prompt...

model_id = os.getenv("HUGGINGFACE_TARGET_MODEL") # feel free to use any other model but I tested it only with meta-llama/Meta-Llama-3-8B-Instruct
output_base_name = os.getenv("TRANSLATED_TRANSCRIPT_NAME") # your basename for the output json

# Adjust your translation target here
translation_main_goal = os.getenv("TRANSLATION_MAIN_GOAL")
# Add more details. 
# I experienced that llama3 will be heavily influenced by a dialoge example so make sure it's very well and representative
# The quality of your output depends on the prompt, your details and on the model you use.
additional_details = os.getenv("TRANSLATION_DETAILS")

# NOTICE THESE ARE RELATIVE PATHS FROM YOUR CURRENT LOCAL PATH!
result_json_file_path = f'./translations/{output_base_name}.json' #
log_file_path = f'./translations/{output_base_name}.log'
input_transcript_path = os.getenv("ORIGINAL_TRANSCRIPT_PATH")


# Basic setups, loading transcripts, preparing pipeline etc...
input_transcript = {}
with open(input_transcript_path, 'r') as file:
        input_transcript = json.load(file)

if file_mode == FileMode.NEW_FILE or not os.path.exists(result_json_file_path):
    with open(result_json_file_path, 'w') as file:
     json.dump({}, file, indent=4)

current_persisted_result = {}

with open(result_json_file_path, 'r') as file:
    current_persisted_result = json.load(file)
    logging.debug(f"current_persisted_result: {current_persisted_result}")
    if 'translated_results' not in current_persisted_result:
        current_persisted_result['translated_results'] = []

pipeline = transformers.pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": torch.bfloat16},
    device="cuda", # Working with local cuda 12.23
)

def build_prompt(transcript, previous_results):

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

    # I was trying lm-format-enforcer to enforce a json scheme like in the llama.cpp variant.
    # But the responses turned out to be so bad, that I stick with defining the output scheme in the prompt, which works well actually with llama3-7b
    output_scheme= """{
        "filename": "V001_03.WAV",
        "original_transcript": " {keep the original value here}",
        "translated_transcript": "{translated transcript goes here}",
        "translated_segments": [
            {
                "start": 0.0,
                "end": 1.0,
                "text": " {translated segment goes here}",
                "speaker": "{THE ORIGINAL SPEAKER}"
            },
            {
                "start": 1.0,
                "end": 3.0,
                "text": " {next translated segment goes here}",
                "speaker": "{THE ORIGINAL SPEAKER}"
            },
            {
                "start": 3.0,
                "end": 6.08,
                "text": " {next translated segment goes here}",
                "speaker": "{THE ORIGINAL SPEAKER}"
            }
        ]
    }"""
    
    content_system=f"""You will be provided with the following inputs to translate the dialogue of the 1996 video game Resident Evil. You must translate (or better transform) all Dialogs, so they will all fulfill the main goal: {translation_main_goal}
    You must respect the length of the original transcription and MAKE SURE THE TEXT YOU TRANSLATE IS OF THE SAME LENGTH THAN THE ORIGINAL! NEVER ADD TOO MUCH TEXT , NEVER SKIP TOO MUCH TEXT! The Text will later be transformed into audio and must be of the same length.
    Also, respect the following additional details in your translation output: {additional_details}

    You will receive a JSON file, containing the original game transcript, with this structure:
    {input_scheme}

Also you will receive the previous results you have generated. Only check the generated text and speaker of the previous result, so you can create a proper new spoken dialog. Do not include the previous results directly into your answer.
The previous results are only passed to you, so you can generate text which makes sense in the context.

YOUR TASK IS TO TRANSFORM THE DIALOGUE IN THE TEXT FIELD, while preserving the original speaker labels and order of lines. 
Do not modify the "speaker" or any other fields. Focus on the speaker labels, to match up who says each line.
When you create a new line and there was a previous line, make sure to respect it in your translation of the new line, but only if it makes sense in the context of the sentence.
Return the translated game transcript in this JSON format: 
{output_scheme}

Make sure the JSON IS ABSOLUTELY VALID AND IS NOT MISSING ANY {{ }} or ,. 
Make sure you have the quotes right. Your String output must absolutely be parsable as valid json.
- the original text must stay in the transcript field of your result.
- translate the text of the translation field and for each text-field in the segments. make sure the content of the translation field is also aligned with the segmented text in the text-field. 
- EACH RESPONSE MUST BE A VALID JSON
- DO NOT MISS ANY PARTS OF THE JSON 
- EACH RESPONSE MUST START WITH {{ 
- EACH RESPONSE MUST END WITH }}
- USE DOUBLE QUOTES, NOT SINGLE QUOTES!
- FORBIDDEN STRING: : '
- FORBIDDEN STRING: {{'
- NEVER SWITCH A SPEAKER!
- each field in the JSON payload must be wrapped with "{{parameter}}" e.g. "filename": "V001_03.WAV",. 'filename' is forbidden because of the ' char. never use ' chars to wrap keys or values!

Ensure the speaker labels match the original and the lines remain in the same order. 
FOCUS ON TRANSFORMING THE DIALOGUE TEXT IN HIGH QUALITY.
Do not write anything else but the output json.  
Don't add any additional info, like how you translated it or any polite phrases.
"""
    content_user = f"""
    PREVIOUS RESULT (just for your information): {previous_results if previous_results else "none"}
    TRANSCRIPT TO TRANSLATE: {transcript}
    """

    messages = [
    {"role": "system", "content": content_system},
    {"role": "user", "content": content_user},
    ]

    prompt = pipeline.tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True,
     )

    return prompt

def execute_prompt(prompt):
    terminators = [
        pipeline.tokenizer.eos_token_id,
        pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]
    
    # Feel free to adjust ... 
    outputs = pipeline(
        prompt,
        # there are some files with lots of dialog and many segments so this causes extra tokens.
        # Most files work fine with 512 tokens. V103_01.WAV, V106_02.WAV, V103_01.WAV require up to about 1200...
        # Considering a translation can be quite longer than the original text, we set max tokens to a higher value ...
        max_new_tokens=2000,
        eos_token_id=terminators,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
    )

    return outputs[0]["generated_text"][len(prompt):]

def get_transcript_entry(filename):
    for entry in input_transcript:
        if entry['filename'] == filename:
            return json.dumps(entry)
    return None

def trigger_translation():
    translated_results=[]
    
    for entry in input_transcript:
        filename = entry['filename']
        if file_mode == FileMode.APPEND:
                    is_entry_existing_in_result_json = any(entry["filename"] == filename for entry in current_persisted_result['translated_results'])
                    if is_entry_existing_in_result_json:
                        logging.info(f"filename {filename} is already translated. Continue with next filename...")
                        continue
        try:
            transcript_entry = get_transcript_entry(filename)            
            logging.debug(f"transcript_entry: {transcript_entry}")
            previous_results = filter_previous_ai_results_for_file(filename, translated_results)
            logging.debug(f"previous_results: {previous_results}")
            prompt = build_prompt(transcript_entry, previous_results)
            logging.log(5, f"prompt: {prompt}") # 5 means trace level logging...A manual level I added at the top of the script

            translated_json_ai_response = execute_prompt(prompt)
            logging.debug(f"translated_json_ai_response: {translated_json_ai_response}")
            converted_ai_output = json.loads(translated_json_ai_response)
            logging.debug(f"converted_ai_output: {converted_ai_output}")
            current_persisted_result['translated_results'].append(converted_ai_output)
            logging.log(5, f"current_persisted_result: {current_persisted_result}") # 5 means trace level logging...A manual level I added at the top of the script

            with open(result_json_file_path, 'w') as file:
                # Write the updated list back to the file
                json.dump(current_persisted_result, file, indent=4)
                logging.info(f"translated {filename}")

        except Exception as e:
            logging.error(f"{e}, {filename}")

def filter_previous_ai_results_for_file(filename, previous_results):
    logging.debug(f"filter_previous_ai_results_for_file")
    dialog_prefix = filename.split("_")[0]
    logging.debug(f"dialog_prefix {dialog_prefix}")
    filtered_results = []
    for item in previous_results:
         try:
            dict_item = json.loads(item)
            if dict_item['filename'].startswith(dialog_prefix):
                filtered_results.append(dict_item)
         except json.UnicodeDecodeError as e:
            logging.error(f"JSONDecodeError: {e.msg} at position {e.pos}, original item: {item}")
    logging.debug(f"filtered_results: {filtered_results}")
    return filtered_results

trigger_translation()
