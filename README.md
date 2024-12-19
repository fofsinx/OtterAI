# 🦦 OtterAI Code Review

AI-powered code review and fix generation for GitHub pull requests.

## Features

- 🤖 Automated code review using various LLM providers (OpenAI, Google Gemini, Groq, Mistral)
- 🔍 Detailed feedback on:
  - Security vulnerabilities and best practices
  - Performance optimizations
  - Code quality and maintainability
  - Test coverage and testing practices
  - Documentation completeness
- 🛠️ Automatic fix generation (optional)
- 🎯 Skip patterns for PRs that don't need review
- 🔧 Highly configurable through environment variables

## Installation

```bash
pip install otterai
```

## Usage

### GitHub Action

Add this to your repository's `.github/workflows/review.yml`:

```yaml
name: OtterAI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    name: Review Pull Request
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    
    steps:
      - uses: harshvardhangoswami/otterai@v1
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
```

### Configuration

The action can be configured using various inputs:

```yaml
- uses: harshvardhangoswami/otterai@v1
  with:
    # Required
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
    
    # Optional
    provider: openai  # openai, gemini, groq, or mistral
    model: gpt-4-turbo-preview  # Provider-specific model
    skip_fixes: false  # Skip automatic fix generation
    skip_generated_pr_review: true  # Skip generated PR review
    extra_prompt: |
      Focus on:
      - Security vulnerabilities
      - Performance optimizations
      - Code quality
```

### Skip Review

You can skip the review for specific PRs by:

1. Adding skip patterns to the PR title:
   - `no-review`
   - `skip-review`
   - `otter-skip`
   - `otter-restricted`

2. PR state patterns that skip review:
   - `merged`
   - `closed`

### Environment Variables

The tool can be configured using environment variables with the `INPUT_` prefix:

- `INPUT_PROVIDER`: LLM provider to use
- `INPUT_MODEL`: Model to use
- `INPUT_OPENAI_API_KEY`: OpenAI API key
- `INPUT_GOOGLE_API_KEY`: Google API key
- `INPUT_GROQ_API_KEY`: Groq API key
- `INPUT_MISTRAL_API_KEY`: Mistral API key
- `INPUT_SKIP_FIXES`: Skip fix generation
- `INPUT_SKIP_GENERATED_PR_REVIEW`: Skip generated PR review
- `INPUT_EXTRA_PROMPT`: Additional instructions for the AI reviewer
- `INPUT_LOG_LEVEL`: Logging level

## Development

1. Clone the repository:
   ```bash
   git clone https://github.com/harshvardhangoswami/otterai.git
   cd otterai
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   .\venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run tests:
   ```bash
   pytest
   ```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.





