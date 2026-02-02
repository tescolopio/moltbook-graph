# 🎯 Quick Reference: Data Pipeline at a Glance

## The Three Questions Answered

### ❓ WHAT is being collected?

**Raw Data from Moltbook.com**
```
┌─────────────────────────────────────┐
│ Source: Moltbook.com community      │
│ Collection: Every 5 minutes         │
│ Method: REST API crawler (Python)   │
└─────────────────────────────────────┘
         ↓
    TOTAL COLLECTED:
    ├─ 3,261 Agents (AI accounts)
    ├─ 1,228 Topics (discussion subjects)
    ├─ 4,038 Posts (contributions)
    └─ 18,138 Relationships (connections)
```

**What Gets Displayed**
```
DISPLAYED (shown on dashboard):
├─ Agents:      200 / 3,261 (6%)
├─ Topics:      100 / 1,228 (8%)
├─ Connections: 20 / 18,138 (0.1%)
└─ Leaderboard: 50 agents (top by engagement)

HIDDEN (filtered out):
├─ Agents:      3,061 (94%) - Below importance threshold
├─ Topics:      1,128 (92%) - Low frequency topics
└─ Relations:   18,118 (99.9%) - Weak connections
```

---

### ❓ HOW is data aggregated?

**4-Step Processing Pipeline**

```
┌─ STEP 1: COLLECTION ──────────────────────────────────┐
│ • Fetch all posts from Moltbook.com every 5 minutes   │
│ • Extract: agents, topics, timestamps, engagement     │
│ • Build: connection matrix, engagement scores         │
└──────────────────────────────────────────────────────┘
                           ↓
┌─ STEP 2: CALCULATION ─────────────────────────────────┐
│ • Engagement = post interactions (likes + replies)    │
│ • Importance = engagement × log(topic_diversity)      │
│ • Tier 1 = top 50 agents                              │
│ • Tier 2 = next 150 agents                            │
└──────────────────────────────────────────────────────┘
                           ↓
┌─ STEP 3: FILTERING ───────────────────────────────────┐
│ • Keep ONLY top 200 agents by importance score        │
│ • Keep ONLY top 100 topics by frequency               │
│ • Keep ONLY top 20 agent-pair connections             │
│ • Reason: Display clarity + visualization performance │
└──────────────────────────────────────────────────────┘
                           ↓
┌─ STEP 4: JSON EXPORT ─────────────────────────────────┐
│ Export 9 JSON files (all 162+ KB total):              │
│ ├─ network_data.json (graph data)                    │
│ ├─ topic_data.json (bubble chart)                    │
│ ├─ timeline_data.json (growth timeline)              │
│ ├─ leaderboard_data.json (rankings)                  │
│ ├─ connections_data.json (agent pairs)               │
│ ├─ summary_stats.json (key metrics)                  │
│ ├─ agent_history.json (crawl metadata)               │
│ ├─ agent_history_viz.json (growth trend)             │
│ └─ heatmap_data.json (activity grid)                 │
└──────────────────────────────────────────────────────┘
                           ↓
            Upload to GitHub Pages
```

---

### ❓ WHEN is data updated & displayed?

**Update Frequency**

```
COLLECTOR PHASE:
  ├─ Python Crawler: Runs every 5 minutes (GitHub Actions)
  ├─ API Query: Fetch new posts from Moltbook.com
  └─ Processing: ~30-60 seconds

DEPLOYMENT PHASE:
  ├─ Commit: JSON files committed to GitHub
  ├─ Pages Build: GitHub Pages auto-rebuilds (~1 min)
  └─ Data Available: 5-10 minutes old on average

DISPLAY PHASE:
  ├─ Browser Load: Promise.all() loads all 9 files in parallel
  ├─ Visualization: 8 tabs render in sequence (2 seconds)
  └─ User Sees: Complete dashboard in 2-3 seconds

REFRESH CYCLE:
  ├─ Browser Meta-Refresh: Every 120 seconds
  ├─ Data Check: "Last Crawl Time" header shows freshness
  └─ Update Lag: ~5-10 minutes behind real-time
```

**Timeline Visualization**

```
0:00 - Crawler starts
  ├─ Fetch posts from API
  ├─ Calculate metrics
  └─ Filter top items
  
5:00 - Crawler completes
  ├─ Write 9 JSON files
  └─ Commit to GitHub
  
5:30 - GitHub Pages deploys
  └─ Files served to browsers
  
5:35 - User opens page
  ├─ Promise.all() loads files
  ├─ 8 visualizations render
  └─ Dashboard ready
  
7:00 - Browser auto-refreshes
  └─ Loads fresh data
```

---

## 8 Visualization Tabs

| # | Tab | Data Source | Display | Update |
|---|-----|-------------|---------|--------|
| 1 | Network | network_data.json | 200 agents + 1,500 connections | Every 5 min |
| 2 | Topics | topic_data.json | 100 topics (bubble sizes) | Every 5 min |
| 3 | Top Pairs | connections_data.json | 20 agent pairs + shared topics | Every 5 min |
| 4 | Timeline | timeline_data.json | 27 dates showing growth | When new date |
| 5 | Growth Trend | agent_history_viz.json | Agent count over time (1+ points) | Every 5 min |
| 6 | Data Quality | summary_stats.json | Coverage percentages & metrics | Every 5 min |
| 7 | Heatmap | heatmap_data.json | 24h × 7d activity grid (168 cells) | Rolling 7-day |
| 8 | Leaderboard | leaderboard_data.json | Top 50 agents by engagement | Every 5 min |

---

## Data Accuracy Summary

### What's Accurate ✓
- Timestamp of "Last Crawl" (shown in header)
- Relative rankings (agent A > agent B by engagement)
- Topic frequency ordering
- Data Quality % report
- Connection weights (shared topics)

### What's Filtered ✗
- **94% of agents hidden** (3,061 of 3,261)
- **92% of topics hidden** (1,128 of 1,228)
- **99.9% of connections hidden** (18,118 of 18,138)
- **Data is 5-10 minutes old** (not real-time)
- **Heatmap is 7-day rolling window** (old data not retained)

---

## Monitoring Data Health

### Quick Checks
1. **Check freshness**: Look at "Last Crawl Time" in header (should be < 10 min old)
2. **Check completeness**: Visit "Data Quality" tab (see coverage %)
3. **Check errors**: Open browser console (F12) - should show "Data loaded successfully"

### If Data is Stale
- Check GitHub Actions workflow (crawler may have failed)
- Check GitHub Pages deployment (Pages may be rebuilding)
- Manually trigger crawler if needed

### If Visualization Fails
- Open browser console (F12)
- Look for file load errors (e.g., "Failed to fetch network_data.json")
- Check network tab to see which files failed
- Verify JSON files exist in repo root

---

## Key Numbers to Remember

```
COLLECTION:
  3,261 agents
  1,228 topics
  4,038 posts
  18,138 connections

DISPLAY:
  200 agents (Tier 1: 50 + Tier 2: 150)
  100 topics
  20 agent pairs
  50 leaderboard
  27 timeline dates
  168 heatmap cells (24×7)

FILTERING:
  94% of agents hidden
  92% of topics hidden
  99.9% of connections hidden

TIMING:
  5 min: crawl cycle
  120 sec: browser refresh
  2 sec: dashboard load
  5-10 min: data age
```

---

## Finding Documentation

| Topic | Location |
|-------|----------|
| Complete data flow | [DATA_PIPELINE.md](DATA_PIPELINE.md) |
| Code comments | [interactive.html](interactive.html) lines 625-780 |
| GitHub Actions | [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) |
| Setup guide | [SETUP.md](SETUP.md) |
| Deployment | This file |

---

**Last Updated**: 2026-02-02  
**Data as of**: 2026-02-02 08:47:29 UTC  
**Dashboard URL**: https://tescolopio.github.io/moltbook-graph/interactive.html
