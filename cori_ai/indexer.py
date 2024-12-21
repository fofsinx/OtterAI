import os
from typing import Dict, List, Optional
from pathlib import Path
import fnmatch
from langchain.prompts import ChatPromptTemplate
import asyncio
import aiofiles
from cori_ai.llm_client import LLMClient

def should_ignore_file(file_path: str) -> bool:
    """Check if file should be ignored in indexing."""
    ignore_patterns = [
        '*.pyc', '__pycache__/*', '.git/*', '.github/*', 'node_modules/*',
        '*.min.js', '*.min.css', '*.map', '*.lock', '*.sum',
        'dist/*', 'build/*', '.env*', '*.log',
        # Swift specific
        '*.xcodeproj/*', '*.xcworkspace/*', 'Pods/*', '*.xcuserstate',
        # Flutter specific
        '.dart_tool/*', '.flutter-plugins', '.flutter-plugins-dependencies',
        # Go specific
        '*go.mod', 'go.sum',
        # Android specific
        'android/*', 'ios/*', 'ios/Pods/*', 'android/.gradle/*',
        # Rust specific
        'Cargo.lock', 'Cargo.toml', '*.rs', '*.toml', '*.lock', '*.lock',
        # Kotlin specific
        '*.kt', '*.kts', '*.gradle', '*.gradlew', '*.gradlew.bat', '*.gradle.kts',
        # Java specific 
        '*.java', '*.class', '*.jar', '*.war', '*.ear', '*.gradle', '*.gradlew', '*.gradlew.bat', '*.gradle.kts',
        # C# specific
        '*.cs', '*.dll', '*.exe', '*.pdb', '*.csproj', '*.sln', '*.config', '*.props', '*.targets', '*.nuspec', '*.nupkg', '*.csproj.user', '*.csproj.vspscc', '*.csproj.vssscc', '*.csproj.webinfo', '*.csproj.user', '*.csproj.vspscc', '*.csproj.vssscc', '*.csproj.webinfo',
        # PHP specific
        '*.php', '*.php3', '*.php4', '*.php5', '*.php7', '*.phps', '*.phpt', '*.phtml', '*.inc', '*.module', '*.profile', '*.engine', '*.engine.php', '*.engine.inc', '*.engine.module', '*.engine.profile', '*.engine.inc', '*.engine.module', '*.engine.profile',
    ]
    return any(fnmatch.fnmatch(file_path, pattern) for pattern in ignore_patterns)

def get_file_type(file_path: str) -> Optional[str]:
    """Get the type of file based on extension and content."""
    ext = Path(file_path).suffix.lower()
    if ext in ['.py', '.js', '.ts', '.java', '.cpp', '.go', '.rs', '.swift', '.dart', '.flutter']:
        return 'source'
    elif ext in ['.md', '.txt', '.rst', '.markdown']:
        return 'documentation'
    elif ext in ['.json', '.yaml', '.yml', '.toml']:
        return 'config'
    elif ext in ['.html', '.css', '.scss', '.less', '.vue', '.svelte', '.astro', '.jsx', '.tsx']:
        return 'frontend'
    elif ext in ['.sql', '.graphql']:
        return 'data'
    elif ext in ['.test.js', '.test.ts', '.spec.py', '_test.go', '.spec.js', '.spec.ts', '.test.dart', '.test.swift', '.test.py', '.test.java', '.test.cpp', '.test.go', '.test.rs', '.test.swift', '.test.dart', '.test.flutter']:
        return 'test'
    elif ext in ['.env', '.env.*', '.env.local', '.env.development', '.env.production', '.env.staging', '.env.test', '.env.development.local', '.env.production.local', '.env.staging.local', '.env.test.local']:
        return 'environment'
    elif ext in ['.gitignore', '.dockerignore']:
        return 'ignore'
    elif ext in ['.git', '.github']:
        return 'git'
    elif ext in ['.github']:
        return 'github'
    elif ext in ['.dockerfile', '.dockerignore', '.docker-compose.yml', '.docker-compose.yaml', '.docker-compose.toml']:
        return 'docker'
    elif ext in ['.npmrc', '.yarnrc', '.yarnrc.yml', '.yarnrc.yaml', '.yarnrc.json', '.yarnrc.toml', '.yarnrc.yaml', '.yarnrc.yml']:
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
        ("system", """You are a technical architect analyzing a codebase structure.
Create a concise but comprehensive overview of the project structure and guidelines.
Focus on:
1. Project organization and architecture
2. Key components and their relationships
3. Coding standards and patterns observed
4. Important dependencies and configurations
5. Testing approach
6. File types and their purpose
 
Steps:
1. Read the codebase structure
2. Read the key files' content
3. Generate the analysis
4. Strictly check which language is used in the codebase; do not mention any other language if not specified.
5. Follow the best practices for the language used in the codebase.

Do not use any other language than English. Do not leak any sensitive information.

Keep the response focused and actionable for code review purposes."""),
        ("human", """Here's the codebase structure:

{index_summary}

Key files content:
{key_files_content}
""")
    ])
    
    # Read content of key files asynchronously
    key_files = []
    tasks = []
    key_file_paths = [os.path.join(repo_root, 'README.md'), os.path.join(repo_root, '.editorconfig')]
    
    async def read_file(file_path: str):
        if os.path.exists(file_path):
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                key_files.append((os.path.basename(file_path), content))
    
    for file_path in key_file_paths:
        tasks.append(read_file(file_path))
    
    await asyncio.gather(*tasks)
    
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
    
    response = llm.invoke(prompt.format(
        index_summary="\n".join(index_summary),
        key_files_content="\n".join(key_files_content)
    ))
    
    return response.content

def generate_review_context(repo_root: str) -> str:
    """Generate the complete context for code review."""
    index = index_codebase(repo_root)
    analysis = asyncio.run(analyze_project_structure(index, repo_root))
    
    return f"""PROJECT CONTEXT AND GUIDELINES

{analysis}

When reviewing code changes, ensure they align with the project structure and guidelines outlined above.
Focus on maintaining consistency with the existing patterns while suggesting improvements where appropriate.""" 