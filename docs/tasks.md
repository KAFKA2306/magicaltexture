Skip to content
Navigation Menu
KAFKA2306
magicaltexture

Type / to search
Code
Issues
Pull requests
Actions
Projects
Wiki
Security
Insights
Settings
CI & Deploy to HuggingFace Spaces
CI & Deploy to HuggingFace Spaces #8
Jobs
Run details
Annotations
1 error
Deploy to HuggingFace Spaces
failed now in 8s
Search logs
0s
1s
0s
3s
1s
Run test -n "$HF_TOKEN" || (echo "HF_TOKEN not set" && exit 1)
  test -n "$HF_TOKEN" || (echo "HF_TOKEN not set" && exit 1)
  test -n "$HF_SPACE_ID" || (echo "HF_SPACE_ID not set" && exit 1)
  huggingface-cli login --token "$HF_TOKEN"
  # 必要なファイルのみ転送（.git/.githubは除外）
  huggingface-cli upload . \
    --repo-id "spaces/$HF_SPACE_ID" \
    --repo-type space \
    --include "app.py" "requirements.txt" "assets" \
    --exclude ".git" ".github" --commit-message "CI deploy: $GITHUB_SHA"
  shell: /usr/bin/bash -e {0}
  env:
    pythonLocation: /opt/hostedtoolcache/Python/3.11.13/x64
    PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.13/x64/lib/pkgconfig
    Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.13/x64
    Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.13/x64
    Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.13/x64
    LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.13/x64/lib
    HF_TOKEN: ***
    HF_SPACE_ID: ***
The token has not been saved to the git credentials helper. Pass `add_to_git_credential=True` in this function directly or `--add-to-git-credential` if using via `hf`CLI if you want to set the git credential as well.
Token is valid (permission: write).
The token `HF_TOKEN` has been saved to /home/runner/.cache/huggingface/stored_tokens
Your token has been saved to /home/runner/.cache/huggingface/token
Login successful.
Note: Environment variable`HF_TOKEN` is set and is the current active token independently from the token you've just configured.
⚠️  Warning: 'huggingface-cli login' is deprecated. Use 'hf auth login' instead.
usage: huggingface-cli <command> [<args>]
huggingface-cli: error: unrecognized arguments: --repo-id spaces/***
Error: Process completed with exit code 2.
0s
0s
0s
0s
CI & Deploy to HuggingFace Spaces · KAFKA2306/magicaltexture@25d8b19 