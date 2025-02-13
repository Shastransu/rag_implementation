import re

# Load processed chunk data
chunk_data_path = "chunk_analysis_results_fixed.txt"
chunks = []

with open(chunk_data_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
    current_chunk = {}
    
    for line in lines:
        line = line.strip()
        
        # Detect new chunk start
        if line.startswith("Chunk") and current_chunk:
            chunks.append(current_chunk)
            current_chunk = {}  # Reset for next chunk
        
        # Extract KB_ID with more robust regex
        elif re.match(r"KB_ID\s*:\s*(KB-\d+)", line):
            current_chunk["KB_ID"] = re.match(r"KB_ID\s*:\s*(KB-\d+)", line).group(1)

        # Extract Title
        elif re.match(r"Title\s*:\s*(.+)", line):
            current_chunk["Title"] = re.match(r"Title\s*:\s*(.+)", line).group(1)

        # Extract other sections dynamically, ensuring proper key-value pairs
        elif ":" in line:
            parts = line.split(":", 1)
            key, value = parts[0].strip(), parts[1].strip()
            if key and value:
                current_chunk[key] = value

    # Append last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk)

# Debug: Check if KB_IDs are properly extracted
for chunk in chunks:
    if "KB_ID" not in chunk or not chunk["KB_ID"]:
        print("Error: KB_ID missing or empty for a chunk:", chunk)
    else:
        print(f"Successfully extracted KB_ID: {chunk['KB_ID']}")

print(f"Total Chunks Processed: {len(chunks)}")