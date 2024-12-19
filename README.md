# ✨ CoriAI Code Review, PhD

🤖 A GitHub Action that provides AI-powered code reviews for your pull requests using multiple LLM providers. Created by a very smart human with multiple degrees in Computer Science! 🎓

Example: [CoriAI PR](https://github.com/theboringhumane/cori-ai/pull/13)

[Cori Repo](https://github.com/theboringhumane/cori-ai)

![✨ CoriAI](/static/otterai.png)

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

- 🔍 Automated code review comments on pull requests
- 🧠 Multiple LLM providers support (OpenAI, Gemini, Groq, Mistral)
- 🔌 Custom API endpoint support
- 💬 Customizable review focus
- 📝 Line-specific comments on code changes
- 🤖 Auto-fix suggestions with new PRs
- 🎯 Project-specific guidelines
- 🚫 Skip review functionality with special PR titles or descriptions or labels (skip-review)

![✨ CoriAI](/static/pr-description.png)

## 🎯 Best Practices for AI Reviews

### 1. Detailed PR Descriptions
For the most effective reviews, include detailed information in your PR description:
- **Type of Change**: Check all relevant boxes (bug fix, new feature, etc.)
- **Key Areas to Review**: List specific areas needing attention
- **Related Issues**: Link to relevant issues/tickets
- **Testing Done**: Document your testing approach
- **Additional Notes**: Add context that might help reviewers


> Example:
> ```
> **Type of Change**:
> [x] Bug fix: Fixed memory leak in data processing pipeline
> [x] New feature: Added support for Mistral AI provider
> [x] Documentation update: Updated API reference docs
> [x] Performance improvement: Optimized file indexing (~40% faster)
> [x] Security enhancement: Added API key validation
> [x] Code cleanup: Removed deprecated functions
> [x] Other: Infrastructure updates
>
> **Key Areas to Review**:
> - Data processing pipeline changes in `processor.py`
> - New Mistral integration in `providers/mistral.py`
> - Security improvements in `auth.py`
>
> **Related Issues**: 
> - Fixes #123 (memory leak)
> - Implements #456 (Mistral support)
> - Addresses #789 (security concerns)
>
> **Testing Done**:
> - Added unit tests for new Mistral provider
> - Load tested with 1000 concurrent requests
> - Security penetration testing completed
> - Memory profiling shows no leaks
>
> **Additional Notes**:
> Infrastructure updates include CI/CD pipeline optimization and dependency upgrades.
> Please pay special attention to the error handling in the Mistral integration.
> ```

### 2. Meaningful PR Labels
Add relevant labels to your PR. The AI uses these to:
- Understand the scope of changes
- Focus on relevant aspects
- Provide more targeted feedback

### 3. Structured Commits
- Use clear commit messages
- Follow conventional commit format
- Link to issues when relevant

### 4. Code Organization
- Keep changes focused and atomic
- Group related changes together
- Include relevant tests
- Update documentation as needed

### 5. Review Context
The AI reviewer considers:
- PR description and labels
- Project structure and conventions
- Existing code patterns
- Test coverage
- Documentation requirements

By following these practices, you'll receive:
- More accurate and relevant feedback
- Better security and performance insights
- Focused comments on critical areas
- Suggestions aligned with project standards

## 🛠️ How to Use

### 1. Skip Code Review (Optional)

![Skip Code Review](/static/skip-code-review.png)

✨ CoriAI can automatically skip reviews based on certain patterns in your PR title or description. Here's how to use it:

#### 🎯 Skip Patterns
You can use any of these patterns (case-insensitive):

```
# Using hyphens
no-review: Your message
skip-review: Your message
no-cori: Your message
skip-cori: Your message
no-coriai: Your message
skip-coriai: Your message
cori-no: Your message
cori-bye: Your message
cori-restricted: Your message

# Multiple flags (comma-separated)
no-review,skip-cori: Complex update
skip-review,cori-restricted: Sensitive change
```

#### 🔄 Automatic Skip Conditions
Reviews are automatically skipped when:
- 🏷️ PR title contains any of the skip patterns
- 📝 PR description contains any of the skip patterns
- 🔒 PR state is 'merged' or 'closed'

#### 📋 Example Usage
```yaml
# Skip review for documentation updates
title: "no-review: Update README.md"

# Skip review for sensitive changes
title: "cori-restricted: Security patch"

# Skip review with multiple flags
title: "no-review,cori-restricted: Confidential update"

# Regular PR (will be reviewed)
title: "feat: Add new feature"
```

When a review is skipped:
- ✨ CoriAI will leave a comment notifying the PR author
- ⏭️ No code review will be performed
- 🚫 Dependencies won't be installed

### 2. Set up Secrets
First, add the API key for your preferred LLM provider:

#### OpenAI (Default)
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
      - uses: actions/checkout@v4
      - name: AI Code Review
        uses: theboringhumane/cori-ai@v1.2.0
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

### 6. Auto-Fix Feature
✨ CoriAI will:
1. Review your code changes
2. Add detailed comments
3. Create a new PR with suggested fixes (coming soon)
  > This will be a new PR that has the fixes
4. Link the fix PR to your original PR (coming soon)
  > This will be a link to the new PR that has the fixes
5. Create relevant labels for the PR (coming soon)
  > This will be a list of labels that need to be added to the PR
6. Create relevant issues for the PR (coming soon)
  > This will be a list of issues that need to be fixed
7. Generate a summary of the PR (coming soon)
  > This will be a summary of the PR and the changes made
8. Generate feature guide for the PR (coming soon)
  > This will be a guide for the developer to understand the feature and how to build it
  > cori-ai will suggest the best way to build the feature and the best practices to follow

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

- Thanks to all LLM providers for their amazing models
- Thanks to GitHub for their platform
- Thanks to the human who created this action (and their PhD committee)

## 🦦 Support

- 📧 Email: thehuman@boring.name
- 🐙 GitHub Issues: [Create an issue](https://github.com/theboringhumane/cori-ai/issues)
- 🦦 Otter Signal: *splashes water playfully*

---

Made with 💖 by @theboringhumane, PhD in Computer Science, Machine Learning, and Fish Recognition





