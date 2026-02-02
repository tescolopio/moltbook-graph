# 📊 Moltbook API Data Analysis Report

## Key Findings

### What Data IS Available ✅

1. **Posts** - 1000 analyzed
   - Fields: id, title, content, author, submolt, created_at
   - Timestamps: YES ✅ (can track temporal patterns)
   - URLs: Mostly empty (only 0.5%)

2. **Authors** 
   - 836 unique authors in sample
   - Field: `author.id` and `author.name`
   - Top author: Senator_Tommy (21 posts)
   - **Can rank by: post count, post frequency, topic diversity**

3. **Topics (Submolts)**
   - 39 unique topics  
   - Fields: `submolt.id`, `submolt.name`, `submolt.display_name`
   - Topic distribution very skewed: 767/1000 posts in "general" (77%)
   - **Can rank topics by: post frequency, agent diversity**

### What Data is NOT Available ❌

| Metric | Status | Notes |
|--------|--------|-------|
| Likes | ❌ NO | Field "upvotes" exists but shows as 0 or not in replies |
| Replies | ❌ NO | Not available in posts endpoint |
| Comments | ❌ NO | Field exists but shows 0 |
| Engagement | ❌ NO | No engagement metric |
| Interactions | ❌ NO | No interaction counts |
| Shares | ❌ NO | Not available |

---

## What We CAN Display

### 1. **Activity by Author** ✅ 
- Post count per author (21, 7, 6, 6, 5... posts)
- **Use for:** Ranking active contributors

### 2. **Topic Diversity** ✅
- Which topics each author participates in
- Authors appear in multiple topics
- **Use for:** Show breadth of knowledge

### 3. **Topic Popularity** ✅
- Posts per topic (767 general, 115 crab-rave, 22 introductions, etc)
- **Use for:** Bubble chart of topic activity

### 4. **Temporal Patterns** ✅
- Post creation timestamps available
- **Use for:** Timeline of when posts created, activity heatmap by time

### 5. **Network Connections** ✅
- Agents → Topics (shared topic participation)
- Agents → Agents (authors in same topics = potential collaborators)
- **Use for:** Network graph showing collaboration

---

## Recommended Ranking Strategy

### Since interaction metrics (replies/likes) are unavailable, use:

#### **PRIMARY SIGNAL: Post Volume + Topic Diversity**
```
Importance Score = Posts × √(Unique Topics)
```

Example:
- Senator_Tommy: 21 posts × √9 topics = 21 × 3 = 63 points ⭐
- Shellraiser: 7 posts × √4 topics = 7 × 2 = 14 points
- eudaemon_0: 6 posts × √3 topics = 6 × 1.7 = 10 points

**Why this works:**
✅ Rewards activity (post count)
✅ Rewards breadth (topic diversity)  
✅ Combines quantity + quality
✅ Based on actual available data

#### **SECONDARY SIGNALS:**

1. **Recency** - Recent posts weighted higher (last week = 2x multiplier)
2. **Topic-specific leadership** - Top author in each topic
3. **Network centrality** - Authors with most cross-topic connections

---

## Data Distribution

```
POST VOLUME (per author):
  Senator_Tommy:        21 posts (2.1% of sample)
  Shellraiser:           7 posts (0.7%)
  eudaemon_0:            6 posts (0.6%)
  [Average]:           1.2 posts per author
  
TOPIC DISTRIBUTION:
  general:            767 posts (76.7%) ← DOMINANT
  crab-rave:          115 posts (11.5%)
  introductions:       22 posts (2.2%)
  [All others]:        96 posts (9.6%)
  
TOPIC DIVERSITY (authors):
  High: Authors with 6+ topics
  Medium: Authors with 3-5 topics
  Low: Authors with 1-2 topics
```

---

## Visual Representations Available

### 1. **Leaderboard** (Activity)
```
Rank | Agent              | Posts | Topics | Score
-----|------------------|-------|--------|--------
  1  | Senator_Tommy    |  21   |   9    |   63 ⭐
  2  | Shellraiser      |   7   |   4    |   14
  3  | eudaemon_0       |   6   |   3    |   10
```

### 2. **Network Graph** (Collaboration)
- Nodes = Authors
- Edges = Shared topics
- Size = Post count
- Color = Topic diversity

### 3. **Topic Bubble Chart** (Activity)
```
Bubble Size = Posts in topic
  General (767 posts) - HUGE
  Crab-rave (115 posts) - Medium
  Introductions (22 posts) - Small
  ...
```

### 4. **Timeline** (Temporal Patterns)
```
Posts per day/week
Activity heatmap (time of day × day of week)
Growth trend (cumulative posts over time)
```

### 5. **Topic Leadership** (Per-topic top authors)
```
GENERAL TOPIC:
  1. Senator_Tommy (21 posts in general)
  2. [Other authors...]
  
CRAB-RAVE TOPIC:
  1. [Top author in crab-rave]
  ...
```

---

## Current Implementation Status

### What We're Using Now:
- ✅ Post count (number of posts per author)
- ✅ Topic diversity (unique topics per author)
- ✅ Topic popularity (posts per topic)
- ✅ Timestamps (for timeline/heatmap)
- ✅ Author-topic connections (for network)

### What's Missing:
- ❌ Interaction metrics (API doesn't provide)
- ❌ Real engagement signals (not available)

### Workaround:
Use **activity + breadth** as proxy for importance:
- Active contributors (many posts)
- Broad thinkers (many topics)
- Early participants (temporal signal)

---

## Recommended Updates to Dashboard

### 1. **Primary Ranking: Activity + Breadth**
```
Leaderboard shows:
  • Posts (activity)
  • Topics (breadth)
  • Importance Score (combined)
  • Join date / first post (tenure)
```

### 2. **Add Context Labels**
```
"Based on: Post count + Topic diversity"
(Interaction metrics not available from API)
```

### 3. **New Visualizations**
```
• Topic heatmap (topics × authors)
• Temporal activity (when posts created)
• Topic leadership (top author per topic)
• Agent collaboration network
```

### 4. **Filters**
```
• Minimum posts (show only active authors)
• Topic filter (show authors in specific topics)
• Date range (show posts in time window)
• High/low activity (trending up/down)
```

---

## Caveats & Limitations

1. **No Real Engagement Data**
   - API doesn't return likes/replies/comments on posts
   - Using activity volume as proxy
   - True influence unknown

2. **Skewed Topic Distribution**
   - 77% of posts in "general" topic
   - Limits topic-specific insights
   - Most authors have 1-3 posts

3. **Sample Bias**
   - Analysis based on 1000 recent posts
   - May not represent historical patterns
   - Only 836 unique authors in sample

4. **Limited Interaction Context**
   - Can't see post-to-post conversations
   - Can't measure influence (who persuaded whom)
   - Can't detect quality of contributions

---

## Next Steps

1. **Update update_data.py** to use:
   - Activity (posts) × Breadth (topics) formula
   - Temporal weighting (recent = more important)
   - Topic-specific rankings

2. **Enhance dashboard** with:
   - "Score breakdown" showing posts + topics
   - "About this ranking" section explaining methodology
   - Caveat that engagement metrics unavailable

3. **Monitor for API improvements**
   - If interaction data becomes available, re-rank automatically
   - Keep formula ready for when data becomes rich

4. **Document limitations**
   - Add "Data Quality" section
   - Show "what we can't see"
   - Explain proxy metrics

---

## Summary

**Best Metric with Available Data:**
```
Importance = Posts × √(Topics) × Recency_Factor
```

**Why this is the best choice:**
- ✅ Data actually available
- ✅ Captures activity (posts)
- ✅ Captures breadth (topics)
- ✅ Rewards recent contributions
- ✅ Fair and transparent
- ✅ Can improve when more data available

**Result:** Solid leaderboard showing most active, broadest contributors
