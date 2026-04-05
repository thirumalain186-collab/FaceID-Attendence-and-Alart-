# Contributing to Smart Attendance System

Thank you for your interest in contributing!

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/FaceID-Attendence-and-Alart-.git
   cd FaceID-Attendence-and-Alart-
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Coding Standards

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all public functions
- Keep functions focused and small

## Commit Message Format

Use this format:
```
type(scope): description

Types: feat, fix, docs, style, refactor, test, chore
```

Examples:
```
feat(attendance): add batch expiry notification
fix(camera): handle camera disconnection gracefully
docs(api): update endpoint documentation
```

## Testing

- Write tests for new features
- Run tests before submitting:
  ```bash
  pytest tests/ --cov=. --cov-report=html
  ```

- Code quality checks:
  ```bash
  flake8 . --max-line-length=120
  black --check .
  ```

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Update README if adding features
5. Submit pull request with description

## Code Review

- Address feedback promptly
- Make small, focused commits
- Keep PRs focused on one feature/fix

## Reporting Issues

Use GitHub Issues with:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- System information
- Log files (if applicable)
