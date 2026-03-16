# Git Workflow

## Metadata
- **ID:** git-workflow
- **Version:** 1.0.0
- **Source:** garuda/internal
- **Agents:** rudra, arjun, priya, michael
- **Tags:** git, github, version-control, collaboration

## Purpose
Standard git workflow for Garuda development team.

## Branch Strategy

### Main Branches
- `main` - Production-ready code
- `develop` - Integration branch

### Feature Branches
- `feature/<ticket-id>-<description>` - New features
- `bugfix/<ticket-id>-<description>` - Bug fixes
- `hotfix/<ticket-id>-<description>` - Production hotfixes

## Commit Convention

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Examples
```
feat(api): Add user authentication endpoint
fix(ui): Resolve mobile navigation issue
docs(readme): Update installation instructions
```

## Workflow Steps

1. **Start Feature**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/GARUDA-123-user-auth
```

2. **Regular Commits**
```bash
git add .
git commit -m "feat(auth): Add login form component"
git push origin feature/GARUDA-123-user-auth
```

3. **Create Pull Request**
- Target: `develop`
- Title: `[GARUDA-123] Add user authentication`
- Description: What, Why, How
- Reviewers: Assign based on lane

4. **After Review**
```bash
git checkout develop
git pull origin develop
git branch -d feature/GARUDA-123-user-auth
```

## PR Checklist
- [ ] Branch name follows convention
- [ ] Commits follow convention
- [ ] Tests pass
- [ ] No merge conflicts
- [ ] Documentation updated
