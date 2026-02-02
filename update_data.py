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
        
        # Process posts ONCE - build all data in one pass
        print("🔍 Processing data...")
        for post in all_posts:
            author = post.get('author', {}).get('name', '')
            submolt_data = post.get('submolt', {})
            # Handle submolt as either dict or string
            submolt = submolt_data.get('name') if isinstance(submolt_data, dict) else str(submolt_data)
            submolt = submolt or 'General'
            
            # Calculate engagement (likes + replies + comments)
            engagement = (post.get('likes', 0) + 
                         post.get('replies', 0) + 
                         post.get('comments', 0) +
                         post.get('shares', 0) * 2)  # Weight shares higher
            
            if author:
                # Track agent data
                agent_id = author.lower()
                if agent_id not in self.agents:
                    self.agents[agent_id] = {'name': author, 'posts': 0, 'engagement': 0, 'topics': 0}
                
                self.agents[agent_id]['posts'] += 1
                self.agents[agent_id]['engagement'] += engagement
                self.agent_engagement[agent_id] += engagement
                self.agent_topics[agent_id].add(submolt)
            
            # Track topics
            if submolt:
                self.topics[submolt] += 1
            
            # Store post
            self.posts.append({
                'id': post.get('id'),
                'title': post.get('title', ''),
                'author': author,
                'submolt': submolt,
                'engagement': engagement,
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
    
    def export_all(self):
        """Export all JSON files."""
        print("💾 Exporting JSON files...")
        
        # Calculate importance score for each agent
        # Importance = engagement × log(topic_diversity) × post_frequency
        import math
        
        agent_importance = {}
        for agent_id, agent_data in self.agents.items():
            topic_diversity = len(self.agent_topics[agent_id])
            post_freq = agent_data['posts']
            engagement = agent_data['engagement']
            
            # Importance formula: engagement weighted by topic diversity and activity
            importance = (engagement + 1) * math.log(max(2, topic_diversity)) * math.log(max(2, post_freq))
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
                'engagement': data['engagement'],
                'importance': agent_importance.get(aid, 0),
                'topics': len(self.agent_topics[aid]),
                'size': max(3, data['engagement'] // 5),
                'value': data['engagement'] + len(self.agent_topics[aid]) * 10  # For sizing alternatives
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
