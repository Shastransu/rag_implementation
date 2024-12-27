## Import libraries required

import os
from dotenv import load_dotenv
import nest_asyncio
import re
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader

## Call the variable

load_dotenv()
nest_asyncio.apply()

LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")   # Call the API Key

def get_files_in_directory(path):
    """Gets all files in the specified directory.

    Args:
        path: The directory path.

    Returns:
        A list of filenames in the directory.
    """

    return [f for f in os.listdir(path) if (os.path.isfile(os.path.join(path, f)))]

raw_file_dir = os.getcwd()   #Current directory

input_raw_file_dir = raw_file_dir + "/input_docs"   #Inout files
output_raw_file_dir = raw_file_dir + "/parsed_docs"  #Output files

print(input_raw_file_dir)

input_raw_file_paths = get_files_in_directory(input_raw_file_dir)
print(input_raw_file_paths)
print("Total number of files present in input directory:",len(input_raw_file_paths))

## Using the Llama Prase to Parse document
### Creating a llama parse object

parser = LlamaParse(
    result_type="markdown"
)

output_docs = []

for i in range(len(input_raw_file_paths)):
    print(f"Currently parsing file name: {input_raw_file_paths[i]}")
    # use SimpleDirectoryReader to parse our file
    file_extension = "." + input_raw_file_paths[i].split(".")[-1]
    file_extractor = {file_extension: parser}

    # Use the markdown parse to parse the PDF and convert to markdown format
    documents = SimpleDirectoryReader(input_files=[input_raw_file_dir + "/" + input_raw_file_paths[i]],
                                      file_extractor=file_extractor).load_data()
    output_docs.append(documents)
