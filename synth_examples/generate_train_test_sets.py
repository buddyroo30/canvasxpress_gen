import json
import re
import random
import sys

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

def shuffle_array_in_place(arr):
    """
    Randomly shuffle an array in-place.

    Args:
    - arr (list): The array to shuffle.

    Returns:
    - None: The array is shuffled in-place.
    """
    random.shuffle(arr)

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

updated_file_path = 'synth_examples_updated.json'
data = read_json_file(updated_file_path)
shuffle_array_in_place(data['examples'])
paramsArray = data['parameters']
write_string_to_file("parameters.json", json.dumps(paramsArray,indent=2))
shuffledExamples = data['examples']
trainSet = shuffledExamples[:2300]
write_string_to_file("train_set.json", json.dumps(trainSet,indent=2))
testSet = shuffledExamples[2300:]
write_string_to_file("test_set.json", json.dumps(testSet,indent=2))

    