# GitHub Actions Setup

This repository uses GitHub Actions to automatically update the knowledge graph every hour.

## Setup Instructions

### 1. Add Repository Secret

Go to your GitHub repository settings:
```
Settings → Secrets and variables → Actions → New repository secret
```

Add the following secret:
- **Name:** `NEO4J_PASSWORD`
- **Value:** `password` (or any password you prefer for the ephemeral Neo4j instance)

### 2. Enable GitHub Actions

The workflow is located at `.github/workflows/update-graph.yml` and will:
- Run automatically every hour (or manually via "Actions" tab)
- Spin up a temporary Neo4j instance
- Crawl 500 posts from Moltbook
- Generate visualizations for top 200 agents
- Commit and push updates to GitHub Pages

### 3. Manual Trigger

You can manually trigger the workflow from:
```
Actions → Update Knowledge Graph → Run workflow
```

## Local Git Authentication (No More Passwords!)

To avoid entering your password every time you push:

1. **Option A: Use credential helper (already configured)**
   ```bash
   git config credential.helper store
   ```
   Next time you push, enter your credentials once and they'll be saved.

2. **Option B: Use SSH instead of HTTPS**
   ```bash
   git remote set-url origin git@github.com:tescolopio/moltbook-graph.git
   ```
   Then add your SSH key to GitHub: Settings → SSH and GPG keys

3. **Option C: Use GitHub CLI**
   ```bash
   # Install gh CLI
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update
   sudo apt install gh
   
   # Authenticate
   gh auth login
   ```

## Cost: FREE! 🎉

GitHub Actions provides **2,000 free minutes per month** for public repositories.

Our workflow takes ~2-3 minutes per run:
- 24 runs/day × 30 days = 720 runs/month
- 720 runs × 3 minutes = 2,160 minutes/month

**Note:** You'll use about 2,160 minutes/month, slightly over the free tier. Options:
1. Reduce frequency to every 2 hours: `cron: '0 */2 * * *'` → ~1,080 minutes ✅ FREE
2. Keep hourly and pay ~$0.16/month for the extra 160 minutes
3. Use the free tier and let it pause after 2,000 minutes (still updates ~2/3 of the month)

## Monitoring

Check workflow status:
```
Actions tab → Update Knowledge Graph → Recent workflow runs
```

View logs for debugging if a run fails.
