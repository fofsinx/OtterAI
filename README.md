# 🦦 Dr. OtterAI Code Review, PhD

🤖 A GitHub Action that provides AI-powered code reviews for your pull requests using multiple LLM providers. Created by a very smart otter with multiple degrees in Computer Science! 🎓

![OtterAI](/static/otterai.png)
![OtterAI](/static/image.png)

## ✨ Features

- 🔍 Automated code review comments on pull requests
- 🧠 Multiple LLM providers support (OpenAI, Gemini, Groq, Mistral)
- 🔌 Custom API endpoint support
- 💬 Customizable review focus
- 📝 Line-specific comments on code changes
- 🤖 Auto-fix suggestions with new PRs
- 🎯 Project-specific guidelines
- 🚫 Skip review functionality with special PR titles or descriptions

## 🛠️ How to Use

### 1. Skip Code Review (Optional)

![Skip Code Review](/static/skip-code-review.png)

Dr. OtterAI can automatically skip reviews based on certain patterns in your PR title or description. Here's how to use it:

#### 🎯 Skip Patterns
You can use any of these patterns (case-insensitive):

```
# Using hyphens
no-review: Your message
skip-review: Your message
no-otter: Your message
skip-otter: Your message
no-otterai: Your message
otter-no: Your message
otter-bye: Your message
otter-restricted: Your message

# Multiple flags (comma-separated)
no-review,skip-otter: Complex update
skip-review,otter-restricted: Sensitive change
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
title: "otter-restricted: Security patch"

# Skip review with multiple flags
title: "no-review,otter-restricted: Confidential update"

# Regular PR (will be reviewed)
title: "feat: Add new feature"
```

When a review is skipped:
- 🦦 Dr. OtterAI will leave a comment notifying the PR author
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
      contents: write  # Ensure this is necessary for your workflow
      pull-requests: write
      actions: write  # Verify if this is essential for your use case
      issues: write  # Confirm if this permission is required
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
  provider: 'openai