import os
from typing import Dict, List, Optional
from pathlib import Path
import fnmatch
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import httpx

def should_ignore_file(file_path: str) -> bool:
    """Check if file should be ignored in indexing."""
    ignore_patterns = [
        '*.pyc', '__pycache__/*', '.git/*', '.github/*', 'node_modules/*',
        '*.min.js', '*.min.css', '*.map', '*.lock', '*.sum',
        'dist/*', 'build/*', '.env*', '*.log'
    ]
    return any(fnmatch.fnmatch(file_path, pattern) for pattern in ignore_patterns)

def get_file_type(file_path: str) -> Optional[str]:
    """Get the type of file based on extension and content."""
    ext = Path(file_path).suffix.lower()
    if ext in ['.py', '.js', '.ts', '.java', '.cpp', '.go', '.rs']:
        return 'source'
    elif ext in ['.md', '.txt', '.rst']:
        return 'documentation'
    elif ext in ['.json', '.yaml', '.yml', '.toml']:
        return 'config'
    elif ext in ['.html', '.css', '.scss', '.less']:
        return 'frontend'
    elif ext in ['.sql', '.graphql']:
        return 'data'
    elif ext in ['.test.js', '.test.ts', '.spec.py', '_test.go']:
        return 'test'
    return None

def index_codebase(root_dir: str) -> Dict[str, List[str]]:
    """Create an index of the codebase organized by file type."""
    index: Dict[str, List[str]] = {
        'source': [],
        'documentation': [],
        'config': [],
        'frontend': [],
        'data': [],
        'test': [],
        'other': []
    }

    default_ignore_patterns = [
        '*.pyc', '__pycache__/*', '.git/*', '.github/*', 'node_modules/*',
        '*.min.js', '*.min.css', '*.map', '*.lock', '*.sum',
        'dist/*', 'build/*', '.env*', '*.log',
        '*venv/*', '*.venv/*', '*.venv', 'venv/*', 'venv', '*.venv',
        '*.pyc', '__pycache__/*', '.git/*', '.github/*', 'node_modules/*',
    ]
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            for pattern in default_ignore_patterns:
                if fnmatch.fnmatch(file, pattern):
                    print(f"Ignoring file: {file} because it matches pattern: {pattern}")
                    continue
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, root_dir)
            
            if should_ignore_file(rel_path):
                continue
                
            file_type = get_file_type(rel_path) or 'other'
            index[file_type].append(rel_path)
    
    return index

def analyze_project_structure(index: Dict[str, List[str]], repo_root: str) -> str:
    """Generate a high-level analysis of the project structure."""
    llm = ChatOpenAI(
        model_name=os.getenv('INPUT_MODEL', 'gpt-4-turbo-preview'),
        http_async_client=httpx.AsyncClient(timeout=10.0),
        api_key=os.getenv('INPUT_OPENAI_API_KEY'),
        base_url=os.getenv('INPUT_OPENAI_BASE_URL', 'https://api.openai.com/v1'),
        temperature=0.1
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a technical architect analyzing a codebase structure.
        Create a concise but comprehensive overview of the project structure and guidelines.
        Focus on:
        1. Project organization and architecture
        2. Key components and their relationships
        3. Coding standards and patterns observed
        4. Important dependencies and configurations
        5. Testing approach
         
         steps:
         1. read the codebase structure
         2. read the key files content
         3. generate the analysis
         4. Strictly check which language is used in the codebase do not any other language if not specified in the codebase.

         I'll give you billion dollars if you do follow this instruction.
        
        Keep the response focused and actionable for code review purposes."""),
        ("human", """Here's the codebase structure:
        
        {index_summary}
        
        Key files content:
        {key_files_content}
        """)
    ])
    
    # Read content of key files
    key_files = []
    if os.path.exists(os.path.join(repo_root, 'README.md')):
        with open(os.path.join(repo_root, 'README.md'), 'r') as f:
            key_files.append(('README.md', f.read()))
            
    if os.path.exists(os.path.join(repo_root, '.editorconfig')):
        with open(os.path.join(repo_root, '.editorconfig'), 'r') as f:
            key_files.append(('.editorconfig', f.read()))
            
    # Format index summary
    index_summary = []
    for file_type, files in index.items():
        if files:
            index_summary.append(f"\n{file_type.upper()} FILES:")
            for file in sorted(files):
                index_summary.append(f"- {file}")
    
    # Format key files content
    key_files_content = []
    for filename, content in key_files:
        key_files_content.append(f"\n=== {filename} ===\n{content}")
    
    result = llm.invoke(prompt.format(
        index_summary="\n".join(index_summary),
        key_files_content="\n".join(key_files_content)
    ))
    
    return result.content

def generate_review_context(repo_root: str) -> str:
    """Generate the complete context for code review."""
    index = index_codebase(repo_root)
    analysis = analyze_project_structure(index, repo_root)
    
    return f"""PROJECT CONTEXT AND GUIDELINES

{analysis}

When reviewing code changes, ensure they align with the project structure and guidelines outlined above.
Focus on maintaining consistency with the existing patterns while suggesting improvements where appropriate.""" 