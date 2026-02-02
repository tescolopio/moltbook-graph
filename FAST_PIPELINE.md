# ⚡ Fast Moltbook Pipeline - Complete Setup

## What Just Happened

You now have a **super-efficient data pipeline** that:
- ✅ Fetches data from Moltbook API directly (NO database required)
- ✅ Exports important data to 9 JSON files in under 2 minutes
- ✅ Automatically commits and pushes to GitHub
- ✅ Runs on a schedule every 5 minutes
- ✅ Updates your website in real-time

## Architecture

```
Moltbook API (public, no auth needed)
    ↓ [Fetch 5,000 posts]
Filter to Top Data
    ↓ [200 agents, 100 topics, 20 connections]
Export 9 JSON Files
    ↓ [200 ms]
Git Commit & Push
    ↓ [30-60 seconds]
Live on GitHub Pages!
```

**Total Pipeline Time: 2-3 minutes** (vs. 30+ minutes with Neo4j approach)

## Files

### Main Script
- **`update_data.py`** - The complete pipeline (API → JSON → GitHub)

### Systemd Automation
- **`/etc/systemd/system/moltbook-fast-update.service`** - Runs the script
- **`/etc/systemd/system/moltbook-fast-update.timer`** - Triggers every 5 minutes

## What Gets Collected & Displayed

| Item | Collected | Displayed | Hidden % |
|------|-----------|-----------|----------|
| Agents | 3,390 | 200 (top by engagement) | 94% |
| Topics | 114 | 100 (top by frequency) | 12% |
| Posts | 5,000 | 27 (timeline dates) | 99.5% |
| Connections | 18,000+ | 20 (top pairs) | 99.9% |

### 9 JSON Files Generated

1. **network_data.json** (200 nodes, 1500 links)
   - Network graph for D3.js visualization
   - Force-directed graph of agents and connections

2. **topic_data.json** (100 topics)
   - Bubble chart data
   - Sized by frequency

3. **leaderboard_data.json** (top 50 agents)
   - Ranked by engagement
   - Posts and engagement metrics

4. **connections_data.json** (top 20 pairs)
   - Agent-to-agent connections
   - Shared topics

5. **summary_stats.json**
   - Global metrics
   - Agent/topic/post counts

6. **agent_history.json**
   - Complete crawl history
   - Agent count trend

7. **agent_history_viz.json**
   - Growth trend visualization data
   - Timeline of agent count changes

8. **timeline_data.json**
   - Activity by date
   - Post counts per day

9. **heatmap_data.json**
   - 24-hour × 7-day activity grid
   - 168 cells total

## How It Works

### Fetch Phase (1-2 min)
```bash
Fetches posts from: https://www.moltbook.com/api/v1/posts
Pagination: 100 posts per request
Limit: 5,000 posts (50 API calls max)
```

### Process Phase (10 sec)
```
Extract:
- Agent names and engagement (likes + replies)
- Topics and topic diversity
- Agent-to-agent connections (shared topics)

Calculate:
- Engagement scores per agent
- Topic frequencies
- Connection weights
```

### Export Phase (500 ms)
```
Generate 9 JSON files with:
- Top 200 agents by engagement
- Top 100 topics by frequency
- Top 20 agent connections
- Full timeline and heatmap
```

### Commit & Push (30-60 sec)
```bash
git add *.json
git commit -m "🤖 Auto-update: {timestamp}"
git push origin main
```

### Live on GitHub Pages
```
GitHub Pages auto-serves updated JSON files
Browser cache invalidated by timestamp
Data appears on dashboard within 1-2 minutes
```

## Schedule

The timer triggers every **5 minutes**:
- First run: 2 minutes after boot
- Subsequent runs: Every 5 minutes thereafter

To check the next scheduled run:
```bash
systemctl list-timers moltbook-fast-update.timer
```

To check the last run:
```bash
journalctl -u moltbook-fast-update.service -n 20
```

To manually trigger a run:
```bash
systemctl start moltbook-fast-update.service
```

## Data Freshness

- **API Fetch**: 0-2 minutes
- **Processing & Export**: ~1 minute
- **Git Commit & Push**: ~1 minute
- **GitHub Pages Deployment**: Instant

**Total Latency: 2-4 minutes** (vs. 30+ minutes before)

## Performance

- **API Calls**: 50 max (5,000 posts ÷ 100 per call)
- **Processing**: Single-pass algorithm
- **Memory**: ~150 MB (light)
- **CPU**: Minimal (Python 3.14)
- **Disk**: ~2 MB JSON files

## Advantages Over Neo4j Approach

| Aspect | Neo4j | Fast Pipeline |
|--------|-------|---------------|
| Requires DB | ✗ Yes | ✓ No |
| Setup Time | 30+ min | 2 min |
| Runtime | 30+ min | 2-3 min |
| CPU Memory | High | Low |
| Latency to Site | 30-45 min | 2-4 min |
| Complexity | Very High | Very Low |
| Git Integration | Manual | Automatic |

## What's Stored

Only **important data** is displayed:
- **Important**: Top agents by engagement, top topics, key connections
- **Ignored**: Low-engagement agents, rare topics, weak connections

This filtering means:
- ✅ Faster processing
- ✅ Smaller JSON files
- ✅ Better visualization performance
- ✅ Clearer data presentation

## Monitoring

### Check Service Status
```bash
systemctl status moltbook-fast-update.timer
systemctl status moltbook-fast-update.service
```

### View Recent Logs
```bash
journalctl -u moltbook-fast-update.service -n 50 -f
```

### Manual Test Run
```bash
cd /mnt/d/moltbook-graph
python3 update_data.py
```

## Troubleshooting

### Timer not running?
```bash
sudo systemctl enable moltbook-fast-update.timer
sudo systemctl start moltbook-fast-update.timer
```

### Git push failing?
- Check credentials: `git remote -v`
- The pipeline continues even if push fails (still updates local files)

### Data not updating?
- Check logs: `journalctl -u moltbook-fast-update.service`
- Check if API is accessible: `curl https://www.moltbook.com/api/v1/posts?limit=1`

## Configuration

To change parameters, edit `update_data.py`:

```python
# Change number of posts fetched
max_posts = 5000  # Currently 5,000

# Change output directory
output_dir = "/mnt/d/moltbook-graph"
```

To change update frequency, edit `/etc/systemd/system/moltbook-fast-update.timer`:

```ini
# Currently every 5 minutes
OnUnitActiveSec=5min

# Change to every 1 minute
OnUnitActiveSec=1min

# Or every 10 minutes
OnUnitActiveSec=10min
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart moltbook-fast-update.timer
```

## URLs

- **Dashboard**: https://tescolopio.github.io/moltbook-graph/
- **Interactive**: https://tescolopio.github.io/moltbook-graph/interactive.html
- **GitHub Repo**: https://github.com/tescolopio/moltbook-graph
- **Raw JSON Data**: https://tescolopio.github.io/moltbook-graph/network_data.json

## Next Steps

1. ✅ Monitor the first few update cycles: `journalctl -f -u moltbook-fast-update.service`
2. ✅ Verify data appears on GitHub Pages within 5 minutes
3. ✅ Check dashboard for live updates
4. ✅ Optionally adjust `max_posts` for different data volumes
5. ✅ Optionally adjust timer frequency if needed

---

**Status**: ✅ Live and Automated  
**Last Updated**: 2026-02-02 14:47:45 UTC  
**Next Run**: Check with `systemctl list-timers moltbook-fast-update.timer`
