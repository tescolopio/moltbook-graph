# GitHub Pages Setup Instructions

## Quick Setup (5 minutes)

### 1. Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Name: `moltbook-graph` (or any name you like)
3. Make it **Public**
4. Don't initialize with README (we already have one)
5. Click **Create repository**

### 2. Push Your Code

GitHub will show you commands, but here's the exact sequence:

```bash
cd /mnt/d

# Add all files
git add .

# Commit
git commit -m "Initial commit: Moltbook Knowledge Graph Dashboard"

# Add your GitHub repo (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/moltbook-graph.git

# Push to GitHub
git branch -M main
git push -u origin main
```

You'll be asked for GitHub credentials. Use a [Personal Access Token](https://github.com/settings/tokens) as the password.

### 3. Enable GitHub Pages

1. Go to your repo: `https://github.com/YOUR_USERNAME/moltbook-graph`
2. Click **Settings** tab
3. Click **Pages** in left sidebar
4. Under "Source":
   - Branch: `main`
   - Folder: `/ (root)`
5. Click **Save**

GitHub will show: "Your site is live at `https://YOUR_USERNAME.github.io/moltbook-graph/`"

**Wait 1-2 minutes** for the first deployment.

### 4. Update the Link

Edit `/mnt/d/README.md` and replace the dashboard link with your actual GitHub Pages URL.

## Auto-Update Strategy

### Option A: Manual Updates (Simplest)

Every time the dashboard updates (every 5 minutes on your machine), you can push:

```bash
cd /mnt/d
git add *.png *.html last_update.txt
git commit -m "Update: $(date)"
git push
```

Add this to your update script for automatic pushes!

### Option B: GitHub Actions (Advanced)

Create `.github/workflows/update.yml` to run the crawler in GitHub Actions. This would:
- Run on schedule (every 5 min)
- Execute crawler
- Generate visualizations
- Commit and push

But this requires setting up Neo4j in Actions (complex).

### Option C: Scheduled Push (Recommended)

Create a cron job to auto-push updates:

```bash
# Add to crontab: crontab -e
*/5 * * * * cd /mnt/d && git add . && git commit -m "Auto-update $(date +\%Y-\%m-\%d\ \%H:\%M)" && git push origin main 2>&1 | logger -t moltbook-git
```

This pushes every 5 minutes after your local update.

## Custom Domain (Optional)

Want `moltbook-graph.yourdomain.com`?

1. Add file `/mnt/d/CNAME` with your domain:
   ```
   moltbook-graph.yourdomain.com
   ```

2. In your DNS settings, add:
   ```
   Type: CNAME
   Name: moltbook-graph
   Value: YOUR_USERNAME.github.io
   ```

3. In GitHub repo Settings > Pages, add custom domain

## Troubleshooting

**404 Error?**
- Wait 2 minutes after enabling Pages
- Check that `index.html` is in the root folder
- Verify branch is set to `main` in Pages settings

**Images not loading?**
- Ensure `.png` files are committed: `git add *.png`
- Check file sizes (GitHub has 100MB limit per file)

**Page not updating?**
- Push changes: `git push`
- GitHub Pages can take 1-2 minutes to rebuild

## Next Steps

1. Star your repo ⭐
2. Share the link on Moltbook!
3. Add more features (historical data, trends, etc.)

---

Need help? Check [GitHub Pages docs](https://docs.github.com/en/pages)
