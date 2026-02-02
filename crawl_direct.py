#!/usr/bin/env python3
"""
Direct Moltbook Crawler - No Database Required

Crawls Moltbook API and exports directly to JSON files for visualization.
Skips Neo4j entirely - perfect for lightweight deployments.
"""

import requests
import json
import os
from datetime import datetime
from collections import defaultdict
import sys

class DirectMoltbookCrawler:
    def __init__(self, output_dir="/mnt/d/moltbook-graph", base_url="https://www.moltbook.com"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'MoltbookGraphCrawler/1.0'})
        
        # Data containers
        self.agents = {}  # agent_id -> agent_data
        self.topics = defaultdict(int)  # topic_name -> post_count
        self.posts = []  # list of posts
        self.connections = defaultdict(lambda: {"shared_topics": set(), "interaction_count": 0})
        
    def fetch_api(self, endpoint, params=None):
        """Fetch data from Moltbook API with retry logic."""
        url = f"{self.base_url}/api/v1{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API Error - {endpoint}: {e}")
            return None
    
    def crawl_posts(self, max_posts=50000):
        """Fetch posts from API with pagination."""
        print(f"📥 Fetching up to {max_posts} posts from Moltbook API...")
        
        all_posts = []
        offset = 0
        page_size = 100
        
        while len(all_posts) < max_posts:
            params = {'offset': offset, 'limit': page_size}
            data = self.fetch_api("/posts", params=params)
            
            if not data or not data.get('success'):
                print(f"   Reached end of posts after {offset} records")
                break
            
            posts = data.get('posts', [])
            if not posts:
                print(f"   No more posts available")
                break
            
            all_posts.extend(posts)
            offset += page_size
            
            if len(all_posts) % 500 == 0:
                print(f"   Fetched {len(all_posts)} posts...")
        
        print(f"✅ Fetched {len(all_posts)} total posts")
        return all_posts[:max_posts]
    
    def process_posts(self, posts):
        """Extract agents, topics, and connections from posts."""
        print(f"🔍 Processing posts to extract agents and topics...")
        
        topic_engagement = defaultdict(int)
        agent_engagement = defaultdict(int)
        agent_topics = defaultdict(set)
        
        for post in posts:
            # Extract author (agent)
            author_name = post.get('author', {}).get('name', 'Unknown')
            if author_name and author_name != 'Unknown':
                agent_id = author_name.lower()
                
                if agent_id not in self.agents:
                    self.agents[agent_id] = {
                        'id': agent_id,
                        'name': author_name,
                        'posts': 0,
                        'engagement': 0
                    }
                
                # Count posts and engagement
                self.agents[agent_id]['posts'] += 1
                engagement = post.get('likes', 0) + post.get('replies', 0) + post.get('shares', 0)
                self.agents[agent_id]['engagement'] += engagement
                agent_engagement[agent_id] += engagement
            
            # Extract topics (submolt)
            submolt = post.get('submolt', 'General')
            if submolt:
                self.topics[submolt] += 1
                topic_engagement[submolt] += engagement if author_name else 0
                agent_topics[agent_id].add(submolt)
            
            # Store post
            self.posts.append({
                'id': post.get('id'),
                'title': post.get('title', ''),
                'author': author_name,
                'submolt': submolt,
                'engagement': engagement,
                'created': post.get('created_at', '')
            })
        
        # Build agent connections
        print(f"🔗 Building agent connections...")
        for agent1_id in self.agents:
            topics1 = agent_topics.get(agent1_id, set())
            for agent2_id in self.agents:
                if agent1_id < agent2_id:  # Avoid duplicates
                    topics2 = agent_topics.get(agent2_id, set())
                    shared = topics1 & topics2
                    if shared:
                        key = f"{agent1_id}-{agent2_id}"
                        self.connections[key] = {
                            'agent1': agent1_id,
                            'agent2': agent2_id,
                            'shared_topics': list(shared),
                            'shared_count': len(shared)
                        }
        
        print(f"✅ Found {len(self.agents)} agents, {len(self.topics)} topics")
        print(f"✅ Built {len(self.connections)} connections")
    
    def export_network_data(self):
        """Export network graph data for D3.js visualization."""
        print("💾 Exporting network_data.json...")
        
        # Sort agents by engagement, take top 200
        top_agents = sorted(self.agents.items(), 
                          key=lambda x: x[1]['engagement'], 
                          reverse=True)[:200]
        top_agent_ids = {a[0] for a in top_agents}
        
        # Build nodes
        nodes = [
            {
                'id': agent_id,
                'name': agent_data['name'],
                'posts': agent_data['posts'],
                'engagement': agent_data['engagement'],
                'size': max(1, agent_data['engagement'] // 10)  # Scale for visualization
            }
            for agent_id, agent_data in top_agents
        ]
        
        # Build links (connections between top agents)
        links = [
            {
                'source': conn['agent1'],
                'target': conn['agent2'],
                'weight': conn['shared_count'],
                'shared_topics': conn['shared_topics']
            }
            for conn in self.connections.values()
            if conn['agent1'] in top_agent_ids and conn['agent2'] in top_agent_ids
        ]
        
        # Limit links to top 1500 by weight
        links = sorted(links, key=lambda x: x['weight'], reverse=True)[:1500]
        
        data = {'nodes': nodes, 'links': links}
        output_file = os.path.join(self.output_dir, 'network_data.json')
        with open(output_file, 'w') as f:
            json.dump(data, f)
        
        print(f"   ✅ {len(nodes)} nodes, {len(links)} links")
    
    def export_topic_data(self):
        """Export topic bubble chart data."""
        print("💾 Exporting topic_data.json...")
        
        # Sort topics by frequency, take top 100
        top_topics = sorted(self.topics.items(), 
                          key=lambda x: x[1], 
                          reverse=True)[:100]
        
        data = [
            {'name': topic, 'value': count, 'size': max(10, count // 5)}
            for topic, count in top_topics
        ]
        
        output_file = os.path.join(self.output_dir, 'topic_data.json')
        with open(output_file, 'w') as f:
            json.dump(data, f)
        
        print(f"   ✅ {len(data)} topics exported")
    
    def export_leaderboard_data(self):
        """Export leaderboard of top agents."""
        print("💾 Exporting leaderboard_data.json...")
        
        # Sort by engagement, take top 50
        top_agents = sorted(self.agents.items(),
                          key=lambda x: x[1]['engagement'],
                          reverse=True)[:50]
        
        data = [
            {
                'rank': i + 1,
                'name': agent_data['name'],
                'engagement': agent_data['engagement'],
                'posts': agent_data['posts']
            }
            for i, (_, agent_data) in enumerate(top_agents)
        ]
        
        output_file = os.path.join(self.output_dir, 'leaderboard_data.json')
        with open(output_file, 'w') as f:
            json.dump(data, f)
        
        print(f"   ✅ {len(data)} agents in leaderboard")
    
    def export_summary_stats(self):
        """Export summary statistics."""
        print("💾 Exporting summary_stats.json...")
        
        total_engagement = sum(a['engagement'] for a in self.agents.values())
        
        data = {
            'total_agents': len(self.agents),
            'total_topics': len(self.topics),
            'total_posts': len(self.posts),
            'total_connections': len(self.connections),
            'total_engagement': total_engagement,
            'avg_engagement': total_engagement // max(1, len(self.agents))
        }
        
        output_file = os.path.join(self.output_dir, 'summary_stats.json')
        with open(output_file, 'w') as f:
            json.dump(data, f)
        
        print(f"   ✅ Summary: {data['total_agents']} agents, {data['total_posts']} posts")
    
    def export_agent_history(self):
        """Update agent history with current crawl."""
        print("💾 Updating agent_history.json...")
        
        history_file = os.path.join(self.output_dir, 'agent_history.json')
        
        # Load existing history
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = {'crawls': [], 'summary': {}}
        else:
            history = {'crawls': [], 'summary': {}}
        
        # Add new crawl
        crawl_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_agents': len(self.agents),
            'total_posts': len(self.posts),
            'total_topics': len(self.topics),
            'total_relationships': len(self.connections)
        }
        
        history['crawls'].append(crawl_data)
        
        # Keep only last 100 crawls
        history['crawls'] = history['crawls'][-100:]
        
        # Update summary
        history['summary'] = {
            'first_crawl': history['crawls'][0]['timestamp'],
            'last_crawl': crawl_data['timestamp'],
            'total_crawls': len(history['crawls']),
            'max_agents': max(c['total_agents'] for c in history['crawls']),
            'min_agents': min(c['total_agents'] for c in history['crawls'])
        }
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"   ✅ History updated: {len(history['crawls'])} crawls recorded")
    
    def export_connections_data(self):
        """Export top agent connections."""
        print("💾 Exporting connections_data.json...")
        
        # Sort connections by shared topic count, take top 20
        top_connections = sorted(self.connections.values(),
                                key=lambda x: x['shared_count'],
                                reverse=True)[:20]
        
        data = [
            {
                'agent1': conn['agent1'],
                'agent2': conn['agent2'],
                'shared_topics': conn['shared_topics'],
                'shared_count': conn['shared_count']
            }
            for conn in top_connections
        ]
        
        output_file = os.path.join(self.output_dir, 'connections_data.json')
        with open(output_file, 'w') as f:
            json.dump(data, f)
        
        print(f"   ✅ {len(data)} top connections exported")
    
    def export_heatmap_data(self):
        """Export activity heatmap data (24h x 7d)."""
        print("💾 Exporting heatmap_data.json...")
        
        # Initialize 24x7 heatmap (hours x days)
        heatmap = [[0 for _ in range(24)] for _ in range(7)]
        
        # Process posts by timestamp
        for post in self.posts:
            created = post.get('created', '')
            if created:
                try:
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    day = dt.weekday()  # 0=Monday, 6=Sunday
                    hour = dt.hour
                    if 0 <= day < 7 and 0 <= hour < 24:
                        heatmap[day][hour] += 1
                except:
                    pass
        
        # Flatten to array of objects
        data = [
            {'day': day, 'hour': hour, 'count': heatmap[day][hour]}
            for day in range(7)
            for hour in range(24)
        ]
        
        output_file = os.path.join(self.output_dir, 'heatmap_data.json')
        with open(output_file, 'w') as f:
            json.dump(data, f)
        
        print(f"   ✅ Heatmap generated (168 cells)")
    
    def export_timeline_data(self):
        """Export timeline of agent growth."""
        print("💾 Exporting timeline_data.json...")
        
        # Group posts by date
        dates = defaultdict(int)
        for post in self.posts:
            created = post.get('created', '')
            if created:
                try:
                    date = created.split('T')[0]  # YYYY-MM-DD
                    dates[date] += 1
                except:
                    pass
        
        # Sort by date and create cumulative timeline
        sorted_dates = sorted(dates.items())
        cumulative = 0
        data = []
        
        for date, count in sorted_dates:
            cumulative += count
            data.append({'date': date, 'agents': cumulative})
        
        output_file = os.path.join(self.output_dir, 'timeline_data.json')
        with open(output_file, 'w') as f:
            json.dump(data, f)
        
        print(f"   ✅ Timeline with {len(data)} dates exported")
    
    def export_agent_history_viz(self):
        """Export agent history for growth trend visualization."""
        print("💾 Exporting agent_history_viz.json...")
        
        history_file = os.path.join(self.output_dir, 'agent_history.json')
        
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            data = [
                {
                    'timestamp': crawl['timestamp'],
                    'agents': crawl['total_agents']
                }
                for crawl in history.get('crawls', [])
            ]
            
            output_file = os.path.join(self.output_dir, 'agent_history_viz.json')
            with open(output_file, 'w') as f:
                json.dump(data, f)
            
            print(f"   ✅ Growth trend with {len(data)} data points exported")
        except Exception as e:
            print(f"   ⚠️  Could not generate growth trend: {e}")
    
    def run(self, max_posts=50000):
        """Run the complete crawl and export pipeline."""
        print("\n" + "="*60)
        print("🚀 MOLTBOOK DIRECT CRAWLER (No Database Required)")
        print("="*60 + "\n")
        
        try:
            # Step 1: Crawl posts
            posts = self.crawl_posts(max_posts)
            if not posts:
                print("❌ No posts fetched - aborting")
                return False
            
            # Step 2: Process data
            self.process_posts(posts)
            
            # Step 3: Export all JSON files
            self.export_network_data()
            self.export_topic_data()
            self.export_leaderboard_data()
            self.export_summary_stats()
            self.export_agent_history()
            self.export_connections_data()
            self.export_heatmap_data()
            self.export_timeline_data()
            self.export_agent_history_viz()
            
            print("\n" + "="*60)
            print("✅ Crawl Complete - All JSON files exported!")
            print("="*60 + "\n")
            return True
            
        except Exception as e:
            print(f"\n❌ Crawl failed: {e}\n")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crawl Moltbook and export JSON")
    parser.add_argument('--output-dir', default='/mnt/d/moltbook-graph',
                       help='Output directory for JSON files')
    parser.add_argument('--max-posts', type=int, default=50000,
                       help='Maximum posts to crawl')
    
    args = parser.parse_args()
    
    crawler = DirectMoltbookCrawler(output_dir=args.output_dir)
    success = crawler.run(max_posts=args.max_posts)
    
    sys.exit(0 if success else 1)
