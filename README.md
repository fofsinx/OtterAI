# ✨ CoriAI Code Review, PhD

🤖 A GitHub Action that provides AI-powered code reviews for your pull requests using multiple LLM providers. Created by a very smart human with multiple degrees in Computer Science! 🎓

Example: [CoriAI PR](https://github.com/theboringhumane/cori-ai/pull/13)

[Cori Repo](https://github.com/theboringhumane/cori-ai)

![✨ CoriAI](/static/otterai.png)

## ✨ Features

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
OPENAI_API_KEY=your-openai-key
```

#### Google Gemini
```bash
GOOGLE_API_KEY=your-gemini-key
```

#### Groq
```bash
GROQ_API_KEY=your-groq-key
```

#### Mistral
```bash
MISTRAL_API_KEY=your-mistral-key
```

### 3. Create Workflow File
Create `.github/workflows/code-review.yml` with:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - name: AI Code Review
        uses: theboringhumane/cori-ai@v1.2.0
        with:
          # Choose your preferred provider
          provider: 'openai'  # or 'gemini', 'groq', 'mistral'
          
          # Provider-specific settings
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          # or
          # google_api_key: ${{ secrets.GOOGLE_API_KEY }}
          # or
          # groq_api_key: ${{ secrets.GROQ_API_KEY }}
          # or
          # mistral_api_key: ${{ secrets.MISTRAL_API_KEY }}
          
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

### 4. Provider-Specific Configurations

#### OpenAI
```yaml
with:
  provider: 'openai'
  openai_api_key: ${{ secrets.OPENAI_API_KEY }}
  model: 'gpt-4-turbo-preview'  # Optional, default model
  openai_base_url: 'https://api.openai.com/v1'  # Optional, for custom endpoints
```

#### Google Gemini
```yaml
with:
  provider: 'gemini'
  google_api_key: ${{ secrets.GOOGLE_API_KEY }}
  model: 'gemini-1.5-flash'  # Optional, default model
```

#### Groq
```yaml
with:
  provider: 'groq'
  groq_api_key: ${{ secrets.GROQ_API_KEY }}
  model: 'mixtral-8x7b-32768'  # Optional, default model
```

#### Mistral
```yaml
with:
  provider: 'mistral'
  mistral_api_key: ${{ secrets.MISTRAL_API_KEY }}
  model: 'mistral-large-latest'  # Optional, default model
```

### 5. Customize Review Focus (Optional)
Add specific focus areas for the review:

```yaml
with:
  # ... provider settings ...
  extra_prompt: |
    Focus on:
    - Security best practices
    - Performance optimizations
    - Code maintainability
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

## 🎓 Default Models by Provider

| Provider | Default Model | Alternative Options |
|----------|---------------|-------------------|
| OpenAI | gpt-4-turbo-preview | gpt-4, gpt-3.5-turbo |
| Gemini | gemini-1.5-flash | gemini-1.5-pro | xyz |
| Groq | mixtral-8x7b-32768 | llama2-70b-4096 | xyz |
| Mistral | mistral-large-latest | mistral-medium, mistral-small | xyz |

## 🔒 Security Best Practices

1. Store API keys securely in GitHub Secrets
2. Use repository-specific tokens
3. Set appropriate permissions in workflow
4. Review auto-generated fixes before merging

## 🐛 Troubleshooting

### Common Issues
1. **API Key Issues**: Ensure the correct API key is set for your chosen provider
2. **Model Availability**: Some models might be region-restricted
3. **Rate Limits**: Consider using different providers during high load

### Provider Status
- OpenAI: [status.openai.com](https://status.openai.com)
- Gemini: [status.generativeai.google](https://status.generativeai.google)
- Groq: [status.groq.com](https://status.groq.com)
- Mistral: [status.mistral.ai](https://status.mistral.ai)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all LLM providers for their amazing models
- Thanks to GitHub for their platform
- Thanks to the human who created this action (and their PhD committee)

## 🦦 Support

- 📧 Email: thehuman@boring.name
- 🐙 GitHub Issues: [Create an issue](https://github.com/theboringhumane/cori-ai/issues)
- 🦦 Otter Signal: *splashes water playfully*

---

Made with 💖 by @theboringhumane, PhD in Computer Science, Machine Learning, and Fish Recognition





