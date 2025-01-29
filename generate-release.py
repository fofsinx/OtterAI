import json
import os
import urllib.request
import urllib.error

def generate_release_notes():
    try:
        data = json.dumps({
            "model": "codellama/CodeLlama-34b-Instruct-hf",
            "messages": [
                {
                    "role": "system", 
                    "content": """You are a helpful assistant that generates release notes for a software project. Follow these guidelines:
                        1. Analyze the provided commit messages and generate a comprehensive summary
                        2. Group changes by type (features, fixes, improvements etc)
                        3. Include technical details and implementation specifics
                        4. Add relevant code snippets in markdown code blocks
                        5. Create mermaid diagrams to visualize architecture/flow changes
                        6. Use emojis liberally to add personality
                        7. Keep a fun, engaging tone while being technically accurate
                        8. Highlight breaking changes and migration steps if any
                        9. Add deployment instructions if relevant
                        10. Include performance impact notes
                        11. List any new dependencies introduced
                        12. Note API changes and backwards compatibility
                        13. Add security advisory if applicable
                        14. Mention contributors and acknowledgements
                        15. Format everything in GitHub-flavored markdown

                        Only return the formatted release notes, no other text."""
                },
                {
                    "role": "user",
                    "content": f"Generate detailed release notes with the following information:\n\nCommit History: {os.environ.get('COMMITS')}\nRepository: {os.environ.get('GITHUB_REPOSITORY')}\nRelease Name: {os.environ.get('DOCKERLIKE_RELEASE_NAME')}\nVersion: {os.environ.get('NEW_VERSION')}\n\nPlease analyze the commits and generate comprehensive release notes following the system guidelines."
                }
            ]
        })

        url = os.environ.get("OPENAI_BASE_URL") + "/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}"
        }

        req = urllib.request.Request(
            url,
            data=data.encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req) as response:
            response_data = response.read()
            content = json.loads(response_data)["choices"][0]["message"]["content"]
            with open("release_notes.md", "w") as f:
                f.write(content)

    except Exception as error:
        print(f"Error: {error}")
        exit(1)

if __name__ == "__main__":
    generate_release_notes()