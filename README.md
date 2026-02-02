# 🌳 Moltbook Engagement Hierarchy - Real-Time Discussion Analysis

A real-time visualization of the complete engagement hierarchy on [Moltbook](https://www.moltbook.com) - showing main areas, posts, comments, and replies with full engagement metrics.

**🔴 [View Live Dashboard](https://YOUR_USERNAME.github.io/moltbook-graph/)** | **🔵 [Interactive Explorer](https://YOUR_USERNAME.github.io/moltbook-graph/interactive.html)**

---

## 📊 Complete Data Structure

The system captures the full engagement hierarchy:

```
MAIN AREAS (14 Active Submolts)
├── General (largest: 767+ posts)
│   ├── 🔥 "Built an email-to-podcast skill today" (20,183 comments)
│   │   ├── 195 top-level comments
│   │   │   ├── "Transforming text to audio is underrated..." (90 upvotes)
│   │   │   ├── "Email-to-podcast is genius..." (86 upvotes)
│   │   │   └── ...
│   │   └── 4 replies to comments
│   │
│   ├── 🔥 "The supply chain attack nobody is talking about" (5,379 comments)
│   │   ├── 185 top-level comments
│   │   └── 5 replies to comments
│   │
│   └── [More hot posts ranked by engagement]
│
├── Crab Rave 🦞 (115 posts)
│   ├── 🔥 "🦞🦞🦞" (216 comments)
│   └── [More posts]
│
├── MoltReg - Community First 🦞 (3 posts)
│   ├── 🔥 "OpenClaw: Bringing JARVIS-Like AI Automation..." (395 comments)
│   └── [More posts]
│
└── [10 more active main areas]
```

---

## 🎯 Key Metrics Tracked

### Post Level
- **comment_count**: Total comments in thread
- **upvotes**: Community agreement/quality signal
- **downvotes**: Controversy metric
- **created_at**: Temporal tracking

### Comment Level
- **upvotes**: Comment quality signal
- **reply_count**: How many replies to this comment
- **author.karma**: Commenter reputation

### Reply Level
- **upvotes**: Reply quality
- **author.follower_count**: Reply author influence

---

## 📈 Real Statistics

**Current Data (as of last crawl):**
- **3,230 total topics** in Moltbook system
- **14 active main areas** with posts
- **3,216 dormant topics** (created but no posts yet)
- **5,000+ posts** analyzed per cycle
- **3,389 unique authors** across posts
- **115 topics with activity**
- **Top post**: 20,183 comments, 578,395 upvotes
- **Top author by posts**: Senator_Tommy (21 posts)

---

## 🔄 Data Pipeline

### Collection (Every 5 minutes)

1. **Fetch Posts** (5,000 posts from Moltbook API)
   - Extract: title, author, submolt (main area), created_at
   - Metrics: comment_count, upvotes, downvotes

2. **Fetch Comments** (Top 10 most-discussed posts)
   - Extract: comment author, content, upvotes
   - Identify: top-level comments vs replies
   - Build: reply trees showing discussions

3. **Aggregate Data**
   - Author metrics: post count, total engagement, topic diversity
   - Topic metrics: post frequency, top posts per area
   - Connection metrics: authors sharing topics

### Processing

```python
Engagement Formula (Post Level):
  engagement = comments + (upvotes / 1000)
  # Comments weighted 1000:1 over upvotes (direct engagement vs passive)

Importance Formula (Author Level):
  importance = (replies + 1) × √(topics) × √(posts)
  # Interaction (replies) is primary signal
  # Topic diversity (breadth) is secondary
  # Post frequency (activity) is tertiary
```

### Export (11 JSON files)

| File | Purpose | Records |
|------|---------|---------|
| `network_data.json` | Agent network graph | 200 nodes, 1,368 links |
| `leaderboard_data.json` | Top agents by importance | 50 agents |
| `hottest_posts_per_topic.json` | Top 5 posts per main area | 115 topics |
| `discussion_trees.json` | Full comment/reply trees | 10 posts |
| `topic_data.json` | Topic popularity ranking | 100 topics |
| `connections_data.json` | Top agent connections | 20 pairs |
| `timeline_data.json` | Activity by date | 6+ dates |
| `heatmap_data.json` | Activity by day/hour | 168 cells |
| `agent_history.json` | Growth over time | 100 crawls |
| `agent_history_viz.json` | Agent count trend | Time series |
| `summary_stats.json` | Global metrics | Counters |

---

## 🌐 API Endpoints Used

**Data Source**: [Moltbook.com Public API](https://www.moltbook.com/api/v1)

| Endpoint | Purpose | Used For |
|----------|---------|----------|
| `GET /api/v1/posts?limit=5000` | Fetch recent posts | Core data collection |
| `GET /api/v1/submolts?limit=200` | Fetch all topics/areas | Identifying main areas |
| `GET /api/v1/posts/{id}/comments` | Fetch comments | Discussion extraction |

**No authentication required** - all endpoints are public.

---

## 🎨 Visualizations Available

### 1. **Main Dashboard** (`index.html`)
- Real-time statistics
- Main areas overview
- Hottest posts by area
- Top agents leaderboard
- Live update status

### 2. **Interactive Explorer** (`interactive.html`)
- Zoomable network graph (D3.js)
- Discussion tree browser
- Comment/reply threading
- Author profile cards
- Search & filter functionality

---

## 🔍 How to Use the Dashboard

### Dashboard View
1. **Header**: Live status and last update time
2. **Main Areas Cards**: Click to view hottest posts in each area
3. **Top Posts**: Sort by comments, upvotes, or engagement
4. **Leaderboard**: Agents ranked by importance

### Interactive View
1. **Network Graph**: 
   - Nodes = Authors (size = engagement)
   - Edges = Shared topics
   - Drag to explore, click for details

2. **Discussion Tabs**:
   - View full comment threads
   - See reply relationships
   - Track engagement metrics

3. **Filters**:
   - By main area
   - By date range
   - By engagement level

---

## 💾 Running Locally

### Prerequisites
```bash
python3 (3.8+)
requests library
git
```

### Installation
```bash
git clone https://github.com/YOUR_USERNAME/moltbook-graph.git
cd moltbook-graph
pip install requests
```

### Manual Update
```bash
python3 update_data.py
# Generates all JSON files and commits to GitHub
```

### Automated Updates (Linux/Mac)
```bash
# Install systemd timer
sudo cp moltbook-update.service /etc/systemd/system/
sudo cp moltbook-update.timer /etc/systemd/system/
sudo systemctl enable --now moltbook-update.timer

# Check status
sudo systemctl status moltbook-update.timer
```

---

## 📊 Data Accuracy

### Fields Available from API ✅
- Post metadata: id, title, content, author, created_at
- Engagement: comment_count (100% present), upvotes (100% present)
- Topic info: submolt (main area) with id and display_name
- Author info: id, name, karma (optional), follower_count

### What We DON'T Track ❌
- Direct "likes" or "shares" (not separate fields in API)
- Individual "replies" to posts (API combines as comments)
- Private messages or user accounts
- IP addresses or user tracking

### Data Limitations
- **Sample**: Top 5,000 recent posts per cycle (not exhaustive)
- **Comments**: Only fetching top 10 most-discussed posts (rate limit)
- **Rate Limiting**: 5-minute minimum between crawls (API consideration)
- **Historical**: Keeping last 100 crawls for trend analysis

---

## 🔐 Privacy & Ethics

✅ **Only uses public API data**
✅ **No user authentication stored**
✅ **No private data accessed**
✅ **Respects Moltbook Terms of Service**
✅ **5-minute crawl delay** (rate limiting)

---

## 🚀 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Data Collection** | Python 3 + requests | API crawling |
| **Storage** | JSON files | Lightweight, version-controllable |
| **Scheduling** | systemd timer | Automated 5-minute updates |
| **Frontend (Dashboard)** | HTML5 + CSS3 + vanilla JS | Static page hosting |
| **Frontend (Interactive)** | D3.js v7 + vanilla JS | Network visualization |
| **Deployment** | GitHub Pages | Free static hosting |
| **Version Control** | Git + GitHub | Automated commits |

---

## 📈 Performance

- **Data Fetch Time**: ~30 seconds (5,000 posts)
- **Comment Fetching**: ~60 seconds (10 posts × comments)
- **Processing**: ~15 seconds (aggregation)
- **File Export**: ~5 seconds (11 JSON files)
- **Git Push**: ~10 seconds
- **Total Cycle**: ~2 minutes
- **Frequency**: Every 5 minutes
- **Data Staleness**: Max 5 minutes

---

## 🔧 Customization

### Change Update Frequency
Edit `update_data.py`:
```python
# Line 68: Adjust post fetch limit
max_posts = 10000  # Default: 5000
```

### Change Discussed Posts Sample
Edit `update_data.py`:
```python
# Line 148: Adjust comment tree sample size
top_posts = sorted(...)[:20]  # Default: 10
```

### Change Exported Topics
Edit `update_data.py`:
```python
# Line 234: Adjust leaderboard size
top_agents = ...[:100]  # Default: 50
```

---

## 🐛 Troubleshooting

### Data not updating
```bash
# Check if pipeline is running
sudo systemctl status moltbook-update.timer

# Run manually to test
python3 update_data.py

# Check logs
sudo journalctl -u moltbook-update -n 50
```

### API connection errors
```bash
# Test API connectivity
curl https://www.moltbook.com/api/v1/posts?limit=1

# Check network
ping -c 1 www.moltbook.com
```

### Git push failures
```bash
# Verify credentials
git config user.name
git config user.email

# Test push manually
git push origin main
```

---

## 📚 Related Documentation

- [FAST_PIPELINE.md](FAST_PIPELINE.md) - Pipeline architecture
- [DATA_ANALYSIS_REPORT.md](DATA_ANALYSIS_REPORT.md) - Data discovery findings
- [IMPORTANCE_METRICS.md](IMPORTANCE_METRICS.md) - Ranking methodology
- [DATA_QUICK_REFERENCE.md](DATA_QUICK_REFERENCE.md) - Field reference

---

## 🤝 Contributing

Contributions welcome! To improve the dashboard:

1. Fork the repository
2. Create a feature branch
3. Update files locally
4. Test with `python3 update_data.py`
5. Submit a pull request

---

## 📞 Support

For issues with:
- **Moltbook API**: Check [moltbook.com](https://www.moltbook.com)
- **This project**: GitHub Issues
- **Data questions**: See DATA_ANALYSIS_REPORT.md

---

## 📄 License

This project visualizes public API data from Moltbook.com. 
Licensed under MIT.

---

**Last Updated**: 2026-02-02  
**Crawl Cycle**: Every 5 minutes  
**Data Source**: Moltbook.com Public API  
**Auto-commits**: Enabled via GitHub Actions

🌳 Real-time. Transparent. Community-driven.
