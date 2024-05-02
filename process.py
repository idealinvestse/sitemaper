import os
import json

# Set the input folder and output file
input_folder = 'C:\python\Sitemaper\out\f2d092ae4982fa8108af4721e0778e9e'
output_file = 'merged_json.json'

# Create a list to store the merged data
merged_data = []

# Iterate through all .json files in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith('.json'):
        # Open and read the file
        with open(os.path.join(input_folder, filename), 'r') as f:
            data = json.load(f)

        # Clean the text and replace characters
        for item in data:
            for key, value in item.items():
                if isinstance(value, str):
                    value = value.replace('ä', '\u^[[B^[[B^[[B^[[B^[[B^[[B00e4').replace('ö', '\u00f6').replace('å', '\u00e5')
                    item[key] = value

        # Add the cleaned data to the merged list
        merged_data.extend(data)

# Write the merged data to a single .json file
with open(output_file, 'w') as f:
    json.dump(merged_data, f, indent=4)
