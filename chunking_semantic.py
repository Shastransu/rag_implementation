import spacy
import re

# Load a pre-trained NLP model
nlp = spacy.load("en_core_web_sm")

def semantic_chunking(text, max_sentences=5):
    """Chunk text into semantically meaningful sections."""
    doc = nlp(text)
    chunks = []
    current_chunk = []

    for sent in doc.sents:
        current_chunk.append(sent.text)
        if len(current_chunk) >= max_sentences:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def enhanced_semantic_chunking(text, max_sentences=5):
    """Chunk text using both semantic and syntactic features."""
    doc = nlp(text)
    chunks = []
    current_chunk = []

    for sent in doc.sents:
        # Use dependency parsing or named entity recognition
        if len(current_chunk) < max_sentences:
            current_chunk.append(sent.text)
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sent.text]

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def advanced_chunking(text, max_sentences=5):
    """Chunk text using advanced NLP techniques."""
    doc = nlp(text)
    chunks = []
    current_chunk = []

    for sent in doc.sents:
        # Use named entity recognition to prioritize sentences
        if len(current_chunk) < max_sentences or any(ent.label_ in ['ORG', 'GPE'] for ent in sent.ents):
            current_chunk.append(sent.text)
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sent.text]

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

def evaluate_chunks(chunks, original_content):
    """Evaluate the quality of the chunks."""
    if not chunks:
        raise ValueError("No chunks generated - check document content and splitters")
    
    test_queries = {
        "KB-001 locations": r"BN1\s*8AF",
        "click+store access": r"2\s*days['']?\s*notice",
        "free collection size": r"15\s*sq\s*ft\s*to\s*250\s*sq\s*ft"
    }
    
    metrics = {
        'avg_precision': 0,
        'avg_recall': 0,
        'boundary_violations': 0,
        'avg_length': sum(len(c) for c in chunks) // len(chunks),
        'total_chunks': len(chunks)
    }
    
    precision_scores = []
    recall_scores = []
    
    for query, pattern in test_queries.items():
        total_relevant = len(re.findall(pattern, original_content, re.IGNORECASE))
        if total_relevant == 0:
            print(f"Critical Error: Test answer '{query}' not found in original content")
            return {'avg_precision': 0, 'avg_recall': 0, 'boundary_violations': 0}
            
        relevant_chunks = [c for c in chunks if re.search(pattern, c, re.IGNORECASE)]
        found_matches = len(relevant_chunks)
        
        precision = min(found_matches / len(chunks), 1.0) if chunks else 0
        recall = min(found_matches / total_relevant, 1.0)
        
        precision_scores.append(precision)
        recall_scores.append(recall)
    
    if precision_scores and recall_scores:
        metrics['avg_precision'] = sum(precision_scores) / len(precision_scores)
        metrics['avg_recall'] = sum(recall_scores) / len(recall_scores)
    
    return metrics

def find_optimal_chunking(file_path):
    """Determine the best chunking configuration."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    required_answers = [
        r"BN1\s*8AF",
        r"2\s*days['']?\s*notice",
        r"15\s*sq\s*ft\s*to\s*250\s*sq\s*ft"
    ]
    for pattern in required_answers:
        if not re.search(pattern, content, re.IGNORECASE):
            raise ValueError(f"Test answer pattern '{pattern}' not found in document")

    configs = [
        (5, 0),  # 5 sentences per chunk
        (10, 0),  # 10 sentences per chunk
        (15, 0),  # 15 sentences per chunk
        (15,4),
        (18,0),
        (20,0),
        (20,3),
        (25,0),
        (30,0),
        (50,0)
    ]
    
    best_score = -1
    best_config = None
    
    for max_sentences, _ in configs:
        try:
            # Use the advanced chunking function
            chunks = advanced_chunking(content, max_sentences=max_sentences)
            chunks = [c for c in chunks if c.strip()]
            
            print(f"\nTesting config: max_sentences={max_sentences}")  # Debug print
            print(f"Generated {len(chunks)} chunks")  # Debug print
            
            if not chunks:
                print("Skipped config with 0 chunks")  # Debug print
                continue
                
            metrics = evaluate_chunks(chunks, content)
            
            print(f"Precision: {metrics['avg_precision']:.2f}, Recall: {metrics['avg_recall']:.2f}")
            print(f"Boundary violations: {metrics['boundary_violations']}")
            
            precision = metrics['avg_precision']
            recall = metrics['avg_recall']
            
            # Maintain a higher precision threshold
            if precision < 0.1:
                print("Skipped config with low precision")  # Debug print
                continue
                
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            score = f1_score - (0.05 * metrics['boundary_violations'])

            if score > best_score:
                best_score = score
                best_config = (max_sentences, metrics)
                
        except Exception as e:
            print(f"Config (max_sentences={max_sentences}) failed: {str(e)}")
            continue

    if not best_config:
        raise ValueError("No valid configurations. Check document structure and test patterns.")
    
    print(f"\n{' Optimal Configuration ':=^60}")
    print(f"Max Sentences: {best_config[0]}")
    print(f"Precision: {best_config[1]['avg_precision']:.2f}, Recall: {best_config[1]['avg_recall']:.2f}")
    print(f"Boundary Violations: {best_config[1]['boundary_violations']}")
    print(f"Avg Chunk Length: {best_config[1]['avg_length']} chars")
    
    return best_config

# Run optimization
if __name__ == "__main__":
    optimal_config = find_optimal_chunking(r'henfield_kb_articles (3).md')
    
    # Print the optimal configuration
    print(f"Optimal Max Sentences: {optimal_config[0]}")
    print(f"Precision: {optimal_config[1]['avg_precision']:.2f}, Recall: {optimal_config[1]['avg_recall']:.2f}")
    print(f"Boundary Violations: {optimal_config[1]['boundary_violations']}")
    print(f"Avg Chunk Length: {optimal_config[1]['avg_length']} chars")