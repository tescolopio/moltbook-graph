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
import subprocess
from datetime import datetime
from collections import defaultdict
import sys

class FastMoltbookPipeline:
    def __init__(self, output_dir="/mnt/d/moltbook-graph"):
        self.base_url = "https://www.moltbook.com"
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.timeout = 15
        
        # Data containers - ONLY store important data
        self.posts = []
        self.agents = {}
        self.topics = defaultdict(int)
        self.agent_engagement = defaultdict(int)
        self.agent_topics = defaultdict(set)
        self.connections = {}
        
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
    
    def crawl(self, max_posts=5000):
        """Fetch and aggregate data from Moltbook API."""
        print("\n🚀 FAST MOLTBOOK PIPELINE")
        print("="*60)
        
        # Fetch posts with pagination
        print("📥 Fetching posts...")
        all_posts = []
        offset = 0
        max_fetches = (max_posts // 100) + 1  # Limit API calls
        fetches = 0
        
        while len(all_posts) < max_posts and fetches < max_fetches:
            data = self.fetch("/posts", {"offset": offset, "limit": 100})
            if not data or not data.get('success'):
                break
            
            posts = data.get('posts', [])
            if not posts:
                break
                
            all_posts.extend(posts)
            offset += 100
            fetches += 1
            
            if len(all_posts) % 500 == 0:
                print(f"   Fetched {len(all_posts)} posts...")
        
        print(f"✅ Got {len(all_posts)} posts from API")
        if len(all_posts) == 0:
            # Avoid wiping data when the API is down; keep previous exports intact
            print("❌ No posts fetched; skipping export to preserve existing data")
            return False
        
        # Process posts ONCE - build all data in one pass
        print("🔍 Processing data...")
        for post in all_posts:
            author = post.get('author', {}).get('name', '')
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
            
            # Store post with engagement metrics
            self.posts.append({
                'id': post.get('id'),
                'title': post.get('title', ''),
                'author': author,
                'submolt': submolt,
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
        
        print(f"✅ {len(self.agents)} agents, {len(self.topics)} topics")
        return True
    
    def save_json(self, filename, data):
        """Save JSON file."""
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w') as f:
            json.dump(data, f, default=str)
    
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
        
        # 2. Topic data (top 100)
        top_topics = sorted(self.topics.items(), key=lambda x: x[1], reverse=True)[:100]
        topics_data = [
            {'name': t, 'value': c, 'size': max(5, c // 3)}
            for t, c in top_topics
        ]
        self.save_json('topic_data.json', topics_data)
        print(f"   ✓ topic_data.json ({len(topics_data)} topics)")
        
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
            'crawled_at': datetime.utcnow().isoformat()
        }
        self.save_json('summary_stats.json', summary)
        print(f"   ✓ summary_stats.json")
        
        # 6. Agent history (track growth)
        history_file = os.path.join(self.output_dir, 'agent_history.json')
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except:
            history = {'crawls': [], 'summary': {}}
        
        crawl_entry = {
            'timestamp': datetime.utcnow().isoformat(),
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
        
        # 11. Discussion trees (comments + replies for top posts)
        discussion_trees = self.build_discussion_trees()
        self.save_json('discussion_trees.json', discussion_trees)
        print(f"   ✓ discussion_trees.json ({len(discussion_trees)} posts with engagement trees)")
        
        # 12. Word cloud data (topic frequency for visualization)
        import math
        word_cloud = [
            {
                'text': t,
                'value': c,
                'size': max(12, min(72, math.log(c + 1) * 8))  # Font size based on frequency
            }
            for t, c in top_topics[:50]  # Top 50 topics
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
            commit_msg = f"🤖 Auto-update: {datetime.utcnow().isoformat()}"
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
            # Crawl
            if not self.crawl():
                return False
            
            # Export
            if not self.export_all():
                return False
            
            # Push to GitHub
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
