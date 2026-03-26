# GitHub Setup & Collaboration Guide

## Step 1: Create GitHub Repository

### Option A: Using GitHub Web Interface
1. Go to https://github.com/new
2. Fill in:
   - **Repository name**: `sideswipe`
   - **Description**: "Hand gesture control system for macOS"
   - **Public/Private**: Your choice
   - **Add .gitignore**: Select Python (already have one, but it's fine)
   - **Add a license**: MIT (we already have one)
3. Click **Create repository**

### Option B: Using GitHub CLI (if installed)
```bash
gh repo create sideswipe --public --description "Hand gesture control system for macOS" --source=. --remote=origin --push
```

## Step 2: Connect Local Repository to GitHub

After creating the GitHub repo, you'll see commands like these. Run them:

```bash
cd /Users/GraysonMackle/Documents/sideswipe

# Add remote (use the URL from GitHub)
git remote add origin https://github.com/YOUR_USERNAME/sideswipe.git

# Rename branch to main (optional but recommended)
git branch -M main

# Push your code
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

## Step 3: Add Team Members as Collaborators

### Via GitHub Web Interface (Easiest)
1. Go to your repo: `github.com/YOUR_USERNAME/sideswipe`
2. Click **Settings** (top right)
3. Click **Collaborators** (left sidebar)
4. Click **Add people**
5. Search for each team member by:
   - GitHub username
   - Email address
6. Click **Add [name] as a collaborator**
7. They'll receive an invite

### Via GitHub CLI
```bash
# Add individual collaborators
gh repo add-collaborator username1 --permission push
gh repo add-collaborator username2 --permission push
gh repo add-collaborator username3 --permission push
```

### Permission Levels
- **Pull**: Read-only access
- **Push**: Can commit and push (recommended for team)
- **Maintain**: Can manage settings
- **Admin**: Full control

## Step 4: Team Members Can Clone Repository

Each team member runs:
```bash
git clone https://github.com/YOUR_USERNAME/sideswipe.git
cd sideswipe
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 src/agent.py
```

## Step 5: Team Workflow

### Creating a Feature Branch
```bash
git checkout -b feature/new-gesture
# Make your changes
git add .
git commit -m "Add new gesture detection"
git push origin feature/new-gesture
```

### Creating a Pull Request
1. Push your branch to GitHub
2. Go to the repo on GitHub
3. Click **Compare & pull request**
4. Add description of changes
5. Click **Create pull request**
6. Team reviews and approves
7. Click **Merge pull request**

### Pulling Latest Changes
```bash
git pull origin main
```

### Setting Up Main Branch Protection (Optional)
1. Go to **Settings** → **Branches**
2. Click **Add rule** under Branch protection rules
3. Enter `main` as pattern
4. Check:
   - ✓ Require pull request reviews
   - ✓ Require status checks
5. Click **Create**

## Step 6: Issue Tracking

### Create Issues for Tasks
1. Click **Issues** tab
2. Click **New issue**
3. Add title and description
4. Assign to team members
5. Add labels (bug, enhancement, documentation, etc.)

### Link to Pull Requests
In a PR description, reference issues with:
```
Closes #5
Fixes #10
```

## Recommended Branching Strategy

```
main (production)
├── feature/clap-detection
├── feature/improved-scrolling
├── bugfix/hand-tracking-loss
└── docs/api-documentation
```

### Branch Naming Convention
- `feature/description` - New feature
- `bugfix/description` - Bug fix
- `docs/description` - Documentation
- `refactor/description` - Code refactoring

## Team Best Practices

### Before Pushing
```bash
# Make sure you're up to date
git pull origin main

# Run locally to verify changes work
python3 src/agent.py

# Check git status
git status

# Review your changes
git diff
```

### Commit Messages
Good commits:
```bash
git commit -m "Add pinch-based scrolling gesture"
git commit -m "Fix hand tracking loss in low light"
git commit -m "Improve swipe detection sensitivity"
```

Bad commits:
```bash
git commit -m "updates"
git commit -m "fix"
git commit -m "asdf"
```

### Pull Request Guidelines
1. **Descriptive title**: "Add pinch scrolling for Chrome"
2. **Detailed description**: Explain what and why
3. **Link issues**: "Closes #15"
4. **Keep PR size small**: Easier to review
5. **Request reviews**: Tag team members

## Collaboration Checklist

- [ ] Create GitHub repo
- [ ] Push local code to GitHub
- [ ] Add team members as collaborators
- [ ] Create issues for tasks
- [ ] Set up branch protection (optional)
- [ ] Create feature branches
- [ ] Use pull requests for changes
- [ ] Review each other's code
- [ ] Merge to main

## Helpful Commands

```bash
# Check remote
git remote -v

# List branches
git branch -a

# Delete branch
git branch -d branch-name

# Undo last commit (keep changes)
git reset --soft HEAD~1

# View commit history
git log --oneline

# See who changed what
git blame filename.py

# Stash changes temporarily
git stash

# Apply stashed changes
git stash pop
```

## Getting Help

- **GitHub Docs**: https://docs.github.com
- **Git Cheat Sheet**: https://github.github.com/training-kit/
- **Ask in repo discussions**: Use GitHub Discussions tab

## Next Steps

1. Create the GitHub repo
2. Push this code to it
3. Add your team members
4. Start collaborating with pull requests!

---

**Questions?** Check GitHub's documentation or ask your team lead!
