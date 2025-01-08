"""Code indexing and analysis module for cori_ai."""
import os
import fnmatch
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set
import asyncio
import aiofiles

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks import StdOutCallbackHandler

from otterai.core.config import settings, callback_manager
from otterai.llm import get_provider


class ProjectAnalysis(BaseModel):
    """Project analysis output schema."""
    project_type: str = Field(description="Type of the project (e.g., library, application, framework)")
    languages: List[str] = Field(description="Programming languages used in the project")
    architecture: Dict[str, Any] = Field(description="Architecture analysis including patterns and components")
    dependencies: Dict[str, List[str]] = Field(description="Project dependencies categorized by type")
    testing: Dict[str, Any] = Field(description="Testing approach and coverage")
    documentation: Dict[str, Any] = Field(description="Documentation quality and coverage")
    security: Dict[str, Any] = Field(description="Security analysis and concerns")
    performance: Dict[str, Any] = Field(description="Performance analysis and bottlenecks")
    recommendations: List[Dict[str, str]] = Field(description="Improvement recommendations")


class DependencyGraph(BaseModel):
    """Dependency graph output schema."""
    nodes: Dict[str, Set[str]] = Field(default_factory=dict, description="Map of files to their dependencies")
    file_types: Dict[str, str] = Field(default_factory=dict, description="Map of files to their types")
    imports: Dict[str, List[str]] = Field(default_factory=dict, description="Map of files to their imports")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Map of files to their dependencies")
    metadata: Dict[str, Dict] = Field(default_factory=dict, description="Additional metadata about files")
    edges: List[Dict[str, str]] = Field(default_factory=list, description="Dependencies between nodes")
    clusters: List[Dict[str, Any]] = Field(default_factory=list, description="Groups of related files")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Graph metrics like modularity")


class CodeIndexer:
    """Code indexer and analyzer."""

    def __init__(self, callback_manager: Optional[CallbackManager] = None):
        """Initialize the code indexer."""
        # Initialize LLM with callback manager
        self.callback_manager = callback_manager or CallbackManager([StdOutCallbackHandler()])
        self.llm = get_provider(settings.provider)
        self.llm._llm = self.llm._llm.bind(callbacks=self.callback_manager)

        # File patterns
        self.ignore_patterns = [
            '*.pyc', '__pycache__/*', '.git/*', '.github/*', 'node_modules/*',
            '*.min.js', '*.min.css', '*.map', '*.lock', '*.sum',
            'dist/*', 'build/*', '.env*', '*.log', '*venv/*', '*.venv/*',
            '*.egg-info/*', '*.egg', '*.whl', '*.tar.gz', '*.tgz',
            '*.coverage', '.pytest_cache/*', 'htmlcov/*',
        ]
        self.file_type_patterns = {
            'source': ['.py', '.js', '.ts', '.java', '.cpp', '.go', '.rs'],
            'documentation': ['.md', '.txt', '.rst', '.adoc'],
            'config': ['.json', '.yaml', '.yml', '.toml', '.ini'],
            'frontend': ['.html', '.css', '.scss', '.less', '.jsx', '.tsx'],
            'data': ['.sql', '.graphql', '.prisma'],
            'test': ['test_*.py', '*_test.py', '*.test.js', '*.test.ts', '*.spec.py', '*_test.go', '*.spec.js', '*.spec.ts'],
            'environment': ['.env', '.env.local', '.env.development', '.env.production'],
            'ignore': ['.gitignore', '.dockerignore', '.eslintignore'],
            'git': ['.git', '.gitmodules', '.gitattributes'],
            'github': ['.github'],
            'docker': ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml'],
            'package': ['package.json', 'setup.py', 'requirements.txt', 'Cargo.toml', 'go.mod'],
        }

        # Initialize text splitter for large files
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        # Initialize parsers
        self.analysis_parser = JsonOutputParser(pydantic_object=ProjectAnalysis)
        self.dependency_parser = JsonOutputParser(pydantic_object=DependencyGraph)

        # Create analysis prompt template
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a code analysis expert. Analyze the following codebase structure and provide detailed insights."),
            ("user",
     cori_ai."Project Structure:\n{index}\n\nKey Files:\n{key_files}\n\nProvide a comprehensive analysis following "
     cori_ai."the schema.")
        ])

        # Create dependency analysis prompt template
        self.dependency_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a dependency analysis expert. Map the relationships between files in this codebase."),
            ("user",
             "Project Structure:\n{index}\n\nFile Contents:\n{file_contents}\n\nGenerate a dependency graph following "
             "the schema.")
        ])

        # Create summarization chain for large files
        self.summary_chain = load_summarize_chain(
            self.llm.llm,
            chain_type="map_reduce",
            verbose=settings.langchain_verbose
        )

        # Create analysis chains
        self.analysis_chain = (
                RunnableParallel({
                    "index": RunnablePassthrough(),
                    "key_files": RunnablePassthrough()
                })
                | self.analysis_prompt
                | self.llm.llm
                | self.analysis_parser
        )

        # Create dependency chain with document handling
        self.dependency_chain = (
                RunnableParallel({
                    "index": RunnablePassthrough(),
                    "file_contents": RunnablePassthrough()
                })
                | self.dependency_prompt
                | self.llm.llm
                | self.dependency_parser
        )

    def should_ignore_file(self, file_path: str) -> bool:
        """Check if file should be ignored in indexing.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            True if file should be ignored.
        """
        return any(fnmatch.fnmatch(file_path, pattern) for pattern in self.ignore_patterns)

    def get_file_type(self, file_path: str) -> str:
        """Get the type of file based on extension and content.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            File type category.
        """
        path = Path(file_path)
        name = path.name.lower()

        # Check test files first
        for pattern in self.file_type_patterns['test']:
            if fnmatch.fnmatch(name, pattern):
                return 'test'

        # Then check exact filename matches
        for file_type, patterns in self.file_type_patterns.items():
            if name in patterns:
                return file_type

        # Then check extensions
        ext = path.suffix.lower()
        for file_type, patterns in self.file_type_patterns.items():
            if ext in patterns:
                return file_type

            # Check compound extensions (e.g., .test.js)
            for pattern in patterns:
                if pattern.startswith('.') and name.endswith(pattern):
                    return file_type

        return 'other'

    def index_codebase(self, root_dir: str) -> Dict[str, List[str]]:
        """Create an index of the codebase organized by file type.
        
        Args:
            root_dir: Root directory of the codebase.
            
        Returns:
            Dictionary mapping file types to lists of file paths.
        """
        index: Dict[str, List[str]] = {
            'source': [],
            'documentation': [],
            'config': [],
            'frontend': [],
            'data': [],
            'test': [],
            'package': [],
            'environment': [],
            'other': [],
        }

        for root, _, files in os.walk(root_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_dir)

                if self.should_ignore_file(rel_path):
                    continue

                file_type = self.get_file_type(rel_path)
                if file_type in index:
                    index[file_type].append(rel_path)
                else:
                    index['other'].append(rel_path)

        return index

    async def read_and_process_file(self, file_path: str, repo_root: str) -> Document:
        """Read and process a file into a LangChain document.
        
        Args:
            file_path: Path to the file.
            repo_root: Root directory of the repository.
            
        Returns:
            LangChain Document object.
        """
        full_path = os.path.join(repo_root, file_path)
        try:
            if os.path.exists(full_path):
                async with aiofiles.open(full_path, 'r') as f:
                    content = await f.read()
                    return Document(
                        page_content=content,
                        metadata={
                            "source": file_path,
                            "type": self.get_file_type(file_path)
                        }
                    )
        except Exception as e:
            pass
        return Document(
            page_content="",
            metadata={
                "source": file_path,
                "type": "missing"
            }
        )

    async def analyze_project_structure(self, index: Dict[str, List[str]], repo_root: str) -> ProjectAnalysis:
        """Generate a high-level analysis of the project structure.
        
        Args:
            index: Codebase index from index_codebase().
            repo_root: Root directory of the repository.
            
        Returns:
            Analysis results as ProjectAnalysis object.
        """
        try:
            # Read key files as documents
            key_file_paths = [
                'README.md',
                '.editorconfig',
                'setup.py',
                'requirements.txt',
                'package.json',
                'pyproject.toml',
                '.pre-commit-config.yaml',
            ]

            # Read files concurrently
            key_files = await asyncio.gather(*[
                self.read_and_process_file(path, repo_root)
                for path in key_file_paths
            ])

            # Split large documents
            key_file_docs = []
            for doc in key_files:
                if doc.page_content:
                    splits = self.text_splitter.split_documents([doc])
                    key_file_docs.extend(splits)

            # Summarize large files if needed
            if any(len(doc.page_content) > 4000 for doc in key_file_docs):
                key_files_content = await self.summary_chain.ainvoke(key_file_docs)
            else:
                key_files_content = "\n\n".join(
                    f"=== {doc.metadata['source']} ===\n{doc.page_content}"
                    for doc in key_file_docs
                )

            # Run analysis chain
            analysis = await self.analysis_chain.ainvoke({
                "index": json.dumps(index, indent=2),
                "key_files": key_files_content
            }, config={"callbacks": self.callback_manager})

            return analysis
        except Exception as e:
            # Return default analysis on error
            return ProjectAnalysis(
                project_type="unknown",
                languages=[],
                architecture={},
                dependencies={},
                testing={},
                documentation={},
                security={},
                performance={},
                recommendations=[]
            )

    async def analyze_dependencies(self, index: Dict[str, List[str]], repo_root: str) -> DependencyGraph:
        """Analyze dependencies between files in the project.
        
        Args:
            index: Codebase index from index_codebase().
            repo_root: Root directory of the repository.
            
        Returns:
            Dependency graph as DependencyGraph object.
        """
        try:
            # Read source files as documents
            source_docs = await asyncio.gather(*[
                self.read_and_process_file(path, repo_root)
                for path in index['source']
            ])

            # Split large documents
            source_file_docs = []
            for doc in source_docs:
                if doc.page_content:
                    splits = self.text_splitter.split_documents([doc])
                    source_file_docs.extend(splits)

            # Summarize large files if needed
            if any(len(doc.page_content) > 4000 for doc in source_file_docs):
                file_contents = await self.summary_chain.ainvoke(source_file_docs)
            else:
                file_contents = "\n\n".join(
                    f"=== {doc.metadata['source']} ===\n{doc.page_content}"
                    for doc in source_file_docs
                )

            # Run dependency chain
            dependency_graph = await self.dependency_chain.ainvoke({
                "index": json.dumps(index, indent=2),
                "file_contents": file_contents
            }, config={"callbacks": self.callback_manager})

            return dependency_graph
        except Exception as e:
            # Return empty graph on error
            return DependencyGraph(
                nodes={},
                file_types={},
                imports={},
                dependencies={},
                metadata={},
                edges=[],
                clusters=[],
                metrics={}
            )

    async def generate_complete_analysis(self, repo_root: str) -> Dict[str, Any]:
        """Generate a complete analysis of the project.
        
        Args:
            repo_root: Root directory of the repository.
            
        Returns:
            Complete analysis including project structure and dependencies.
        """
        # Index the codebase
        index = self.index_codebase(repo_root)

        try:
            # Run both analyses concurrently
            project_analysis, dependency_graph = await asyncio.gather(
                self.analyze_project_structure(index, repo_root),
                self.analyze_dependencies(index, repo_root)
            )

            return {
                "index": index,
                "project_analysis": project_analysis.model_dump(),
                "dependency_graph": dependency_graph.model_dump()
            }
        except Exception as e:
            return {
                "index": index,
                "project_analysis": {},
                "dependency_graph": {}
            }
