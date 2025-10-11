# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cam-vision is a Python project focused on computer vision applications. The project is currently in its initial setup phase.

## Development Environment

This is a Python project managed with PyCharm. The repository uses standard Python tooling conventions.

### Dependencies & Environment

- Python virtual environment expected (venv, poetry, pipenv, uv, pdm, or pixi)
- Check for `requirements.txt`, `pyproject.toml`, `Pipfile`, or `pyproject.toml` for dependency management
- Environment variables should be stored in `.env` files (gitignored)

## GitHub Actions Integration

The repository has Claude Code integrated via GitHub Actions:

- **claude.yml**: Responds to `@claude` mentions in issues, PRs, and comments
- **claude-code-review.yml**: Automatically reviews PRs when opened or updated

When providing PR reviews, reference the review criteria defined in claude-code-review.yml:
- Code quality and best practices
- Potential bugs or issues
- Performance considerations
- Security concerns
- Test coverage