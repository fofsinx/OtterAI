import os
from typing import List, Dict, Any
from github import Github
from langchain.chains import create_structured_output_chain
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from .indexer import generate_review_context

class CodeReviewComment(BaseModel):
    path: str = Field(description="File path where the comment should be added")
    line: int = Field(description="Line number for the comment")
    body: str = Field(description="The actual review comment")

def get_pr_diff(gh_token: str, repo_name: str, pr_number: int) -> List[Dict[str, Any]]:
    """Get the PR diff from GitHub."""
    g = Github(gh_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    return [
        {
            'file': file.filename,
            'patch': file.patch,
            'content': file.raw_url
        }
        for file in pr.get_files()
    ]

def review_code(diff_files: List[Dict[str, Any]], project_context: str, extra_prompt: str = "") -> List[CodeReviewComment]:
    """Review code changes using LangChain and OpenAI."""
    llm = ChatOpenAI(
        model=os.getenv('INPUT_MODEL', 'gpt-4-turbo-preview'),
        api_key=os.getenv('INPUT_OPENAI_API_KEY'),
        base_url=os.getenv('INPUT_OPENAI_BASE_URL', 'https://api.openai.com/v1'),
        temperature=0.1
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are an expert code reviewer. Review the code changes and provide specific, actionable feedback.
        Focus on:
        - Code quality and best practices
        - Potential bugs and edge cases
        - Performance implications
        - Security concerns
        - Maintainability and readability
        
        {project_context}
        
        Additional instructions: {extra_prompt}"""),
        ("human", "Here are the code changes to review:\n{code_diff}")
    ])

    parser = PydanticOutputParser(pydantic_object=CodeReviewComment)
    chain = create_structured_output_chain(CodeReviewComment, llm, prompt, verbose=True)
    
    comments = []
    for file in diff_files:
        result = chain.invoke({
            "code_diff": f"File: {file['file']}\nPatch:\n{file['patch']}",
            "extra_prompt": extra_prompt
        })
        if result.comments:
            comments.extend(result.comments)
    
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
        pr.create_review_comment(
            body=comment.body,
            commit_id=pr.head.sha,
            path=comment.path,
            line=comment.line
        )

if __name__ == "__main__":
    main() 