import asyncio
from typing import List, Dict, Any
from github import Github, Repository, GithubException, PullRequest
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import base64
from datetime import datetime
import logging
import time

from otterai.indexer import analyze_project_structure, index_codebase
from otterai.llm_client import LLMClient

# Initialize a lock to handle race conditions
from threading import Lock
lock = Lock()

def create_branch_name(pr_number: int) -> str:
    """Create a unique branch name for the fixes."""
    return f"otterai/fixes-for-pr-{pr_number}"

def get_file_content(repo: Repository, file_path: str, ref: str) -> str:
    """Get content of a file from GitHub."""
    try:
        content = repo.get_contents(file_path, ref=ref)
        return base64.b64decode(content.content).decode('utf-8')
    except GithubException as e:
        logging.error(f"GitHub API error retrieving {file_path}: {e.data.get('message', str(e))}")
    except Exception as e:
        logging.error(f"Unexpected error getting file content: {str(e)}")
    return ""

def generate_fix(llm: ChatOpenAI, file_path: str, original_content: str, review_comments: List[Dict[str, Any]]) -> str:
    """Generate fixed content for a file based on review comments."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are Dr. OtterAI, a highly skilled code fixer specializing in addressing review comments with precision.
        
IMPORTANT GUIDELINES:
1. Implement only the changes necessary to address the review comments provided.
2. Maintain the original code style and formatting.
3. Insert comments to explain significant changes for better code understanding.
4. Ensure that no new issues are introduced during the fixing process.
5. Preserve the existing functionality of the code.
6. Incorporate appropriate error handling as needed.
7. Adhere to language-specific best practices and standards.
8. Handle race conditions when writing to the same file. Do not modify which is working, just add the changes.

{analysis}
         
\n\n
         
Please return the complete fixed file content, including all necessary imports and dependencies."""),
        ("human", f"""Path: {file_path}

Original Content:
{original_content}

Review Comments:
{''.join([f"Line {comment['line']}: {comment['body']}\n" for comment in review_comments])}

Provide the revised content addressing all the above comments.""")
    ])

    try:
        response = llm.invoke(prompt.format())
        fixed_content = extract_code_from_response(response.content, ['python', 'javascript', 'typescript', 
                                                                        'go', 'rust', 'c', 'c++', 'c#', 'java', 'kotlin', 'swift', 'objective-c', 'php', 'ruby', 'perl', 'haskell', 'erlang', 'elixir', 'scala', 'groovy', 'groovy-lang', 'groovy-lang.org', 'groovy-lang.org.'])
        return fixed_content if fixed_content else original_content
    except Exception as e:
        logging.error(f"Error generating fix: {str(e)}")
        return original_content

def extract_code_from_response(response: str, languages: List[str]) -> str:
    """Extract code block from LLM response."""
    try:
        if "```" in response:
            parts = response.split("```")
            for i in range(1, len(parts), 2):
                lang = parts[i].split('\n')[0].strip()
                if lang in languages:
                    return '\n'.join(parts[i].split('\n')[1:])
        return response.strip()
    except Exception as e:
        logging.error(f"Error extracting code from response: {str(e)}")
        return ""

def create_fix_pr(
    repo: Repository,
    base_pr: PullRequest.PullRequest,
    files_to_fix: Dict[str, List[Dict[str, Any]]],
    analysis: str
) -> str:
    """Create a new PR with fixes for the review comments."""
    
    # Create a new branch from the head of the base PR with retry to handle race conditions
    for attempt in range(3):
        try:
            new_branch = create_branch_name(base_pr.number)
            base_ref = base_pr.head.ref
            base_sha = base_pr.head.sha
            logging.info(f"Creating branch {new_branch} from {base_ref} with SHA {base_sha}")
            with lock:
                repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=base_sha)
            break
        except GithubException as e:
            if e.status == 422 and 'Reference already exists' in e.data.get('message', ''):
                logging.warning(f"Branch {new_branch} already exists. Using the existing branch.")
                break
            logging.error(f"Error creating branch: {e.data.get('message', str(e))}")
            return ""
        except Exception as e:
            logging.error(f"Unexpected error creating branch: {str(e)}")
            return ""
    
    llm = LLMClient().get_client()

    # Generate and commit fixes
    files_changed = []

    for file_path, comments in files_to_fix.items():
        try:
            original_content = get_file_content(repo, file_path, base_ref)
            if not original_content:
                continue

            fixed_content = generate_fix(llm, file_path, original_content, comments, analysis)
            if fixed_content == original_content:
                continue

            with lock:
                file_contents = repo.get_contents(file_path, ref=new_branch)
                repo.update_file(
                    path=file_path,
                    message=f"🤖 Fix {file_path} based on review comments from Dr. OtterAI",
                    content=fixed_content,
                    sha=file_contents.sha,
                    branch=new_branch
                )
            files_changed.append(file_path)
        except GithubException as e:
            logging.error(f"GitHub API error updating {file_path}: {e.data.get('message', str(e))}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error updating {file_path}: {str(e)}")
            continue

    if not files_changed:
        logging.warning("No files were changed, skipping PR creation")
        return ""

    # Create PR description using LLM
    description_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are Dr. OtterAI, tasked with creating a pull request description for automated fixes.
Maintain a professional tone while keeping a playful otter personality.
Ensure the description includes:
1. A concise summary of the changes made.
2. A list of files that were fixed.
3. The types of fixes applied.
4. Suggestions for testing the fixes.
5. Recommended next steps if any."""),
        ("human", f"""Base PR: #{base_pr.number}
Files changed: {', '.join(files_changed)}
Number of review comments addressed: {len(files_to_fix)}

Create a detailed PR description based on the above information.""")
    ])

    try:
        response = llm.invoke(description_prompt.format())
        pr_description = extract_pr_description_from_response(response.content)
    except Exception as e:
        logging.error(f"Error generating PR description: {str(e)}")
        pr_description = "🦦 Automated fixes for review comments."

    # Create the PR with retry to handle race conditions
    for attempt in range(3):
        try:
            with lock:
                fix_pr = repo.create_pull(
                    title=f"🤖 Auto-fixes for PR #{base_pr.number}",
                    body=pr_description,
                    base=base_ref,
                    head=new_branch,
                    maintainer_can_modify=True
                )
            logging.info(f"✨ Created fix PR: {fix_pr.html_url}")
            return fix_pr.html_url
        except GithubException as e:
            if e.status == 422 and 'A pull request already exists' in e.data.get('message', ''):
                logging.warning(f"Pull request for branch {new_branch} already exists. Updating the existing PR.")
                # update the existing PR
                fix_pr = repo.get_pull(fix_pr.number)
                fix_pr.update(state="open", title=f"🤖 Auto-fixes for PR #{base_pr.number}", body=pr_description)
                return fix_pr.html_url
            logging.error(f"GitHub API error creating PR: {e.data.get('message', str(e))}")
            return ""
        except Exception as e:
            logging.error(f"Unexpected error creating PR: {str(e)}")
            return ""
    else:
        logging.error("Failed to create pull request after multiple attempts.")
        return ""

def extract_pr_description_from_response(response: str) -> str:
    """Extract PR description from LLM response."""
    try:
        if "```" in response:
            parts = response.split("```")
            return ''.join(parts[1::2]).strip()
        return response.strip()
    except Exception as e:
        logging.error(f"Error extracting PR description: {str(e)}")
        return "🦦 Automated fixes for review comments."