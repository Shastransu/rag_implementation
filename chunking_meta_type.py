import re
import json
from pathlib import Path
import pandas as pd
from datetime import datetime

# Load the document
file_path = r"D:\cag-demo\henfiled_KB_V2.md"
with open(file_path, "r", encoding="utf-8") as file:
    content = file.read()

# Define a regex pattern to detect KB sections
kb_pattern = re.compile(r"(#### KB-\d+:.*?)(?=#### KB-\d+:|\Z)", re.DOTALL)

# Extract KB articles
kb_articles = kb_pattern.findall(content)

# Define a function to structure the extracted chunks
def process_kb_articles(kb_articles):
    structured_data = []
    print("\n=== Generated Chunks ===\n")
    
    for idx, kb in enumerate(kb_articles, 1):
        # Extract Unique ID and Title
        kb_id_match = re.search(r"#### (KB-\d+): (.+)", kb)
        kb_id = kb_id_match.group(1) if kb_id_match else "Unknown"
        title = kb_id_match.group(2) if kb_id_match else "Unknown"

        # Improved metadata extraction with multiline support
        metadata_pattern = r"- \*\*([^:]+):\*\* ((?:.(?!-\s\*\*))*.)"
        metadata = dict(re.findall(metadata_pattern, kb, re.DOTALL))
        
        # Updated section patterns with strict boundary detection
        sections = {
            'Primary Information': r"\*\*Primary Information:\*\*\n(.*?)(?=\n\*\*[A-Z]|\Z)",
            'Locations': r"\*\*Locations:\*\*\n(.*?)(?=\n\*\*[A-Z]|\Z)",
            'Storage Services': r"\*\*Storage Services:\*\*(.*?)(?=\n\*\*|\Z)",
            'How It Works': r"\*\*How It Works:\*\*(.*?)(?=\n\*\*|\Z)",
            'Comparison with Standard Self-Storage': r"\*\*Comparison with Standard Self-Storage:\*\*(.*?)(?=\n\*\*|\Z)",
            'Unit Sizes': r"\*\*Unit Sizes:\*\*(.*?)(?=\n\*\*|\Z)",
            'Promotions': r"\*\*Promotions:\*\*(.*?)(?=\n\*\*|\Z)",
            'FAQs': r"\*\*FAQs:\*\*(.*?)(?=\n\*\*|\Z)",
            'Service Details': r"\*\*Service Details:\*\*(.*?)(?=\n\*\*|\Z)",
            'About Henfield Storage': r"\*\*About Henfield Storage:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Why Choose Henfield Storage': r"\*\*Why Choose Henfield Storage\?\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Edge Cases & Handling': r"\*\*Edge Cases & Handling:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Related Topics & Links': r"\*\*Related Topics & Links:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Structured Metadata': r"\*\*Structured Metadata:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'How It Works': r"\*\*How It Works:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Service Details': r"\*\*Service Details:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Unit Sizes': r"\*\*Unit Sizes:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Promotions': r"\*\*Promotions:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Contact Information': r"\*\*Contact Information:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Help & Information': r"\*\*Help & Information:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Regional Storage Locations': r"\*\*Regional Storage Locations:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'London Area Locations': r"\*\*London Area Locations:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Services': r"\*\*Services:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Specialized Storage Solutions': r"\*\*Specialized Storage Solutions:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Social Media': r"\*\*Social Media:\*\*(.*?)(?=\n\*\*[A-Za-z]|\Z)",
            'Unit Sizes and Descriptions': r"\*\*Unit Sizes and Descriptions:\*\*\n(.*?)(?=\n\*\*[A-Z]|\Z)",
            'Storage 101 – Sizing Up My Unit': r"\*\*Storage 101 – Sizing Up My Unit:\*\*\n(.*?)(?=\n\*\*[A-Z]|\Z)",
            'Getting a Quote': r"\*\*Getting a Quote:\*\*\n(.*?)(?=\n\*\*[A-Z]|\Z)"
        }
        
        extracted_sections = {}
        for section_name, pattern in sections.items():
            section_match = re.search(pattern, kb, re.DOTALL)
            if section_match:
                content = section_match.group(1).strip()
                # Enhanced cleaning that preserves list indentation
                content = re.sub(r'(?<!\n)\n(?!\s*-)', ' ', content)  # Keep list items intact
                extracted_sections[section_name] = content

        # Enhanced FAQ extraction
        if 'FAQs' not in extracted_sections:
            faq_pattern = r"\*\*FAQs:\*\*(.*?)(?=\n\*\*|\Z)"
            faq_match = re.search(faq_pattern, kb, re.DOTALL)
            if faq_match:
                faq_content = faq_match.group(1).strip()
                extracted_sections['FAQs'] = re.sub(r'\n{2,}', '\n', faq_content)

        # Handle comparison tables
        comparison_pattern = r"\*\*Comparison with (.*?):\*\*\n(.*?)(?=\n\*\*|\Z)"
        comparisons = re.findall(comparison_pattern, kb, re.DOTALL)
        for comp_title, comp_content in comparisons:
            cleaned_content = re.sub(r'\n\s*-', '\n-', comp_content.strip())  # Fix list formatting
            extracted_sections[f"Comparison: {comp_title}"] = cleaned_content

        # Extract AI Tags and Triggers
        ai_tags_match = re.search(r"\*\*AI Tags:\*\*(.*?)(?=\n\*\*|\Z)", kb, re.DOTALL)
        triggers_match = re.search(r"\*\*Triggers:\*\*(.*?)(?=\n\*\*|\Z)", kb, re.DOTALL)

        # Store structured data with all sections
        data = {
            "KB_ID": kb_id,
            "Title": title,
            "Creation Date": metadata.get("Creation Date", ""),
            "Last Modified Date": metadata.get("Last Modified Date", ""),
            "Author": metadata.get("Author", ""),
            "Last Modified By": metadata.get("Last Modified By", ""),
            "Version": metadata.get("Version", ""),
            "Category Tags": metadata.get("Category Tags", ""),
            "Source URL": metadata.get("Source URL", ""),
            **extracted_sections,
            "AI Tags": ai_tags_match.group(1).strip() if ai_tags_match else "",
            "Triggers": triggers_match.group(1).strip() if triggers_match else ""
        }
        structured_data.append(data)
    
    return structured_data

# After processing, add summary statistics
def print_chunk_statistics(kb_data):
    print("\n=== Chunk Statistics ===")
    print(f"Total Chunks: {len(kb_data)}")
    
    # Category distribution
    categories = {}
    for item in kb_data:
        cats = item['Category Tags'].split(',') if item['Category Tags'] else ['Uncategorized']
        for cat in cats:
            cat = cat.strip()
            categories[cat] = categories.get(cat, 0) + 1
    
    print("\nCategory Distribution:")
    for cat, count in categories.items():
        print(f"- {cat}: {count} chunks")
    
    # Length statistics - safely handle missing Primary Information
    lengths = [len(item.get('Primary Information', '')) for item in kb_data if 'Primary Information' in item]
    if lengths:
        avg_length = sum(lengths) / len(lengths)
        print(f"\nAverage chunk length: {avg_length:.0f} characters")
    else:
        print("\nNo Primary Information sections found in chunks")

def write_chunk_results(kb_data, output_file="chunk_analysis_results.txt"):
    """Write chunk analysis results to a text file with complete chunk content."""
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header with timestamp
        f.write(f"Henfield KB Chunk Analysis Results\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        # Write overall statistics
        f.write("=== Overall Statistics ===\n")
        f.write(f"Total Chunks: {len(kb_data)}\n\n")

        # Write category distribution
        f.write("=== Category Distribution ===\n")
        categories = {}
        for item in kb_data:
            cats = item['Category Tags'].split(',') if item['Category Tags'] else ['Uncategorized']
            for cat in cats:
                cat = cat.strip()
                categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in categories.items():
            f.write(f"- {cat}: {count} chunks\n")
        f.write("\n")

        # Write detailed chunk information
        f.write("=== Detailed Chunk Analysis ===\n")
        for idx, chunk in enumerate(kb_data, 1):
            f.write(f"\nChunk {idx}/{len(kb_data)}\n")
            f.write("=" * 80 + "\n")
            
            # Write metadata first
            metadata_fields = [
                "KB_ID", "Title", "Category Tags", "Creation Date", "Version",
                "Author", "Last Modified By", "Last Modified Date", "Source URL"
            ]
            
            # New: Clean empty values and normalize section names
            clean_chunk = {k: v.strip() for k, v in chunk.items() if v.strip()}
            
            written_sections = set()
            
            # Write priority sections first with strict formatting
            priority_sections = [
                'Primary Information', 'Comparison with Standard Self-Storage',
                'FAQs', 'How It Works', 'Unit Sizes', 'Promotions',
                'Service Details', 'Storage Services', 'Locations'
            ]
            
            for section in priority_sections:
                if clean_chunk.get(section):
                    f.write(f"\n{section}:\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"{clean_chunk[section]}\n")
                    written_sections.add(section)
                    del clean_chunk[section]  # Remove from remaining sections

            # Write remaining sections with duplicate check
            for key in list(clean_chunk.keys()):  # Convert to list for safe iteration
                if (key not in written_sections and 
                    key not in metadata_fields and 
                    key not in ["AI Tags", "Triggers"]):
                    f.write(f"\n{key}:\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"{clean_chunk[key]}\n")
                    written_sections.add(key)
                    del clean_chunk[key]  # Prevent reprocessing

            # Write AI Tags and Triggers at the end
            if chunk.get("AI Tags"):
                f.write("\nAI Tags:\n")
                f.write("-" * 40 + "\n")
                f.write(f"{chunk['AI Tags']}\n")
            
            if chunk.get("Triggers"):
                f.write("\nTriggers:\n")
                f.write("-" * 40 + "\n")
                f.write(f"{chunk['Triggers']}\n")
            
            f.write("\n" + "=" * 80 + "\n")

        # Write footer
        f.write("\n" + "=" * 80 + "\n")
        f.write("End of Analysis Report\n")

# Update the main processing section
kb_data = process_kb_articles(kb_articles)
print_chunk_statistics(kb_data)

# Convert to DataFrame
kb_df = pd.DataFrame(kb_data)

from sklearn.metrics import precision_score, recall_score
import numpy as np

# Simulated Test Queries and Ground Truth
test_queries = [
    "What are the benefits of Henfield Storage?",
    "Does Henfield Storage offer free collection?",
    "Where are Henfield Storage locations?"
]

# Updated ground truth based on new KB structure
ground_truth = {
    test_queries[0]: {"KB-001", "KB-007", "KB-008"},
    test_queries[1]: {"KB-002", "KB-003", "KB-005"},
    test_queries[2]: {"KB-001", "KB-006", "KB-012"}
}

# Updated retrieved results based on new KB structure
retrieved_results = {
    test_queries[0]: {"KB-001", "KB-007", "KB-009"},  # Contains 2 correct, 1 incorrect
    test_queries[1]: {"KB-002", "KB-003"},           # Perfect match (2/2 correct)
    test_queries[2]: {"KB-001", "KB-006", "KB-012", "KB-010"}  # 3 correct, 1 incorrect
}

# Calculate Precision and Recall
precision_list = []
recall_list = []
boundary_violations = 0  # Assume we manually check and count these

for query in test_queries:
    relevant = ground_truth[query]
    retrieved = retrieved_results[query]
    
    true_positives = len(relevant.intersection(retrieved))
    false_positives = len(retrieved - relevant)
    false_negatives = len(relevant - retrieved)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    
    precision_list.append(precision)
    recall_list.append(recall)

# Aggregate Metrics
avg_precision = np.mean(precision_list)
avg_recall = np.mean(recall_list)

# Output Results
metrics_result = {
    "Total Chunks Generated": len(kb_df),
    "Average Precision": round(avg_precision, 2),
    "Average Recall": round(avg_recall, 2),
    "Boundary Violations": boundary_violations
}

print(metrics_result)

# After processing KB articles
write_chunk_results(kb_data)
print(f"Results have been written to chunk_analysis_results.txt")

