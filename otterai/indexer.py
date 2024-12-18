import os
from typing import Dict, List, Optional
from pathlib import Path
import fnmatch
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import httpx
import asyncio
import aiofiles
from otterai.llm_client import LLMClient
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
    elif ext in ['.test.js', '.test.ts', '.spec.py', '_test.go', '.spec.js', '.spec.ts']:
        return 'test'
    elif ext in ['.env', '.env.*']:
        return 'environment'
    elif ext in ['.gitignore', '.dockerignore']:
        return 'ignore'
    elif ext in ['.git', '.github']:
        return 'git'
    elif ext in ['.github']:
        return 'github'
    elif ext in ['.dockerfile', '.dockerignore', '.docker-compose.yml', '.docker-compose.yaml', '.docker-compose.toml']:
        return 'docker'
    elif ext in ['.npmrc', '.yarnrc', '.yarnrc.yml', '.yarnrc.yaml', '.yarnrc.json', '.yarnrc.toml']:
        return 'npm'
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
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, root_dir)
            
            if should_ignore_file(rel_path):
                print(f"Ignoring file: {file} because it matches ignore patterns.")
                continue
                
            file_type = get_file_type(rel_path) or 'other'
            index[file_type].append(rel_path)
    
    return index

async def analyze_project_structure(index: Dict[str, List[str]], repo_root: str) -> str:
    """Generate a high-level analysis of the project structure."""
    llm_client = LLMClient()
    llm = llm_client.get_client()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a technical architect analyzing a codebase