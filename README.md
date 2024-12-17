# 🦦 Dr. OtterAI Code Review, PhD

🤖 A GitHub Action that provides AI-powered code reviews for your pull requests using multiple LLM providers. Created by a very smart otter with multiple degrees in Computer Science! 🎓

![OtterAI](/static/otterai.png)

## ✨ Features

- 🔍 Automated code review comments on pull requests
- 🧠 Multiple LLM providers support (OpenAI, Gemini, Groq, Mistral)
- 🔌 Custom API endpoint support
- 💬 Customizable review focus
- 📝 Line-specific comments on code changes
- 🤖 Auto-fix suggestions with new PRs
- 🎯 Project-specific guidelines
- 🚫 Skip review functionality with special PR titles

## 🛠️ How to Use

### 1. Skip Code Review (Optional)
To skip the code review for specific PRs, include any of these patterns in your PR title:
```
no-review: Update documentation
skip review: Quick fix
skip-code-review: Emergency patch
otterai-skip: Configuration update
otter skip: Minor changes
otter-restricted: Sensitive update
```

The review will be skipped and Dr. OtterAI will leave a comment notifying the PR author.

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
        uses: fofsinx/otterai@v1.0.0
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
Dr. OtterAI will:
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
  > otter will suggest the best way to build the feature and the best practices to follow

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
- Thanks to the otter who created this action (and their PhD committee)

## 🦦 Support

- 📧 Email: thehuman@boring.name
- 🐙 GitHub Issues: [Create an issue](https://github.com/fofsinx/otterai/issues)
- 🦦 Otter Signal: *splashes water playfully*

---

Made with 💖 by Dr. OtterAI, PhD in Computer Science, Machine Learning, and Fish Recognition





