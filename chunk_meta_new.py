import re
import pandas as pd
from datetime import datetime

# Reload the document
kb_file_path = "henfiled_KB_V2.md"
with open(kb_file_path, "r", encoding="utf-8") as file:
    kb_content = file.read()

# Extract all KB sections dynamically
kb_pattern = re.compile(r"(#### KB-\d+:.*?)(?=#### KB-\d+:|\Z)", re.DOTALL)
kb_articles = kb_pattern.findall(kb_content)

# Add after line 12 (after kb_articles extraction)
TEST_QUERIES = [
    ("What is the free collection policy?", r"free collection service.*?3[- ]?month"),
    ("Where is the Brighton location?", r"Brighton.*?BN1 8AF"),
    ("What are the business storage unit sizes?", r"(?s)Unit Sizes and Descriptions::.*?(\d+ sq ft Room \(.*?\))|(\d+ sq ft Locker \(.*?\))"),
    ("What's the price match guarantee?", r"price match guarantee"),
    ("What are the security features?", r"24/7 CCTV|security fencing|alarms"),
    ("How does Click+Store work?", r"Click\+Store.*?store without leaving home"),
    ("What items are prohibited?", r"prohibited items.*?(vehicles|perishables|illegal)"),
    ("What's the minimum storage period?", r"minimum.*?\d+ month"),
    ("Do you offer student storage?", r"student storage"),
    ("What insurance is required?", r"insurance.*?mandatory"),
    ("How to access after hours?", r"access.*?opening hours"),
    ("What payment methods are accepted?", r"payment methods.*?(direct debit|credit card)"),
    ("Are pets allowed?", r"pets (not permitted|allowed)"),
    ("What's the deposit amount?", r"deposit.*?one month's rent"),
    ("How to change unit size?", r"change unit size"),
    ("What's included in free collection?", r"free collection.*?(van|driver|loading)"),
    ("COVID safety measures?", r"COVID.*?(mask|sanitizer|distancing)"),
    ("Vehicle storage policy?", r"vehicles (not allowed|prohibited)"),
    ("Temperature controlled units?", r"temperature controlled.*?No"),
    ("How to get a quote?", r"get a quote.*?\d+")
]

# Function to properly process KB articles and remove duplication
def process_and_clean_kb_articles(kb_articles):
    structured_data = []

    for kb in kb_articles:
        # Extract KB ID and Title
        kb_id_match = re.search(r"#### (KB-\d+): (.+)", kb)
        kb_id = kb_id_match.group(1) if kb_id_match else "Unknown"
        title = kb_id_match.group(2) if kb_id_match else "Unknown"

        # Extract metadata
        metadata_pattern = r"- \*\*([^:]+):\*\* (.*)"
        metadata = dict(re.findall(metadata_pattern, kb))

        # Extract all sections dynamically
        section_pattern = re.compile(r"\*\*(.+?)\*\*\s*\n(.*?)(?=\n\*\*|\Z)", re.DOTALL)
        extracted_sections = {match[0].strip(): match[1].strip() for match in section_pattern.findall(kb)}

        # Clean and structure extracted sections properly
        cleaned_sections = {}
        for section_name, content in extracted_sections.items():
            # Merge multi-line lists into properly formatted bullet points
            formatted_content = re.sub(r'(?<!\n)\n(?!\s*-)', ' ', content.strip())
            cleaned_sections[section_name] = {
                'content': formatted_content,
                'word_count': len(formatted_content.split()),
            }

        # Extract AI Tags and Triggers correctly
        ai_tags_match = re.search(r"\*\*AI Tags:\*\*\s*(.*?)\n", kb, re.DOTALL)
        triggers_match = re.search(r"\*\*Triggers:\*\*\s*(.*?)\n", kb, re.DOTALL)

        structured_data.append({
            "KB_ID": kb_id,
            "Title": title,
            "Creation Date": metadata.get("Creation Date", ""),
            "Last Modified Date": metadata.get("Last Modified Date", ""),
            "Author": metadata.get("Author", ""),
            "Last Modified By": metadata.get("Last Modified By", ""),
            "Version": metadata.get("Version", ""),
            "Category Tags": metadata.get("Category Tags", ""),
            "Source URL": metadata.get("Source URL", ""),
            **cleaned_sections,  # Add all properly formatted sections dynamically
            "AI Tags": ai_tags_match.group(1).strip() if ai_tags_match else "",
            "Triggers": triggers_match.group(1).strip() if triggers_match else "",
        })

    return structured_data

# Process the KB data with the fix
fixed_kb_data = process_and_clean_kb_articles(kb_articles)

# Add this section to print first chunk
if fixed_kb_data:
    print("\n=== FIRST CHUNK PREVIEW ===")
    first_chunk = fixed_kb_data[0]
    for key, value in first_chunk.items():
        print(f"\n{key}:\n{'-'*40}")
        print(value[:500] + "..." if len(value) > 500 else value)  # Show first 500 chars
    print("\n" + "="*80 + "\n")

# Save properly formatted output
def save_cleaned_results(kb_data, output_file="chunk_analysis_results_fixed.txt"):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Henfield KB Chunk Analysis Results\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        for idx, chunk in enumerate(kb_data, 1):
            f.write(f"Chunk {idx}/{len(kb_data)}\n")
            f.write("=" * 80 + "\n")
            for key, value in chunk.items():
                f.write(f"\n{key}:\n{'-' * 40}\n{value}\n")
            f.write("\n" + "=" * 80 + "\n")

    return output_file

# Add after process_and_clean_kb_articles function
def evaluate_chunk_quality(kb_data, original_content):
    """Evaluate chunk quality using test queries and patterns."""
    evaluation_results = []
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    boundary_violations = 0
    partial_matches = 0
    multi_chunk_answers = 0
    
    print("\n=== Starting Chunk Quality Evaluation ===")
    
    # Create answer bank from original content
    answer_bank = {}
    for query, pattern in TEST_QUERIES:
        matches = re.findall(pattern, original_content, re.DOTALL | re.IGNORECASE)
        answer_bank[query] = bool(matches)

    # Test each query against chunks
    for query, pattern in TEST_QUERIES:
        found = False
        source_chunks = []
        
        for chunk in kb_data:
            # Properly handle both string and dictionary values
            content = "\n".join(
                str(v) if not isinstance(v, dict) else v['content']
                for v in chunk.values()
            )
            if re.search(pattern, content, re.IGNORECASE):
                found = True
                source_chunks.append(chunk['KB_ID'])

        expected_answer = answer_bank.get(query, False)
        
        # Update confusion matrix
        if expected_answer:
            if found:
                true_positives += 1
                # Check if answer requires multiple chunks
                if len(source_chunks) > 1:
                    # FIX: Use the original pattern instead of matched text
                    any_full = any(
                        re.search(pattern, "\n".join(
                            str(v) if not isinstance(v, dict) else v['content']
                            for v in chunk.values()
                        ), re.DOTALL|re.IGNORECASE)
                        for chunk in kb_data
                    )
                    if not any_full:
                        multi_chunk_answers += 1
                        boundary_violations += 1
            else:
                false_negatives += 1
        else:
            if found:
                false_positives += 1

        evaluation_results.append({
            'query': query,
            'found': found,
            'source_chunks': ", ".join(source_chunks),
            'expected_answer': expected_answer
        })

    # Calculate metrics
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'evaluation_results': evaluation_results,
        'metrics': {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'total_questions': len(TEST_QUERIES),
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'answerable_questions': sum(answer_bank.values())
        },
        'boundary_metrics': {
            'boundary_violations': boundary_violations,
            'multi_chunk_answers': multi_chunk_answers,
            'partial_matches': partial_matches,
            'overretrieval_cases': sum(len(r['source_chunks']) > 1 
                                     for r in evaluation_results),
            'fragmentation_score': multi_chunk_answers/len(TEST_QUERIES)
        }
    }

# Add this ABOVE the main block
def save_evaluation_results(evaluation_data, output_file="chunk_metrics_evaluation.txt"):
    """Save evaluation results to file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Chunk Metrics Evaluation Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        # Write metrics
        metrics = evaluation_data['metrics']
        f.write("Overall Metrics:\n")
        f.write(f"- Precision: {metrics['precision']:.2%}\n")
        f.write(f"- Recall: {metrics['recall']:.2%}\n")
        f.write(f"- F1 Score: {metrics['f1_score']:.2%}\n")
        f.write(f"- Correct Answers: {metrics['true_positives']}/{metrics['total_questions']}\n")
        f.write(f"- Answerable Questions: {metrics['answerable_questions']}\n\n")
        
        # Add boundary metrics section
        boundary = evaluation_data['boundary_metrics']
        f.write("Boundary Metrics:\n")
        f.write(f"- Boundary Violations: {boundary['boundary_violations']} (answers split across chunks)\n")
        f.write(f"- Multi-chunk Answers: {boundary['multi_chunk_answers']}\n")
        f.write(f"- Partial Matches: {boundary['partial_matches']}\n")
        f.write(f"- Over-retrieval Cases: {boundary['overretrieval_cases']}\n")
        f.write(f"- Fragmentation Score: {boundary['fragmentation_score']:.2%}\n\n")
        
        # Write detailed results
        f.write("Detailed Question Results:\n")
        for result in evaluation_data['evaluation_results']:
            status = "FOUND" if result['found'] else "MISSED"
            f.write(f"\nQuestion: {result['query']}\n")
            f.write(f"Status: {status}\n")
            f.write(f"Expected Answer: {'Present' if result['expected_answer'] else 'Not Present'}\n")
            if result['source_chunks']:
                f.write(f"Source Chunks: {result['source_chunks']}\n")
            f.write("-"*60 + "\n")

    return output_file

# Add this function after the save_cleaned_results function
def print_chunk(kb_data, chunk_index=0):
    """Print a specific chunk in readable format."""
    if chunk_index >= len(kb_data):
        print(f"Chunk index {chunk_index} out of range (total chunks: {len(kb_data)})")
        return
    
    chunk = kb_data[chunk_index]
    print(f"\n=== CHUNK {chunk_index+1} ===")
    print(f"KB ID: {chunk['KB_ID']}")
    print(f"Title: {chunk['Title']}")
    
    # Print all sections dynamically
    for key, value in chunk.items():
        if key not in ['KB_ID', 'Title']:
            print(f"\n{key}:")
            print("-"*40)
            if isinstance(value, dict):
                print(f"Content: {value['content'][:500]}...")
                print(f"Word Count: {value['word_count']}")
            else:
                print(str(value)[:500] + "..." if len(str(value)) > 500 else str(value))
    
    print("\n" + "="*80 + "\n")

# Modify after line 61 (after processing KB data)
if __name__ == "__main__":
    # Process KB data
    fixed_kb_data = process_and_clean_kb_articles(kb_articles)
    
    # Print first chunk preview
    if fixed_kb_data:
        print("\n=== FIRST CHUNK PREVIEW ===")
        first_chunk = fixed_kb_data[0]
        for key, value in first_chunk.items():
            print(f"\n{key}:\n{'-'*40}")
            print(value[:500] + "..." if len(value) > 500 else value)
        print("\n" + "="*80 + "\n")
    
    # Run evaluation
    evaluation_data = evaluate_chunk_quality(fixed_kb_data, kb_content)
    
    # Save evaluation results
    metrics_file = save_evaluation_results(evaluation_data)
    print(f"\nMetrics evaluation saved to: {metrics_file}")
    
    # Save cleaned results
    fixed_output_file = save_cleaned_results(fixed_kb_data)

    # Print first chunk with full details
    print_chunk(fixed_kb_data, 0)  # Change the index to print different chunks

# # Convert fixed data to DataFrame and display to user
# fixed_kb_df = pd.DataFrame(fixed_kb_data)
# import ace_tools as tools
# tools.display_dataframe_to_user(name="Fixed KB Data", dataframe=fixed_kb_df)
