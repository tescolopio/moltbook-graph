# 📊 Data Pipeline Documentation

## Overview

This document describes exactly what data is being collected, how it's aggregated, and when it's displayed on the Moltbook Intelligence dashboard.

---

## Data Flow Architecture

```
Moltbook API → Python Crawler → JSON Generation → GitHub Pages → Browser Display
```

---

## WHAT: Data Being Collected

### Raw Data Source
- **Source**: Moltbook.com community posts
- **Collection Method**: REST API crawler
- **Collection Frequency**: Every 5 minutes
- **Data Captured Per Post**:
  - Agent ID (username/poster)
  - Post content and metadata
  - Topics mentioned in post
  - Timestamp
  - Engagement metrics (likes, replies, shares)

### Core Entities Tracked
1. **Agents** (AI account holders)
   - Total: 3,261 unique agents
   - Displayed: Top 200 agents
   - Attributes: engagement score, topic count, post count, importance rank, tier level

2. **Topics** (Discussion subjects)
   - Total: 1,228 unique topics
   - Displayed: Top 100 topics
   - Attributes: frequency, popularity score

3. **Posts** (Individual contributions)
   - Total: 4,038 posts analyzed
   - Attributes: author, topics, timestamp, engagement

4. **Relationships**
   - Total: 18,138 documented connections
   - Types: agent-to-agent (shared topics), agent-to-topic (mentions)
   - Top 20 connections displayed

---

## HOW: Data Aggregation & Processing

### Step 1: Collection (Every 5 minutes)
```python
# Crawler fetches from Moltbook API
- Retrieve all new/updated posts since last crawl
- Extract agent mentions and topic references
- Calculate real-time engagement metrics
```

### Step 2: Aggregation
```
Network Building:
  - Create nodes for each agent
  - Calculate importance score = (engagement × topic_diversity)
  - Build weighted edges based on shared topics
  - Assign tier levels (Tier 1: top 50, Tier 2: next 150)

Topic Analysis:
  - Count topic frequency across all posts
  - Rank by popularity
  - Calculate topic-agent associations

Timeline Aggregation:
  - Group posts by date
  - Count cumulative agents, posts, topics
  - Track growth metrics
```

### Step 3: Filtering & Display Logic

| Data | Total | Displayed | Filter Method |
|------|-------|-----------|---------------|
| Agents | 3,261 | 200 | Top 200 by importance score |
| Topics | 1,228 | 100 | Top 100 by frequency |
| Posts | 4,038 | 27 | By timeline date |
| Connections | 18,138 | 20 | Top 20 agent pairs by shared topics |
| Leaderboard | 3,261 | 50 | Top 50 by engagement |
| Heatmap | Full week | 168 cells | 24 hours × 7 days |

### Step 4: JSON Export
Generated files and their purposes:

| File | Purpose | Size | Update Frequency |
|------|---------|------|------------------|
| **network_data.json** | Force-directed graph visualization | 162 KB | Every 5 min |
| **topic_data.json** | Topic bubble chart | 11 KB | Every 5 min |
| **timeline_data.json** | Growth trend line chart | 1.5 KB | Every 5 min |
| **leaderboard_data.json** | Top 50 agents ranking | 4.5 KB | Every 5 min |
| **connections_data.json** | Top 20 agent pairs with shared topics | 4.2 KB | Every 5 min |
| **summary_stats.json** | Key metrics snapshot | 287 bytes | Every 5 min |
| **agent_history.json** | Single crawl baseline data | 387 bytes | Every 5 min |
| **agent_history_viz.json** | Growth trend data (1 data point per crawl) | 163 bytes | Every 5 min |
| **heatmap_data.json** | Activity heatmap by day/hour (week snapshot) | 1.3 KB | Every 5 min |

---

## WHEN: Display Timeline & Refresh Schedule

### Initial Page Load (Browser)
```
1. Page requests all 9 JSON files simultaneously
   └─ Files downloaded from GitHub Pages
   
2. Promise.all() waits for all data to load
   └─ Timeout: No explicit timeout (waits indefinitely)
   
3. Browser console logs success/failure for each file
   └─ Example: "network: 200 nodes, topics: 100 topics"
   
4. All 8 visualizations initialize in order:
   ├─ Network Graph (force-directed layout)
   ├─ Topics (bubble chart)
   ├─ Top Pairs (connection list)
   ├─ Timeline (area chart)
   ├─ Growth Trend (line chart)
   ├─ Data Quality (HTML report)
   ├─ Activity Heatmap (day/hour grid)
   └─ Leaderboard (ranking table)
   
5. Last crawl timestamp displayed
   └─ Extracted from agent_history.json
```

### Runtime Refresh Schedule
- **Browser Auto-Refresh**: Every 120 seconds (meta refresh tag)
- **GitHub Actions Crawl**: Every 5 minutes
- **Visual Update Lag**: ~5-10 minutes (crawl time + upload time)

### Data Age Information
- **"Last Crawl Time"**: Displayed in header (from agent_history.json)
- **"Data as of"**: Reflects last Python crawler execution
- **Note**: Network data is a snapshot, not real-time streaming

---

## Data Accuracy & Quality

### Known Limitations

1. **Agent Filtering**
   - Only 200 of 3,261 agents shown (94% hidden)
   - Display cutoff: agents must have minimum importance score
   - Justification: Visualization clarity on large networks

2. **Topic Filtering**
   - Only 100 of 1,228 topics shown (92% hidden)
   - Filtered by frequency threshold
   - Less popular topics completely hidden

3. **Relationship Subset**
   - Only 20 of 18,138 connections displayed
   - Top connections by shared topic count only
   - Weaker relationships not visualized

4. **Time Lag**
   - Dashboard shows snapshot from ~5-10 minutes ago
   - Reflects when Python crawler last ran
   - Not real-time data

5. **Heatmap Data**
   - Shows only last 7 days (rolling window)
   - Activity count may not include all posts
   - Bucket by day + hour (UTC assumed)

### Data Quality Report
Displayed in **"Data Quality"** tab:
```
Total Agents in Database: 3,261
Agents Displayed: 200
Hidden Agents: 3,061 (93.9%)
Reason: Importance score below display threshold

Total Topics Tracked: 1,228
Topics Displayed: 100
Hidden Topics: 1,128 (91.8%)
Reason: Frequency below threshold

Total Posts Analyzed: 4,038
Posts Displayed: 27 (timeline view)
Subset Reason: 1 per date shown
```

---

## File Structures

### network_data.json
```json
{
  "nodes": [
    {
      "id": "AgentName",
      "engagement": 1107285,    // Total interaction score
      "topics": 9,              // Unique topics discussed
      "importance": 2549617.93, // Ranking metric
      "tier": 1,                // 1=top 50, 2=next 150
      "posts": 3                // Posts by this agent
    }
  ],
  "links": [
    {
      "source": "Agent1",
      "target": "Agent2",
      "value": 10              // Shared topic count
    }
  ]
}
```

### summary_stats.json
```json
{
  "total_agents": 3261,
  "total_topics": 1228,
  "total_posts": 4038,
  "total_relationships": 18138,
  "displayed": {
    "agents": 200,
    "topics": 100,
    "leaderboard": 50,
    "hot_topics": 1,
    "top_connections": 20
  },
  "tiers": {
    "tier1": 50,     // Top tier
    "tier2": 150     // Secondary tier
  }
}
```

### agent_history_viz.json
```json
[
  {
    "date": "2026-02-02",
    "time": "08:47:29",
    "agents": 3261,
    "posts": 4038,
    "topics": 1228,
    "growth": 0,              // Change since last crawl
    "agentsPerPost": 0.81     // Metric: agents / posts
  }
]
```

### heatmap_data.json
```json
[
  {
    "day": 6,      // 0=Sunday, 6=Saturday
    "hour": 0,     // 0-23 (UTC)
    "count": 142   // Posts in that hour
  }
]
```

---

## Visualization Details

### 🌐 Network Tab
- **What**: Force-directed graph of top 200 agents
- **Layout**: D3.js force simulation
- **Node Size**: Proportional to engagement score
- **Edge Width**: Proportional to shared topic count
- **Color**: Gradient based on tier level
- **Interaction**: Hover to highlight connections, drag to move

### 📊 Topics Tab
- **What**: Bubble chart of top 100 topics
- **Bubble Size**: Topic frequency
- **Color**: Category or tier
- **Interaction**: Click to filter network

### 🔗 Top Pairs Tab
- **What**: Table of top 20 agent-to-agent connections
- **Columns**: Agent 1, Agent 2, Shared Topics, Sample Topics
- **Sort**: By shared topic count (descending)

### 📈 Timeline Tab
- **What**: Area chart of agent/post/topic growth
- **Data Points**: 1 per date (27 dates shown)
- **Metrics**: Agents, Topics, Posts (stacked area)
- **Interaction**: Hover for exact values

### 📊 Growth Trend Tab
- **What**: Line chart of agent growth over time
- **Data Points**: 1 per crawl cycle (~5 min intervals)
- **Current Data**: 1 point (new feature)
- **Future**: Will show growth curve as data accumulates

### ⚠️ Data Quality Tab
- **What**: HTML report of data completeness
- **Metrics**: Agent/topic/post coverage percentages
- **Purpose**: Transparency about what's shown vs hidden

### 🔥 Activity Heatmap Tab
- **What**: Day-of-week × Hour-of-day grid
- **Cells**: 24 hours × 7 days = 168 cells
- **Color Intensity**: Activity count (hotter = more posts)
- **Axes**: Rows=Days (Sun-Sat), Columns=Hours (0-23 UTC)

### 🏆 Leaderboard Tab
- **What**: Table of top 50 agents by engagement
- **Columns**: Rank, Agent Name, Engagement, Topics, Posts
- **Sort**: By engagement score (descending)

---

## Common Questions

### Q: Why are most agents hidden?
**A**: The network has 3,261 agents but only 200 fit on screen without crowding. Hidden agents have lower engagement/importance scores. Filter threshold can be adjusted in Python crawler.

### Q: Why is data ~5 minutes old?
**A**: Python crawler runs every 5 minutes, fetches data, processes it, writes JSON, and GitHub Pages rebuilds. Real-time updates would require WebSocket/streaming, which is complex for static hosting.

### Q: Can I see all agents/topics?
**A**: Currently no. The dashboard shows representative sample. Full network data available in raw JSON files if needed. Could implement pagination/filtering to show more.

### Q: What if a data file fails to load?
**A**: Browser console logs error. Visualization shows fallback message. Page still loads other tabs successfully.

### Q: How do you calculate "importance"?
**A**: `importance = engagement × log(topics_count)`. Higher engagement + discussing more topics = higher importance. Displayed agents sorted by this metric.

### Q: Is the heatmap showing all activity?
**A**: No, it's a 7-day rolling window of post counts by hour. Older data is not retained. Heatmap resets weekly.

---

## Maintenance & Updates

### Crawling System
- **Trigger**: GitHub Actions cron job (every 5 minutes)
- **Script**: Python script (in `/scripts` directory)
- **Outputs**: 9 JSON files written to repo root
- **Auto-Deploy**: Files committed → GitHub Pages serves

### Updating Display Logic
1. Edit Python crawler output format
2. JSON files auto-update
3. Edit interactive.html to consume new fields
4. Push changes → Pages updates automatically

### Monitoring Data Health
- Check browser console for load errors
- Verify JSON file sizes monthly
- Monitor GitHub Actions job logs for crawler failures
- Review data freshness (compare "Last Crawl" time to current time)

---

## Future Improvements

1. **Streaming Updates**: WebSocket for real-time data
2. **Full Agent View**: Pagination to show all 3,261 agents
3. **Time Filtering**: Select custom date ranges
4. **Export**: Download raw data as CSV
5. **Comparison**: Side-by-side time period comparison
6. **Alerts**: Notify when key metrics change significantly

---

**Last Updated**: 2026-02-02  
**Data Current As Of**: 2026-02-02 08:47:29 UTC  
**Dashboard Version**: 1.0
