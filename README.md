# 🦦 Dr. OtterAI Code Review, PhD

🤖 A GitHub Action that provides AI-powered code reviews for your pull requests using OpenAI's GPT models. Created by a very smart otter with multiple degrees in Computer Science! 🎓

## ✨ Features

- 🔍 Automated code review comments on pull requests
- ⚙️ Configurable OpenAI model selection 
- 🔌 Support for custom OpenAI API endpoints
- 💬 Additional prompt customization for specific review focus
- 📝 Line-specific comments on code changes
- 🧠 Powered by an otter with a PhD in AI Ethics

## 🛠️ How to Use

### 1. Set up Secrets
First, add these secrets to your repository:
- `OPENAI_API_KEY`: Your OpenAI API key
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- (Optional) `OPENAI_BASE_URL`: Custom OpenAI API endpoint if you're using Azure or another provider

### 2. Create Workflow File
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
        uses: fofsinx/otterai@sudo1
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

### 3. Customize the Review (Optional)
Add these optional parameters to customize the review:

```yaml
with:
  # ... required parameters ...
  model: 'gpt-4-turbo-preview'  # Choose your preferred model
  extra_prompt: |
    Focus on:
    - Security best practices
    - Performance optimizations
    - Code maintainability
  openai_base_url: 'https://your-custom-endpoint.com'  # For custom API endpoints
```

### 4. Create a Pull Request
The AI reviewer will automatically:
- Analyze your code changes
- Add relevant comments
- Suggest improvements
- Focus on your specified review areas

### 5. Review Feedback
- Check the pull request comments
- Address the AI's suggestions
- Iterate on your code as needed


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to OpenAI for their powerful GPT models
- Thanks to GitHub for their amazing platform
- Thanks to the otter who created this action

## 🦦 OtterAI Code Review, PhD





