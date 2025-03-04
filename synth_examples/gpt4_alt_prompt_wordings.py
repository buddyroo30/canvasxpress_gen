import json
import re
import os
import time
from openai import AzureOpenAI
from dotenv import load_dotenv
import tiktoken

load_dotenv()

use_model = 'gpt-4o-global'

openai_enc = tiktoken.encoding_for_model(use_model)

def generate_results_openai(prompt, model='gpt-4o-global', max_new_tokens=512, topp=1.0, temperature=0.0):

    client = AzureOpenAI()

    completion = client.chat.completions.create(
        model=model,
        max_tokens=max_new_tokens,
        temperature=temperature,
        top_p=topp,
        messages=[
         {
            "role": "user",
            "content": prompt,
            },
        ],
    )
    generated_text = completion.choices[0].message.content
    #time.sleep(1)

    return(generated_text)

def read_json_file(file_path):
    """
    Read a file containing JSON text and evaluate the contents to a Python dictionary.

    Args:
    - file_path (str): The path to the JSON file.

    Returns:
    - dict: The contents of the file as a Python dictionary.
    """
    try:
        with open(file_path, 'r') as file:
            # Read the file contents
            file_contents = file.read()
            # Parse the JSON text to a Python dictionary
            data = json.loads(file_contents)
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {file_path}")
        return None

def write_string_to_file(file_path, content):
    """
    Write a string to a file.

    Args:
    - file_path (str): The path to the file.
    - content (str): The string content to write to the file.
    """
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"Successfully wrote to {file_path}")
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")

# Function to remove backticks and optional ```json block from the input string
def remove_backticks_and_json_block(input_str):
    """
    Remove backticks and optional ```json block from the input string.

    Args:
    - input_str (str): The input string containing backticks and optional ```json block.

    Returns:
    - str: The cleaned string without backticks and optional ```json block.
    """
    # Remove the ```json block or ``` block from the beginning and end of the string
    cleaned_str = re.sub(r'^```json|```$', '', input_str)
    cleaned_str = re.sub(r'^```|```$', '', cleaned_str)
    return cleaned_str.strip()

file_path = 'synth_examples.json'
updated_file_path = 'synth_examples_updated.json'
partial_results = {}
if os.path.exists(updated_file_path):
    tmp_data = read_json_file(updated_file_path)
    for current_example in tmp_data['examples']:
        prompt = current_example['prompt']
        if 'alt_prompts' in current_example:
            alt_prompts = current_example['alt_prompts']
            partial_results[prompt] = alt_prompts
data = read_json_file(file_path)
updated_data = {}
examples_data = data['examples']
parameters_data = data['parameters']
updated_data['parameters'] = parameters_data
updated_examples = []
total_input_tokens = 0
total_output_tokens = 0
for current_example in examples_data:
    header = current_example['header']
    config = current_example['config']
    prompt = current_example['prompt']
    cur_updated_example = { "header": header, "config": config, "prompt": prompt }
    if prompt in partial_results:
        cur_updated_example['alt_prompts'] = partial_results[prompt]
        updated_examples.append(cur_updated_example)
        continue
    alt_prompt = """The following is an English paragraph of multiple sentences that describes a data visualization, and please generate 3
                 different, alternative ways of expressing the same meaning.

                But important: Keep the word "sort" unchanged if it appears. Keep the words "group by"
                unchanged if they appear. Avoid substituting the term "sort" with "group by," or vice versa.
                "Sort" and "group" are not interchangeable terms and should not be treated as synonyms.
                "Sort" and "organize" are not interchangeable; each carries a distinct meaning. "Group"
                refers to aggregating data, while "sort" involves organizing data in a specific order.
                When building a filtered dataset, use only "like" and "different" to define criteria.
                Use "different" in place of "not like" whenever the word "filter" appears in the paragraph.
                Return the 3 alternative paragraphs as a valid JSON list or array of strings. Return ONLY
                the JSON list/array and nothing else (no backticks, do not embed the list in another JSON
                object, etc). Specifically return like this: ["ALTERNATIVE1", "ALTERNATIVE2", "ALTERNATIVE3"].
                Here is the paragraph: """ + prompt
    input_encoding_tokens = openai_enc.encode(alt_prompt)
    num_input_tokens = len(input_encoding_tokens)
    total_input_tokens += num_input_tokens
    generated_text = generate_results_openai(alt_prompt, model=use_model, max_new_tokens=2048, topp=1.0, temperature=0.1)
    output_encoding_tokens = openai_enc.encode(generated_text)
    num_output_tokens = len(output_encoding_tokens)
    total_output_tokens += num_output_tokens
    print(f"Header: {header}\nConfig: {config}\nPrompt: {prompt}\nNum Input Tokens: {num_input_tokens}\nNum Output Tokens: {num_output_tokens}\nGenerated Text: {generated_text}\n\n")
    try:
        cleaned_generated_text = remove_backticks_and_json_block(generated_text)
        python_list = json.loads(cleaned_generated_text)
        cur_updated_example['alt_prompts'] = python_list
        updated_examples.append(cur_updated_example)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        break

updated_data['examples'] = updated_examples

print(f"Total input tokens: {total_input_tokens}\nTotal output tokens: {total_output_tokens}")
updated_data_str = json.dumps(updated_data, indent=2)
write_string_to_file(updated_file_path, updated_data_str)
    