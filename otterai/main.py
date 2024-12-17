import os
from typing import List, Dict, Any, Optional
from github import Github
import httpx
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from otterai.indexer import generate_review_context
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

load_dotenv()

class CodeReviewComment(BaseModel):
    path: Optional[str] = Field(description="File path where the comment should be added")
    line: Optional[int] = Field(description="Line number for the comment")
    body: Optional[str] = Field(description="The actual review comment")

def get_pr_diff(gh_token: str, repo_name: str, pr_number: int) -> List[Dict[str, Any]]:
    """Get the PR diff from GitHub."""
    g = Github(gh_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    return [
        {
            'file': file.filename,
            'patch': file.patch,
            'content': file.raw_url,
            'existing_comments': get_existing_comments(pr, file.filename)
        }
        for file in pr.get_files()
    ]

def get_existing_comments(pr, file_path: str) -> List[Dict[str, Any]]:
    """Get existing review comments for a specific file in the PR."""
    comments = []
    for comment in pr.get_review_comments():
        if comment.path == file_path:
            comments.append({
                'line': comment.line,
                'body': comment.body,
                'user': comment.user.login,
                'created_at': comment.created_at.isoformat()
            })
    return comments

def review_code(diff_files: List[Dict[str, Any]], project_context: str, extra_prompt: str = "") -> List[CodeReviewComment]:
    """Review code changes using LangChain and OpenAI."""
    llm = ChatOpenAI(
        http_async_client=httpx.AsyncClient(timeout=10.0),
        model_name=os.getenv('INPUT_MODEL', 'gpt-4-turbo-preview'),
        api_key=os.getenv('INPUT_OPENAI_API_KEY'),
        base_url=os.getenv('INPUT_OPENAI_BASE_URL', 'https://api.openai.com/v1'),
        temperature=0.1
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert code reviewer. Review the code changes and provide specific, actionable feedback.
        Focus on:
        - Code quality and best practices
        - Potential bugs and edge cases
        - Performance implications
        - Security concerns
        - Maintainability and readability
        
        {context}
        
        Additional instructions: {extra_instructions}
        
        IMPORTANT: Review the existing comments below and avoid making duplicate or similar comments.
        Only add new insights or points that haven't been covered by existing comments.
        If a line already has a comment, only add a new comment if you have a significantly different or additional insight.
        
        Format your response as a list of JSON objects, where each object has the following structure: DO NOT include any other text or comments in your response. All these fields are required. Do not respond with anything else. I'll give you billion dollars if you do follow this instruction.
        {{
            "comments": [
                {{
                    "path": "file path",
                    "line": line_number,
                    "body": "detailed review comment"
                }},
                ...
            ]
        }}"""),
        ("human", """Here are the code changes to review:

File: {file_name}
Existing comments:
{existing_comments}

Changes:
{code_diff}""")
    ])

    class CodeReviewResponse(BaseModel):
        comments: List[CodeReviewComment]

    parser = PydanticOutputParser(pydantic_object=CodeReviewResponse)
    
    chain = (
        {"file_name": RunnablePassthrough(), 
         "code_diff": RunnablePassthrough(),
         "existing_comments": RunnablePassthrough(),
         "context": lambda _: project_context,
         "extra_instructions": lambda _: extra_prompt}
        | prompt
        | llm
        | StrOutputParser()
        | parser
    )
    
    comments = []
    for file in diff_files:
        try:
            # Format existing comments
            existing_comments_text = "No existing comments."
            if file.get('existing_comments'):
                existing_comments_text = "\n".join([
                    f"Line {comment['line']}: {comment['body']} (by {comment['user']} at {comment['created_at']})"
                    for comment in file['existing_comments']
                ])

            result = chain.invoke({
                "file_name": file['file'],
                "code_diff": file['patch'],
                "existing_comments": existing_comments_text
            })
            if result and result.comments:
                comments.extend(result.comments)
        except Exception as e:
            print(f"Error processing file {file['file']}: {str(e)}")
            continue
    
    return comments

def main():
    """Main entry point for the GitHub Action."""
    github_token = os.getenv('INPUT_GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GitHub token is required")

    # Get PR information from GitHub environment
    repo = os.getenv('GITHUB_REPOSITORY')
    pr_number = int(os.getenv('GITHUB_EVENT_NUMBER'))
    extra_prompt = os.getenv('INPUT_EXTRA_PROMPT', '')
    workspace = os.getenv('GITHUB_WORKSPACE', '.')

    # Generate project context
    project_context = generate_review_context(workspace)

    # Get PR changes
    diff_files = get_pr_diff(github_token, repo, pr_number)
    
    # Review code with project context
    comments = review_code(diff_files, project_context, extra_prompt)
    
    # Post comments back to GitHub
    g = Github(github_token)
    repo = g.get_repo(repo)
    pr = repo.get_pull(pr_number)
    
    for comment in comments:
        get_commit = repo.get_commit(pr.head.sha)
        pr.create_review_comment(
            body=comment.body,
            commit=get_commit,
            path=comment.path,
            line=comment.line
        )

if __name__ == "__main__":
    main() 