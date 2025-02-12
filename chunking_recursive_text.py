## Using CAG to generate a semantic search engine

from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

# Updated configuration for better alignment with document structure
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # Larger chunk size to capture full sections
    chunk_overlap=100,  # Minimal overlap to reduce redundancy
    separators=[
        r"\n={80}\n",  # Exact match for 80 equals signs line
        r"^####\s*KB-\d{3}:",  # Match section headers
        "\n\n",  # Paragraph breaks
        "\n",  # Line breaks
        " ",  # Spaces
        ""  # Fallback
    ],
    length_function=lambda x: len(x.splitlines()),  # Custom length function
    is_separator_regex=True,
)

def chunk_kb_articles(file_path):
    with open(file_path, 'r') as file:
        kb_content = file.read()
    
    # Split documents while preserving metadata structure
    chunks = text_splitter.create_documents([kb_content])
    
    # Filter out empty chunks
    return [c for c in chunks if c.page_content.strip()]

def evaluate_chunks(chunks, original_content):
    """Improved boundary checking"""
    if not chunks:
        raise ValueError("No chunks generated - check document content and splitters")
    
    # Test queries with flexible matching
    test_queries = {
        "KB-001 locations": r"BN1\s*8AF",
        "click+store access": r"2\s*days['']?\s*notice",
        "free collection size": r"15\s*sq\s*ft\s*to\s*250\s*sq\s*ft"
    }
    
    # Metrics tracking
    metrics = {
        'avg_precision': 0,
        'avg_recall': 0,
        'boundary_violations': 0,
        'avg_length': sum(len(c.page_content) for c in chunks) // len(chunks),
        'total_chunks': len(chunks)
    }
    
    # Reset boundary checking
    current_article = None
    for chunk in chunks:
        content = chunk.page_content
        # Check if starts with article header
        if re.match(r"^#### KB-\d{3}:", content):
            current_article = content[:15]  # Store article ID
        # If we're inside an article but chunk doesn't start with header
        elif current_article and not content.startswith("####"):
            metrics['boundary_violations'] += 1

    # Precision/recall calculation
    precision_scores = []
    recall_scores = []
    
    for query, pattern in test_queries.items():
        # Find ALL matches in original content first
        total_relevant = len(re.findall(pattern, original_content, re.IGNORECASE))
        if total_relevant == 0:
            print(f"Critical Error: Test answer '{query}' not found in original content")
            return {'avg_precision': 0, 'avg_recall': 0, 'boundary_violations': 0}  # Fail fast
            
        # Find chunks containing AT LEAST ONE match
        relevant_chunks = [c for c in chunks if re.search(pattern, c.page_content, re.IGNORECASE)]
        found_matches = len(relevant_chunks)
        
        # Prevent division errors and cap recall at 1.0
        precision = min(found_matches / len(chunks), 1.0) if chunks else 0
        recall = min(found_matches / total_relevant, 1.0)  # Cap recall at 100%
        
        precision_scores.append(precision)
        recall_scores.append(recall)
    
    if precision_scores and recall_scores:
        metrics['avg_precision'] = sum(precision_scores) / len(precision_scores)
        metrics['avg_recall'] = sum(recall_scores) / len(recall_scores)
    
    return metrics

def find_optimal_chunking(file_path):
    """Automatically determine best chunking configuration"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Validate test answers exist
    required_answers = [
        r"BN1\s*8AF",
        r"2\s*days['']?\s*notice",
        r"15\s*sq\s*ft\s*to\s*250\s*sq\s*ft"
    ]
    for pattern in required_answers:
        if not re.search(pattern, content, re.IGNORECASE):
            raise ValueError(f"Test answer pattern '{pattern}' not found in document")

    # Test configurations
    configs = [
        (1000, 100, r"\n={80}\n"),  # Larger chunk size with minimal overlap
        (800, 100, r"\n={80}\n"),  # Even larger chunk size
        (600, 50, r"\n={80}\n"),  # Moderate chunk size
        (400, 50, r"\n={80}\n"),  # Smaller chunk size
    ]
    
    best_score = -1
    best_config = None
    
    for size, overlap, sep in configs:
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=size,
                chunk_overlap=overlap,
                separators=[sep, "\n#### ", "\n\n", "\n", " ", ""],
                is_separator_regex=True
            )
            chunks = splitter.create_documents([content])
            chunks = [c for c in chunks if c.page_content.strip()]
            
            print(f"\nTesting config: size={size}, overlap={overlap}")  # Debug print
            print(f"Generated {len(chunks)} chunks")  # Debug print
            
            if not chunks:
                print("Skipped config with 0 chunks")  # Debug print
                continue
                
            metrics = evaluate_chunks(chunks, content)
            
            # Add debug prints for metrics
            print(f"Precision: {metrics['avg_precision']:.2f}, Recall: {metrics['avg_recall']:.2f}")
            print(f"Boundary violations: {metrics['boundary_violations']}")
            
            # Calculate weighted score with safety check
            precision = metrics['avg_precision']
            recall = metrics['avg_recall']
            
            if precision + recall == 0:
                print("Skipped config with 0 precision and recall")  # Debug print
                continue
                
            # Adjust the scoring logic
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            # Consider reducing the penalty for boundary violations
            score = f1_score - (0.05 * metrics['boundary_violations'])  # Reduced penalty

            # Allow configurations with high recall
            if precision > 0.1 and score > best_score:  # Ensure precision is above a threshold
                best_score = score
                best_config = (size, overlap, metrics)
                
        except Exception as e:
            print(f"Config ({size},{overlap}) failed: {str(e)}")
            continue

    if not best_config:
        raise ValueError("No valid configurations. Check document structure and test patterns.")
    
    # Print results
    print(f"\n{' Optimal Configuration ':=^60}")
    print(f"Chunk Size: {best_config[0]}, Overlap: {best_config[1]}")
    print(f"Precision: {best_config[2]['avg_precision']:.2f}, Recall: {best_config[2]['avg_recall']:.2f}")
    print(f"Boundary Violations: {best_config[2]['boundary_violations']}")
    print(f"Avg Chunk Length: {best_config[2]['avg_length']} chars")
    
    return best_config

# Run optimization
if __name__ == "__main__":
    optimal_config = find_optimal_chunking(r'henfield_kb_articles (3).md')
    
    # Update text splitter with optimal config
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=optimal_config[0],
        chunk_overlap=optimal_config[1],
        separators=[r"\n={80}\n", "\n#### ", "\n\n", "\n", " ", ""],
        is_separator_regex=True
    )

    # Print the optimal configuration
    print(f"Optimal Chunk Size: {optimal_config[0]}, Overlap: {optimal_config[1]}")
    print(f"Precision: {optimal_config[2]['avg_precision']:.2f}, Recall: {optimal_config[2]['avg_recall']:.2f}")
    print(f"Boundary Violations: {optimal_config[2]['boundary_violations']}")
    print(f"Avg Chunk Length: {optimal_config[2]['avg_length']} chars")


