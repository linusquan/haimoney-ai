

run python use `uv run python` or activate uv environment with `uv shell`

# Project Module Management
- Project is properly configured as installable package in pyproject.toml with build-system
- Use `uv pip install -e .` to install project in editable mode for proper module imports
- NEVER use manual sys.path manipulation - indicates improper project setup
- Modules should be importable as `from tools.file_extract import GeminiFileExtractor`
- Package structure defined in pyproject.toml: packages = ["factfind", "tools"]


DO NOT adding emoji in the code