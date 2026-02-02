#!/usr/bin/env python3
"""
Fast Moltbook Data Pipeline - Direct API to GitHub

Fetches only IMPORTANT data from Moltbook API and exports directly to JSON.
Skips Neo4j entirely. Commits and pushes to GitHub automatically.

Runs: Every 5 minutes via cron or systemd timer
"""

import requests
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from collections import defaultdict
import sys

class FastMoltbookPipeline:
    def __init__(self, output_dir=None):
        self.base_url = "https://www.moltbook.com"
        repo_root = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = output_dir or os.path.join(repo_root, "data")
        os.makedirs(self.output_dir, exist_ok=True)

        # Allow overriding max post cap (0 = no cap)
        try:
            env_max_posts = int(os.getenv("MAX_POSTS", "0"))
        except ValueError:
            env_max_posts = 0
        self.max_posts = env_max_posts if env_max_posts > 0 else None

        self.session = requests.Session()
        self.session.timeout = 15
        
        # Data containers - ONLY store important data
        self.posts = []
        self.agents = {}
        self.topics = defaultdict(int)
        self.topic_engagement = defaultdict(int)
        self.topic_agents = defaultdict(set)
        self.agent_engagement = defaultdict(int)
        self.agent_topics = defaultdict(set)
        self.connections = {}
        # Last crawl timestamp for incremental fetch
        self.last_crawl_dt = None
        try:
            history_path = os.path.join(self.output_dir, 'agent_history.json')
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    history = json.load(f)
                ts = history.get('summary', {}).get('last_crawl')
                if ts:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    self.last_crawl_dt = dt
        except Exception:
            self.last_crawl_dt = None
        
    def fetch(self, endpoint, params=None):
        """Fetch from Moltbook API."""
        try:
            url = f"{self.base_url}/api/v1{endpoint}"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ API Error ({endpoint}): {e}")
            return None
    
    def crawl(self, max_posts=None):
        """Fetch and aggregate data from Moltbook API."""
        print("\n🚀 FAST MOLTBOOK PIPELINE")
        print("="*60)
        
        # Fetch posts with pagination
        print("📥 Fetching posts...")
        all_posts = []
        offset = 0
        fetches = 0
        max_posts = max_posts if max_posts is not None else self.max_posts

        while True:
            if max_posts is not None and len(all_posts) >= max_posts:
                break

            data = self.fetch("/posts", {"offset": offset, "limit": 100})
            if not data or not data.get('success'):
                break
            
            posts = data.get('posts') or data.get('data', {}).get('posts', [])
            if not posts:
                break

            # Incremental: keep only posts newer than last crawl
            if self.last_crawl_dt:
                filtered_posts = []
                for p in posts:
                    created_str = p.get('created_at') or p.get('created') or ''
                    try:
                        created_dt = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                        if created_dt.tzinfo is None:
                            created_dt = created_dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        created_dt = None
                    if created_dt and created_dt <= self.last_crawl_dt:
                        # Assume API is descending; stop pagination here
                        posts = None
                        break
                    filtered_posts.append(p)
                if posts is None:
                    all_posts.extend(filtered_posts)
                    break
                posts = filtered_posts

            all_posts.extend(posts)
            offset += 100
            fetches += 1
            
            if len(all_posts) % 500 == 0:
                print(f"   Fetched {len(all_posts)} posts...")
        
        print(f"✅ Got {len(all_posts)} posts from API" + (" (capped)" if max_posts else ""))
        if len(all_posts) == 0:
            # Avoid wiping data when the API is down; keep previous exports intact
            print("❌ No posts fetched; skipping export to preserve existing data")
            return False
        
        # Process posts ONCE - build all data in one pass
        print("🔍 Processing data...")
        missing_author_posts = []

        for post in all_posts:
            if not post:
                continue

            author_info = post.get('author')
            author = author_info.get('name') if isinstance(author_info, dict) else None

            # Author is required by API; if missing, skip and log for visibility
            if not author:
                missing_author_posts.append(post.get('id'))
                continue
            submolt_data = post.get('submolt', {})
            # Handle submolt as either dict or string
            submolt = submolt_data.get('name') if isinstance(submolt_data, dict) else str(submolt_data)
            submolt = submolt or 'General'
            
            # Calculate engagement from POST-level metrics (comments + upvotes)
            # This is the "hotness" score for individual posts/topics
            comments = post.get('comment_count', post.get('comments', 0))
            upvotes = post.get('upvotes', 0)
            
            # Engagement formula: comments are direct engagement, upvotes are agreement
            # Weight comments more heavily as they show actual discussion
            post_engagement = comments + (upvotes // 1000)  # 1000 upvotes ≈ 1 comment value
            
            if author:
                # Track agent data
                agent_id = author.lower()
                if agent_id not in self.agents:
                    self.agents[agent_id] = {'name': author, 'posts': 0, 'engagement': 0, 'topics': 0}
                
                self.agents[agent_id]['posts'] += 1
                self.agents[agent_id]['engagement'] += post_engagement  # Aggregate author's post engagement
                self.agent_engagement[agent_id] += post_engagement
                self.agent_topics[agent_id].add(submolt)
            
            # Track topics (main areas)
            if submolt:
                self.topics[submolt] += 1
                self.topic_engagement[submolt] += post_engagement
                if agent_id:
                    self.topic_agents[submolt].add(agent_id)
            
            # Store post with engagement metrics
            self.posts.append({
                'id': post.get('id'),
                'title': post.get('title', ''),
                'author': author,
                'submolt': submolt,
                'tags': [submolt] if submolt else [],
                'engagement': post_engagement,
                'comments': comments,
                'upvotes': upvotes,
                'created': post.get('created_at', '')
            })
        
        # Build connections (only for top 200 agents to save processing)
        print("🔗 Building connections...")
        top_200 = sorted(self.agents.keys(), 
                        key=lambda a: self.agents[a]['engagement'],
                        reverse=True)[:200]
        
        for i, a1 in enumerate(top_200):
            for a2 in top_200[i+1:]:
                shared = self.agent_topics[a1] & self.agent_topics[a2]
                if shared:
                    key = f"{a1}:{a2}"
                    self.connections[key] = {
                        'agent1': a1,
                        'agent2': a2,
                        'shared_topics': list(shared),
                        'count': len(shared)
                    }
        
        if missing_author_posts:
            print(f"⚠️  Skipped {len(missing_author_posts)} posts missing required author (samples: {missing_author_posts[:5]})")

        print(f"✅ {len(self.agents)} agents, {len(self.topics)} topics")
        return True
    
    def save_json(self, filename, data):
        """Save JSON file."""
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w') as f:
            json.dump(data, f, default=str)

    def clean_outputs(self):
        """Post-process exported JSONs to normalize fields for the front-end."""
        def load_json(name, default):
            try:
                with open(os.path.join(self.output_dir, name), 'r') as f:
                    return json.load(f)
            except Exception:
                return default

        # connections_data.json: ensure fields and sample_topics
        connections = load_json('connections_data.json', [])
        cleaned_connections = []
        for c in connections:
            a1 = c.get('agent1') or (c.get('agents') or [None, None])[0]
            a2 = c.get('agent2') or (c.get('agents') or [None, None])[1]
            if not a1 or not a2:
                continue
            shared = c.get('shared_topics') or c.get('shared') or []
            if not isinstance(shared, list):
                shared = [shared] if shared else []
            sample = shared[:4]
            count = c.get('count') or c.get('weight') or len(shared) or 0
            cleaned_connections.append({
                'agent1': a1,
                'agent2': a2,
                'shared_topics': shared,
                'count': int(count),
                'sample_topics': sample
            })
        self.save_json('connections_data.json', cleaned_connections)

        # timeline_data.json: sort by date and keep {date, count}
        timeline = load_json('timeline_data.json', [])
        cleaned_timeline = []
        for row in timeline:
            date = row.get('date') or row.get('time')
            count = row.get('count', 0)
            if date:
                cleaned_timeline.append({'date': date, 'count': int(count)})
        cleaned_timeline.sort(key=lambda r: r['date'])
        self.save_json('timeline_data.json', cleaned_timeline)

        # agent_history_viz.json: ensure posts field exists
        hist = load_json('agent_history_viz.json', [])
        cleaned_hist = []
        for row in hist:
            ts = row.get('timestamp') or row.get('time')
            agents = int(row.get('agents', 0))
            posts = int(row.get('posts', 0)) if 'posts' in row else 0
            if agents <= 0 or posts <= 0 or not ts:
                continue  # Drop zero/empty samples that break growth trend
            cleaned_hist.append({'timestamp': ts, 'agents': agents, 'posts': posts})

        # Drop partial runs: keep only entries near the max posts observed
        if cleaned_hist:
            max_posts = max(r['posts'] for r in cleaned_hist)
            threshold = max_posts * 0.8  # keep runs with >=80% of max posts
            cleaned_hist = [r for r in cleaned_hist if r['posts'] >= threshold]

        # Sort by timestamp string; if ISO this is stable
        cleaned_hist.sort(key=lambda r: r['timestamp'])
        self.save_json('agent_history_viz.json', cleaned_hist)

        # heatmap_data.json: ensure full 7x24 grid
        heatmap = load_json('heatmap_data.json', [])
        grid = {(cell.get('day'), cell.get('hour')): cell.get('count', 0) for cell in heatmap}
        full = []
        for d in range(7):
            for h in range(24):
                full.append({'day': d, 'hour': h, 'count': int(grid.get((d, h), 0))})
        self.save_json('heatmap_data.json', full)

        # summary_stats.json: coerce numeric fields and keep required keys
        summary = load_json('summary_stats.json', {})
        for key in ['total_agents', 'total_topics', 'total_posts', 'total_connections', 'total_engagement']:
            summary[key] = int(summary.get(key, 0))
        self.save_json('summary_stats.json', summary)

        # leaderboard_data.json: enforce numeric metrics and non-empty names
        leaderboard = load_json('leaderboard_data.json', [])
        cleaned_lb = []
        for row in leaderboard:
            name = row.get('name') or row.get('agent')
            if not name:
                continue
            cleaned_lb.append({
                'rank': int(row.get('rank', len(cleaned_lb) + 1)),
                'name': name,
                'engagement': int(row.get('engagement', 0)),
                'posts': int(row.get('posts', 0)),
                'topics': int(row.get('topics', 0)),
                'importance': float(row.get('importance', 0.0))
            })
        self.save_json('leaderboard_data.json', cleaned_lb[:50])

        # topic_network_data.json: ensure weights and drop zero-weight links
        topic_net = load_json('topic_network_data.json', {'nodes': [], 'links': []})
        cleaned_nodes = []
        for n in topic_net.get('nodes', []):
            nid = n.get('id') or n.get('topic')
            if not nid or str(nid).lower() == 'general':
                continue  # Drop generic bucket entirely
            n['id'] = nid
            n['posts'] = int(n.get('posts', 0))
            n['engagement'] = int(n.get('engagement', 0))
            n['agents'] = int(n.get('agents', 0))
            cleaned_nodes.append(n)
        valid_topics = {n['id'] for n in cleaned_nodes}
        cleaned_links = []
        for l in topic_net.get('links', []):
            src = l.get('source')
            tgt = l.get('target')
            if src not in valid_topics or tgt not in valid_topics:
                continue
            w = l.get('weight') or l.get('shared_agents') or l.get('value') or 0
            if w:
                cleaned_links.append({
                    'source': src,
                    'target': tgt,
                    'weight': int(w),
                    'shared_agents': int(w)
                })
        topic_net['nodes'] = cleaned_nodes
        topic_net['links'] = cleaned_links
        self.save_json('topic_network_data.json', topic_net)

        # topic_data.json: keep required fields and aliases
        topics = load_json('topic_data.json', [])
        cleaned_topics = []
        for t in topics:
            name = t.get('topic') or t.get('name')
            if not name or str(name).lower() == 'general':
                continue  # Drop generic bucket entirely
            cleaned_topics.append({
                'topic': name,
                'name': name,
                'posts': int(t.get('posts', t.get('value', 0))),
                'value': int(t.get('posts', t.get('value', 0))),
                'engagement': int(t.get('engagement', 0)),
                'agents': int(t.get('agents', 0)),
                'hot': bool(t.get('hot', False)),
                'size': int(t.get('size', 0) or 0),
                'submolts': t.get('submolts', 1)
            })
        self.save_json('topic_data.json', cleaned_topics)

        # word_cloud_data.json: drop generic bucket if present
        word_cloud = load_json('word_cloud_data.json', [])
        cleaned_wc = [w for w in word_cloud if str(w.get('text', '')).lower() != 'general']
        self.save_json('word_cloud_data.json', cleaned_wc)
    
    def build_discussion_trees(self):
        """Fetch comment/reply trees for top posts (limited for performance)."""
        print("🌳 Building discussion trees for top posts...")
        
        discussion_trees = {}
        
        # Only fetch trees for top 10 most-commented posts (to stay within API rate limits)
        top_posts = sorted(self.posts, key=lambda p: p.get('comments', 0), reverse=True)[:10]
        
        for post in top_posts:
            post_id = post.get('id')
            
            try:
                # Fetch comments for this post
                response = self.session.get(
                    f"{self.base_url}/api/v1/posts/{post_id}/comments",
                    params={"limit": 200, "sort": "top"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    comments_data = response.json()
                    comments = comments_data.get('comments', [])
                    
                    # Separate top-level comments and replies
                    top_level = [c for c in comments if c.get('parent_id') is None]
                    replies = [c for c in comments if c.get('parent_id') is not None]
                    
                    # Build reply tree
                    reply_tree = defaultdict(list)
                    for reply in replies:
                        parent_id = reply.get('parent_id')
                        reply_tree[parent_id].append({
                            'id': reply.get('id'),
                            'author': reply.get('author', {}).get('name', 'unknown'),
                            'content': reply.get('content', '')[:150],
                            'upvotes': reply.get('upvotes', 0),
                            'created_at': reply.get('created_at', '')
                        })
                    
                    discussion_trees[post_id] = {
                        'post_title': post.get('title', ''),
                        'post_author': post.get('author', ''),
                        'submolt': post.get('submolt', ''),
                        'total_comments': comments_data.get('count', 0),
                        'top_level_comments_fetched': len(top_level),
                        'replies_fetched': len(replies),
                        'top_comments': [
                            {
                                'id': c.get('id'),
                                'author': c.get('author', {}).get('name', 'unknown'),
                                'content': c.get('content', '')[:150],
                                'upvotes': c.get('upvotes', 0),
                                'created_at': c.get('created_at', ''),
                                'reply_count': len(reply_tree.get(c.get('id'), []))
                            }
                            for c in top_level[:5]
                        ]
                    }
                    
                    print(f"   ✓ {post.get('title', '')[:60]}... ({len(top_level)} comments, {len(replies)} replies)")
            except Exception as e:
                print(f"   ⚠️  Error fetching comments for {post_id}: {str(e)[:50]}")
                continue
        
        return discussion_trees
    
    def export_all(self):
        """Export all JSON files."""
        print("💾 Exporting JSON files...")
        
        # Calculate importance score for each agent
        # Importance = replies (interaction) × topic_diversity × activity_level
        import math
        
        agent_importance = {}
        for agent_id, agent_data in self.agents.items():
            topic_diversity = len(self.agent_topics[agent_id])
            post_freq = agent_data['posts']
            replies = agent_data['engagement']  # Direct replies/comments (interaction)
            
            # Importance formula: Replies (interaction) is the primary signal
            # replies × sqrt(topics) × sqrt(posts)
            # Higher replies = much more important
            # Broader topics = somewhat more important  
            # More posts = somewhat more important
            importance = (replies + 1) * math.sqrt(max(1, topic_diversity)) * math.sqrt(max(1, post_freq))
            agent_importance[agent_id] = importance
        
        # 1. Network data (top 200 agents + connections)
        top_agents = sorted(
            [(k, v) for k, v in self.agents.items()],
            key=lambda x: agent_importance.get(x[0], 0),
            reverse=True
        )[:200]
        
        nodes = [
            {
                'id': aid,
                'name': data['name'],
                'posts': data['posts'],
                'engagement': data['engagement'],  # Replies/comments (interaction)
                'importance': agent_importance.get(aid, 0),
                'topics': len(self.agent_topics[aid]),
                'size': max(3, int(math.sqrt(data['engagement'] + 1)) * 2),  # Sqrt scale for replies
                'value': data['engagement'] + len(self.agent_topics[aid]) * 5  # Interaction-weighted
            }
            for aid, data in top_agents
        ]
        
        top_agent_ids = {aid for aid, _ in top_agents}
        links = [
            {
                'source': c['agent1'],
                'target': c['agent2'],
                'weight': c['count']
            }
            for c in sorted(self.connections.values(),
                          key=lambda x: x['count'],
                          reverse=True)[:1500]
            if c['agent1'] in top_agent_ids and c['agent2'] in top_agent_ids
        ]
        
        self.save_json('network_data.json', {'nodes': nodes, 'links': links})
        print(f"   ✓ network_data.json ({len(nodes)} nodes, {len(links)} links)")
        
        # 2. Topic data (top 100 with engagement + agent counts) — exclude the generic "general" bucket
        top_topics_all = sorted(self.topics.items(), key=lambda x: x[1], reverse=True)
        top_topics = [(t, c) for t, c in top_topics_all if t != 'general'][:100]
        topics_data = []
        for topic, count in top_topics:
            engagement = self.topic_engagement.get(topic, 0)
            agents = len(self.topic_agents.get(topic, []))
            topics_data.append({
                'topic': topic,
                'name': topic,           # backward compatible key
                'posts': count,
                'value': count,          # backward compatible key
                'engagement': engagement,
                'agents': agents,
                'size': max(6, int(math.sqrt(count)) * 2 + 2),
                'hot': engagement >= 50 or count >= 75,
                'submolts': 1
            })
        self.save_json('topic_data.json', topics_data)
        print(f"   ✓ topic_data.json ({len(topics_data)} topics)")

        # 2a. Topic network (top 80 topics, edges = shared participating agents)
        top_topic_ids = [t for t, _ in top_topics[:80]]
        topic_nodes = []
        for topic in top_topic_ids:
            posts = self.topics.get(topic, 0)
            engagement = self.topic_engagement.get(topic, 0)
            agents = len(self.topic_agents.get(topic, []))
            topic_nodes.append({
                'id': topic,
                'topic': topic,
                'posts': posts,
                'engagement': engagement,
                'agents': agents,
                'value': posts,
                'hot': engagement >= 50 or posts >= 75,
                'size': max(5, int(math.sqrt(posts)) * 2 + 2)
            })

        topic_agent_map = {t: self.topic_agents.get(t, set()) for t in top_topic_ids}
        topic_links = []
        for i, t1 in enumerate(top_topic_ids):
            agents1 = topic_agent_map[t1]
            for t2 in top_topic_ids[i+1:]:
                shared_agents = agents1 & topic_agent_map[t2]
                shared_count = len(shared_agents)
                if shared_count >= 1:
                    topic_links.append({
                        'source': t1,
                        'target': t2,
                        'weight': shared_count,
                        'shared_agents': shared_count
                    })

        topic_links = sorted(topic_links, key=lambda l: l['weight'], reverse=True)[:1500]
        self.save_json('topic_network_data.json', {'nodes': topic_nodes, 'links': topic_links})
        print(f"   ✓ topic_network_data.json ({len(topic_nodes)} topics, {len(topic_links)} links)")
        
        # 3. Leaderboard (top 50 by importance)
        leaderboard = [
            {
                'rank': i+1,
                'name': data['name'],
                'engagement': data['engagement'],
                'posts': data['posts'],
                'topics': len(self.agent_topics[aid]),
                'importance': agent_importance.get(aid, 0)
            }
            for i, (aid, data) in enumerate(top_agents[:50])
        ]
        self.save_json('leaderboard_data.json', leaderboard)
        print(f"   ✓ leaderboard_data.json ({len(leaderboard)} agents)")
        
        # 4. Top connections (20)
        top_conns = sorted(self.connections.values(), 
                          key=lambda x: x['count'], reverse=True)[:20]
        conns_data = [
            {
                'agent1': c['agent1'],
                'agent2': c['agent2'],
                'shared_topics': c['shared_topics'],
                'count': c['count']
            }
            for c in top_conns
        ]
        self.save_json('connections_data.json', conns_data)
        print(f"   ✓ connections_data.json ({len(conns_data)} connections)")
        
        # 5. Summary stats
        summary = {
            'total_agents': len(self.agents),
            'total_topics': len(self.topics),
            'total_posts': len(self.posts),
            'total_connections': len(self.connections),
            'total_engagement': sum(a['engagement'] for a in self.agents.values()),
            'crawled_at': datetime.now(timezone.utc).isoformat()
        }
        self.save_json('summary_stats.json', summary)
        print(f"   ✓ summary_stats.json")

        # 5a. API stats snapshot and parity check
        api_stats = self.fetch('/stats')
        if api_stats:
            self.save_json('api_stats.json', api_stats)

            # Optional parity comparison against pipeline counts
            parity = {
                'pipeline': {
                    'posts': len(self.posts),
                    'agents': len(self.agents),
                    'topics': len(self.topics)
                },
                'api_stats': {
                    'posts': api_stats.get('posts'),
                    'agents': api_stats.get('agents'),
                    'topics': api_stats.get('submolts')
                },
                'delta': {}
            }

            for key, api_key in [('posts', 'posts'), ('agents', 'agents'), ('topics', 'submolts')]:
                p_val = parity['pipeline'][key]
                a_val = parity['api_stats'].get(api_key)
                if isinstance(a_val, (int, float)):
                    parity['delta'][key] = p_val - a_val

            self.save_json('api_stats_parity.json', parity)
            print(f"   ✓ api_stats.json + api_stats_parity.json")
        else:
            print("   ⚠️  /api/v1/stats unavailable; skipped api_stats.json")

        # 5b. Agent posting stats (for visualization of active vs total agents)
        active_agents = len(self.agents)
        agents_with_engagement = sum(1 for a in self.agents.values() if a['engagement'] > 0)
        total_posts = len(self.posts)
        avg_posts_per_agent = total_posts / active_agents if active_agents else 0
        top_posters = sorted(
            [(k, v) for k, v in self.agents.items()],
            key=lambda x: x[1]['posts'],
            reverse=True
        )[:20]
        agent_posting_stats = {
            'total_agents': active_agents,
            'agents_with_engagement': agents_with_engagement,
            'total_posts': total_posts,
            'avg_posts_per_agent': avg_posts_per_agent,
            'top_posters': [
                {
                    'name': data['name'],
                    'posts': data['posts'],
                    'engagement': data['engagement'],
                    'topics': len(self.agent_topics[aid])
                }
                for aid, data in top_posters
            ]
        }
        self.save_json('agent_posting_stats.json', agent_posting_stats)
        print(f"   ✓ agent_posting_stats.json")
        
        # 6. Agent history (track growth)
        history_file = os.path.join(self.output_dir, 'agent_history.json')
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except:
            history = {'crawls': [], 'summary': {}}
        
        crawl_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_agents': len(self.agents),
            'total_posts': len(self.posts),
            'total_topics': len(self.topics),
            'total_relationships': len(self.connections)
        }
        history['crawls'].append(crawl_entry)
        history['crawls'] = history['crawls'][-100:]  # Keep last 100
        history['summary'] = {
            'first_crawl': history['crawls'][0]['timestamp'],
            'last_crawl': crawl_entry['timestamp'],
            'total_crawls': len(history['crawls']),
            'max_agents': max(c['total_agents'] for c in history['crawls']),
            'min_agents': min(c['total_agents'] for c in history['crawls'])
        }
        self.save_json('agent_history.json', history)
        print(f"   ✓ agent_history.json (crawl #{len(history['crawls'])})")
        
        # 7. Growth trend (for visualization)
        growth = [{'timestamp': c['timestamp'], 'agents': c['total_agents']}
                 for c in history['crawls']]
        # Include posts to support dual-line growth chart
        for i, c in enumerate(history['crawls']):
            growth[i]['posts'] = c.get('total_posts', 0)
        self.save_json('agent_history_viz.json', growth)
        
        # 8. Timeline (dates with activity)
        dates = defaultdict(int)
        for post in self.posts:
            created = post.get('created', '')
            if created:
                date = created.split('T')[0]
                dates[date] += 1
        
        timeline = [
            {'date': d, 'count': c}
            for d, c in sorted(dates.items())
        ]
        self.save_json('timeline_data.json', timeline)
        print(f"   ✓ timeline_data.json ({len(timeline)} dates)")
        
        # 9. Heatmap (24h x 7d)
        heatmap = [[0]*24 for _ in range(7)]
        for post in self.posts:
            try:
                dt = datetime.fromisoformat(post.get('created', '').replace('Z', '+00:00'))
                day, hour = dt.weekday(), dt.hour
                if 0 <= day < 7 and 0 <= hour < 24:
                    heatmap[day][hour] += 1
            except:
                pass
        
        heatmap_data = [
            {'day': d, 'hour': h, 'count': heatmap[d][h]}
            for d in range(7) for h in range(24)
        ]
        self.save_json('heatmap_data.json', heatmap_data)
        print(f"   ✓ heatmap_data.json (168 cells)")
        
        # 10. Hottest posts per topic (main areas)
        posts_by_topic = defaultdict(list)
        for post in self.posts:
            topic = post.get('submolt', 'General')
            posts_by_topic[topic].append(post)
        
        # Get top 5 posts per topic, sorted by engagement
        hottest_per_topic = {}
        for topic, posts in posts_by_topic.items():
            sorted_posts = sorted(posts, key=lambda p: p.get('engagement', 0), reverse=True)
            hottest_per_topic[topic] = [
                {
                    'id': p['id'],
                    'title': p['title'],
                    'author': p['author'],
                    'engagement': p['engagement'],
                    'comments': p.get('comments', 0),
                    'upvotes': p.get('upvotes', 0),
                    'created': p.get('created', '')
                }
                for p in sorted_posts[:5]
            ]
        
        self.save_json('hottest_posts_per_topic.json', hottest_per_topic)
        print(f"   ✓ hottest_posts_per_topic.json ({len(hottest_per_topic)} topics)")

        # 10b. Title word cloud (top 100 words weighted by engagement)
        title_word_counts = defaultdict(float)
        stopwords = {
            'the','and','for','with','this','that','from','just','into','your','you','are','our','has','have','was','were','but','not','out','all','any','can','will','about','what','when','how','why','who','their','they','them','his','her','its','its','on','in','of','to','a','an','is','it','at','by','as','be','or','if','do','did','done','so','we','us','my','me','up','down','over','under','new','more','less'
        }
        for post in self.posts:
            title = post.get('title') or ''
            engagement = post.get('engagement', 0) or 0
            weight = max(1, engagement)
            for token in re.findall(r"[A-Za-z0-9']+", title):
                word = token.lower()
                if len(word) < 3 or word in stopwords:
                    continue
                title_word_counts[word] += weight

        top_title_words = sorted(title_word_counts.items(), key=lambda x: x[1], reverse=True)[:100]
        title_word_cloud = [
            {
                'text': w,
                'value': v,
                'size': max(12, min(72, math.log(v + 1) * 8))
            }
            for w, v in top_title_words
        ]
        self.save_json('title_word_cloud.json', title_word_cloud)
        print(f"   ✓ title_word_cloud.json ({len(title_word_cloud)} words)")
        
        # 11. Discussion trees (comments + replies for top posts)
        discussion_trees = self.build_discussion_trees()
        self.save_json('discussion_trees.json', discussion_trees)
        print(f"   ✓ discussion_trees.json ({len(discussion_trees)} posts with engagement trees)")
        
        # 12. Word cloud data (topic frequency for visualization)
        import math
        filtered_topics = [(t, c) for t, c in top_topics if t != 'general']
        word_cloud = [
            {
                'text': t,
                'value': c,
                'size': max(12, min(72, math.log(c + 1) * 8))  # Font size based on frequency
            }
            for t, c in filtered_topics[:50]  # Top 50 topics excluding the general bucket
        ]
        self.save_json('word_cloud_data.json', word_cloud)
        print(f"   ✓ word_cloud_data.json ({len(word_cloud)} topics)")
        
        # 13. Engagement distribution (for histogram)
        engagement_values = sorted([a['engagement'] for a in self.agents.values()], reverse=True)
        if engagement_values:
            max_eng = engagement_values[0]
            bins = 10
            bin_size = max(1, max_eng // bins)
            
            engagement_dist = defaultdict(int)
            for eng in engagement_values:
                bin_idx = min(bins - 1, eng // bin_size) if bin_size > 0 else 0
                engagement_dist[bin_idx] += 1
            
            engagement_histogram = [
                {
                    'range': f"{i * bin_size}-{(i + 1) * bin_size}",
                    'count': engagement_dist[i],
                    'agents': engagement_dist[i]
                }
                for i in range(bins)
            ]
        else:
            engagement_histogram = []
        
        self.save_json('engagement_distribution.json', engagement_histogram)
        print(f"   ✓ engagement_distribution.json (distribution across {len(self.agents)} agents)")

        # Final cleanup pass for front-end stability
        self.clean_outputs()
        
        return True
    
    def git_commit_and_push(self):
        """Commit changes and push to GitHub."""
        print("\n🔄 Committing to GitHub...")
        try:
            os.chdir(self.output_dir)
            
            # Add all JSON files
            subprocess.run(
                ['git', 'add', '*.json'],
                capture_output=True,
                timeout=10,
                check=False
            )
            
            # Commit with timestamp
            commit_msg = f"🤖 Auto-update: {datetime.now(timezone.utc).isoformat()}"
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"   ✓ Committed: {commit_msg}")
            else:
                print(f"   ℹ️  Nothing to commit (data unchanged)")
            
            # Push to GitHub
            result = subprocess.run(
                ['git', 'push', 'origin', 'main'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"   ✓ Pushed to GitHub")
            else:
                print(f"   ⚠️  Push failed: {result.stderr[:100]}")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ Git error: {e}")
            return False
    
    def run(self):
        """Run the complete pipeline."""
        try:
            clean_only = os.getenv("CLEAN_ONLY", "0").lower() in {"1", "true", "yes"}
            if clean_only:
                print("   ℹ️  CLEAN_ONLY set: skipping crawl/export; running cleaners on existing outputs")
                self.clean_outputs()
                print("   ✓ Cleaning complete")
                return True

            # Allow a full refresh override (ignore incremental cutoff and caps)
            if os.getenv("FULL_RUN", "0").lower() in {"1", "true", "yes"}:
                self.last_crawl_dt = None
                self.max_posts = None
                print("   ℹ️  FULL_RUN enabled: ignoring last crawl cutoff and post cap")
            # Crawl
            if not self.crawl():
                return False
            
            # Export
            if not self.export_all():
                return False
            
            # Push to GitHub (unless explicitly skipped)
            skip_git = os.getenv("SKIP_GIT", "0").lower() in {"1", "true", "yes"}
            if skip_git:
                print("   ℹ️  SKIP_GIT set; skipping git commit/push")
            else:
                if not self.git_commit_and_push():
                    print("   ⚠️  Warning: Git push failed, but JSON files were generated")
            
            print("\n" + "="*60)
            print("✅ PIPELINE COMPLETE - Data is live on GitHub Pages!")
            print("="*60 + "\n")
            return True
            
        except Exception as e:
            print(f"\n❌ PIPELINE FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    pipeline = FastMoltbookPipeline()
    success = pipeline.run()  # Fetch 5000 posts by default (very fast)
    sys.exit(0 if success else 1)
