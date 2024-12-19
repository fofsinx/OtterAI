"""Tests for code indexer."""
import os
import pytest
from unittest.mock import Mock, AsyncMock, patch, mock_open
import tempfile
import shutil
import json

from langchain_core.messages import AIMessage
from langchain_core.documents import Document
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks import StdOutCallbackHandler

from otterai.indexer import CodeIndexer, ProjectAnalysis, DependencyGraph
from otterai.core.config import settings
from otterai.core.models import DependencyGraph


@pytest.fixture
def mock_callback_manager():
    """Mock callback manager fixture."""
    return CallbackManager([StdOutCallbackHandler()])


@pytest.fixture
def mock_llm(mock_callback_manager):
    """Mock LLM fixture."""
    llm = Mock()
    llm.ainvoke = AsyncMock(return_value=AIMessage(content=json.dumps({
        "project_type": "library",
        "languages": ["python"],
        "architecture": {"type": "modular"},
        "dependencies": {"runtime": ["pytest"]},
        "testing": {"framework": "pytest"},
        "documentation": {"quality": "good"},
        "security": {"issues": []},
        "performance": {"bottlenecks": []},
        "recommendations": [{"type": "test", "description": "Add more tests"}]
    })))
    llm.astream = AsyncMock(return_value=[AIMessage(content="Test")])
    llm.get_num_tokens = Mock(return_value=10)
    llm.modelname_to_contextsize = Mock(return_value=4096)
    llm.bind = Mock(return_value=llm)
    llm.callback_manager = mock_callback_manager
    return llm


@pytest.fixture
def mock_provider(mock_llm, mock_callback_manager):
    """Mock LLM provider fixture."""
    provider = Mock()
    provider.llm = mock_llm
    provider._llm = mock_llm
    provider.model = "test-model"
    provider.generate = AsyncMock(return_value="Test response")
    provider.generate_json = AsyncMock(return_value={
        "project_type": "library",
        "languages": ["python"],
        "architecture": {"type": "modular"},
        "dependencies": {"runtime": ["pytest"]},
        "testing": {"framework": "pytest"},
        "documentation": {"quality": "good"},
        "security": {"issues": []},
        "performance": {"bottlenecks": []},
        "recommendations": [{"type": "test", "description": "Add more tests"}]
    })
    provider.stream = AsyncMock(return_value=["Test"])
    provider.count_tokens = Mock(return_value=10)
    provider.get_token_limit = Mock(return_value=4096)
    return provider


@pytest.fixture
def mock_settings(mock_callback_manager):
    """Mock settings fixture."""
    settings.callback_manager = mock_callback_manager
    settings.provider = "openai"
    return settings


@pytest.fixture
def indexer(mock_provider, mock_callback_manager):
    """Fixture for CodeIndexer instance."""
    with patch('otterai.llm.get_provider', return_value=mock_provider):
        indexer = CodeIndexer(callback_manager=mock_callback_manager)
        indexer.llm = mock_provider  # Override the LLM directly
        indexer.analysis_chain = Mock()
        indexer.analysis_chain.ainvoke = AsyncMock(return_value=ProjectAnalysis(
            project_type="library",
            languages=["python"],
            architecture={"type": "modular"},
            dependencies={"runtime": ["pytest"]},
            testing={"framework": "pytest"},
            documentation={"quality": "good"},
            security={"issues": []},
            performance={"bottlenecks": []},
            recommendations=[{"type": "test", "description": "Add more tests"}]
        ))
        indexer.dependency_chain = Mock()
        indexer.dependency_chain.ainvoke = AsyncMock(return_value=DependencyGraph(
            nodes={"src/main.py": set(["src/utils.py"])},
            file_types={"src/main.py": "source", "src/utils.py": "source"},
            imports={"src/main.py": ["src/utils.py"]},
            dependencies={"src/main.py": ["src/utils.py"]},
            metadata={"src/main.py": {"type": "source"}},
            edges=[{"source": "src/main.py", "target": "src/utils.py"}],
            clusters=[{"name": "src", "files": ["main.py", "utils.py"]}],
            metrics={"modularity": 0.8}
        ))
        return indexer


@pytest.fixture
def test_repo():
    """Create a temporary test repository."""
    temp_dir = tempfile.mkdtemp()
    
    # Create test files
    files = {
        'src/main.py': 'def main():\n    print("Hello")\n',
        'src/utils.py': 'def helper():\n    return True\n',
        'tests/test_main.py': 'def test_main():\n    assert True\n',
        'docs/README.md': '# Test Project\n',
        '.env': 'SECRET=test\n',
        'requirements.txt': 'pytest\n',
    }
    
    for path, content in files.items():
        full_path = os.path.join(temp_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_should_ignore_file(indexer):
    """Test file ignore patterns."""
    # Initialize with empty collections
    graph = DependencyGraph(
        nodes={"src/main.py": set()},
        edges=[],
        clusters=[],
        metrics={},
        file_types={},
        imports={},
        dependencies={},
        metadata={}
    )
    # Should ignore
    assert indexer.should_ignore_file('__pycache__/test.pyc')
    assert indexer.should_ignore_file('.git/config')
    assert indexer.should_ignore_file('node_modules/package.json')
    assert indexer.should_ignore_file('dist/bundle.js')
    assert indexer.should_ignore_file('.env')
    
    # Should not ignore
    assert not indexer.should_ignore_file('src/main.py')
    assert not indexer.should_ignore_file('tests/test_main.py')
    assert not indexer.should_ignore_file('README.md')


def test_get_file_type(indexer):
    """Test file type detection."""
    # Initialize with empty collections
    graph = DependencyGraph(
        nodes={"src/main.py": set()},
        edges=[],
        clusters=[],
        metrics={},
        file_types={},
        imports={},
        dependencies={},
        metadata={}
    )
    
    graph.file_types = {
        "src/main.py": "source",
        "lib/utils.js": "source",
        "app/models/user.ts": "source",
        "README.md": "documentation",
        "docs/api.rst": "documentation",
        "config.json": "config",
        ".env.local": "environment",
        "docker-compose.yml": "docker",
        "tests/test_main.py": "test",
        "src/utils.test.js": "test",
        "app/user.spec.ts": "test",
        "requirements.txt": "package",
        "setup.py": "package",
        "package.json": "package",
        "unknown.xyz": "other"
    }
    
    # Test source files
    assert indexer.get_file_type("src/main.py") == "source"
    assert indexer.get_file_type("lib/utils.js") == "source" 
    assert indexer.get_file_type("app/models/user.ts") == "source"
    
    # Test documentation files
    assert indexer.get_file_type("README.md") == "documentation"
    assert indexer.get_file_type("docs/api.rst") == "documentation"
    
    # Test config files
    assert indexer.get_file_type("config.json") == "config"
    assert indexer.get_file_type(".env.local") == "environment"
    assert indexer.get_file_type("docker-compose.yml") == "docker"
    
    # Test test files
    assert indexer.get_file_type("tests/test_main.py") == "test"
    assert indexer.get_file_type("src/utils.test.js") == "test"
    assert indexer.get_file_type("app/user.spec.ts") == "test"
    
    # Test package files
    assert indexer.get_file_type("requirements.txt") == "package"
    assert indexer.get_file_type("setup.py") == "package"
    assert indexer.get_file_type("package.json") == "package"
    
    # Test unknown file type
    assert indexer.get_file_type("unknown.xyz") == "other"


def test_index_codebase(test_repo, indexer):
    """Test codebase indexing."""
    index = indexer.index_codebase(test_repo)
    
    # Check file categorization
    assert len(index['source']) == 2
    assert 'src/main.py' in index['source']
    assert 'src/utils.py' in index['source']
    
    assert len(index['test']) == 1
    assert 'tests/test_main.py' in index['test']
    
    assert len(index['documentation']) == 1
    assert 'docs/README.md' in index['documentation']
    
    # Environment files should be ignored
    assert '.env' not in index['environment']
    
    assert len(index['package']) == 1
    assert 'requirements.txt' in index['package']


@pytest.mark.asyncio
async def test_read_and_process_file(test_repo, indexer):
    """Test file reading and processing."""
    # Test existing file
    doc = await indexer.read_and_process_file('src/main.py', test_repo)
    assert isinstance(doc, Document)
    assert doc.page_content == 'def main():\n    print("Hello")\n'
    assert doc.metadata['source'] == 'src/main.py'
    assert doc.metadata['type'] == 'source'
    
    # Test missing file
    doc = await indexer.read_and_process_file('missing.py', test_repo)
    assert isinstance(doc, Document)
    assert doc.page_content == ''
    assert doc.metadata['source'] == 'missing.py'
    assert doc.metadata['type'] == 'missing'


@pytest.mark.asyncio
async def test_analyze_project_structure(test_repo, indexer):
    """Test project structure analysis."""
    index = indexer.index_codebase(test_repo)
    analysis = await indexer.analyze_project_structure(index, test_repo)
    assert isinstance(analysis, ProjectAnalysis)
    assert analysis.project_type == "library"
    assert "python" in analysis.languages
    assert analysis.architecture["type"] == "modular"


@pytest.mark.asyncio
async def test_analyze_dependencies(test_repo, indexer):
    """Test dependency analysis."""
    index = indexer.index_codebase(test_repo)
    graph = await indexer.analyze_dependencies(index, test_repo)
    assert isinstance(graph, DependencyGraph)
    assert isinstance(graph.nodes, dict)
    assert isinstance(graph.file_types, dict)
    assert isinstance(graph.imports, dict)
    assert isinstance(graph.dependencies, dict)
    assert isinstance(graph.metadata, dict)
    assert isinstance(graph.edges, list)
    assert isinstance(graph.clusters, list)
    assert isinstance(graph.metrics, dict)
    
    # Check specific values from mock
    assert "src/main.py" in graph.nodes
    assert "src/utils.py" in list(graph.nodes["src/main.py"])
    assert graph.file_types["src/main.py"] == "source"
    assert graph.imports["src/main.py"] == ["src/utils.py"]
    assert graph.edges[0] == {"source": "src/main.py", "target": "src/utils.py"}


@pytest.mark.asyncio
async def test_generate_complete_analysis(test_repo, indexer):
    """Test complete analysis generation."""
    analysis = await indexer.generate_complete_analysis(test_repo)
    assert isinstance(analysis, dict)
    assert 'index' in analysis
    assert 'project_analysis' in analysis
    assert 'dependency_graph' in analysis
    assert analysis['project_analysis']['project_type'] == "library"
    assert "python" in analysis['project_analysis']['languages']


def test_text_splitter(indexer):
    """Test text splitting functionality."""
    # Test small text (no splitting needed)
    text = "Short text"
    docs = indexer.text_splitter.split_text(text)
    assert len(docs) == 1
    assert docs[0] == text
    
    # Test large text (should be split)
    text = "A" * 5000
    docs = indexer.text_splitter.split_text(text)
    assert len(docs) > 1
    assert all(len(doc) <= 4000 for doc in docs)


@pytest.mark.asyncio
async def test_error_handling(test_repo, indexer):
    """Test error handling in analysis."""
    # Test file read error
    with patch('aiofiles.open', side_effect=Exception("Read error")):
        doc = await indexer.read_and_process_file('src/main.py', test_repo)
        assert doc.page_content == ''
        assert doc.metadata['type'] == 'missing'
    
    # Test LLM error in generate_complete_analysis
    with patch.object(indexer.analysis_chain, 'ainvoke', side_effect=Exception("LLM error")), \
         patch.object(indexer.dependency_chain, 'ainvoke', side_effect=Exception("LLM error")):
        analysis = await indexer.generate_complete_analysis(test_repo)
        assert isinstance(analysis, dict)
        assert 'index' in analysis
        assert isinstance(analysis['index'], dict)
        # Check that project_analysis has default empty values
        assert analysis['project_analysis']['project_type'] == "unknown"
        assert analysis['project_analysis']['languages'] == []
        assert analysis['project_analysis']['architecture'] == {}
        assert analysis['project_analysis']['dependencies'] == {}
        assert analysis['project_analysis']['testing'] == {}
        assert analysis['project_analysis']['documentation'] == {}
        assert analysis['project_analysis']['security'] == {}
        assert analysis['project_analysis']['performance'] == {}
        assert analysis['project_analysis']['recommendations'] == []