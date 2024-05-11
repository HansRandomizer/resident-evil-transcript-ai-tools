import json

# Load the JSON file
with open('D:/codeProjects/resident-evil-transcript-ai-tools/translations/input.json', 'r') as file:
    data = json.load(file)

# Sort the entries by filename (case-insensitive)
data_list = data['translated_results']

# Sort the list based on the filename (case-insensitive)
sorted_data_list = sorted(data_list, key=lambda x: x['filename'].lower())

# Convert the sorted list back to a dictionary
sorted_data = {'translated_results': sorted_data_list}

# Save the sorted data to a JSON file
with open('D:/codeProjects/resident-evil-transcript-ai-tools/translations/output.json', 'w') as file:
    json.dump(sorted_data, file, indent=4)