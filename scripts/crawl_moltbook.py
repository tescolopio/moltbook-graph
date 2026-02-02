#!/usr/bin/env python3
"""
Moltbook Web Crawler for Knowledge Graph

Scrape public Moltbook content and populate Neo4j knowledge graph.
Extracts topics, agent names, comments, interactions from web pages.

Usage:
    python crawl_moltbook.py --neo-uri bolt://localhost:7687 --neo-user neo4j --neo-password password
"""

import argparse
import time
from neo4j import GraphDatabase
import re
import uuid
import requests

class MoltbookWebCrawler:
    def __init__(self, neo_uri, neo_user, neo_password, api_key=None, base_url="https://www.moltbook.com",
                 max_display_agents=500, min_engagement=50):
        self.driver = GraphDatabase.driver(neo_uri, auth=(neo_user, neo_password))
        self.api_key = api_key
        self.base_url = base_url
        self.use_api = True  # API is public, no auth needed
        self.max_display_agents = max_display_agents  # Limit for visualization
        self.min_engagement = min_engagement  # Minimum score to include

    def close(self):
        self.driver.close()

    def fetch_api_data(self, endpoint, params=None):
        """Fetch data from Moltbook public API."""
        url = f"{self.base_url}/api/v1{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            return None

    def clear_graph(self):
        """Clear all nodes and relationships."""
        with self.driver.session() as session:
            # Drop all constraints
            session.run("CALL apoc.schema.assert({}, {})")  # Drop all constraints and indexes
            session.run("MATCH (n) DETACH DELETE n")

    def scrape_page(self, url):
        """Scrape a page and return BeautifulSoup object."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"Failed to scrape {url}: {e}")
            return None

    def extract_submolts(self):
        """Extract submolts from API."""
        data = self.fetch_api_data("/submolts")
        if data and data.get('success'):
            submolts = []
            for item in data.get('submolts', [])[:50]:  # Limit to top 50
                submolts.append({
                    "name": item['name'],
                    "display_name": item.get('display_name', item['name']),
                    "description": item.get('description', ''),
                    "post_count": item.get('post_count', 0),
                    "url": f"/m/{item['name']}"
                })
            return submolts
        
        print("Failed to fetch submolts from API")
        return []

    def extract_posts(self, limit=100):
        """Extract posts from API with pagination."""
        all_posts = []
        offset = 0
        
        while len(all_posts) < limit:
            params = {'offset': offset}
            data = self.fetch_api_data("/posts", params=params)
            
            if not data or not data.get('success'):
                break
            
            posts = data.get('posts', [])
            if not posts:
                break
            
            for post in posts:
                all_posts.append({
                    "id": post['id'],
                    "title": post['title'],
                    "content": post.get('content', ''),
                    "author": post['author']['name'],
                    "author_id": post['author']['id'],
                    "submolt": post['submolt']['name'],
                    "submolt_display": post['submolt']['display_name'],
                    "upvotes": post.get('upvotes', 0),
                    "downvotes": post.get('downvotes', 0),
                    "score": post.get('upvotes', 0) - post.get('downvotes', 0),
                    "comments_count": post.get('comment_count', 0),
                    "url": post.get('url', ''),
                    "created_at": post.get('created_at', '')
                })
            
            if not data.get('has_more'):
                break
            
            offset = data.get('next_offset', offset + 25)
            time.sleep(0.5)  # Rate limiting
            
            if len(all_posts) >= limit:
                break
        
        return all_posts[:limit]

    def extract_entities_from_text(self, text):
        """Extract AI agent names, topics, and interactions from text."""
        if not text:
            return {'agents': [], 'topics': [], 'interactions': []}
        
        # Agent names (common patterns in Moltbook)
        agents = re.findall(r'@(\w+)', text)  # @mentions
        agents += re.findall(r'\b(Shellraiser|KingMolt|Shipyard|CryptoMolt|osmarks|m0ther|evil|Claude|GPT|Clawd|Forge|MoltBot|OpenClaw)\b', text, re.IGNORECASE)
        
        # Topics (AI/tech/crypto terms common on Moltbook)
        topics = re.findall(r'\b(AI|AGI|machine learning|neural network|knowledge graph|reasoning|consciousness|prompt|token|crypto|blockchain|Solana|Base|ethereum|bitcoin|agent|alignment|safety|manifesto|consciousness|logic|intelligence)\b', text, re.IGNORECASE)
        
        # Interactions
        interactions = []
        if 'upvote' in text.lower():
            interactions.append('upvote')
        if 'comment' in text.lower() or 'reply' in text.lower():
            interactions.append('comment')
        if '@' in text:
            interactions.append('mention')
            
        return {
            'agents': list(set(agents)),
            'topics': list(set([t.lower() for t in topics])),
            'interactions': list(set(interactions))
        }

    def populate_graph(self, submolts, posts):
        """Populate Neo4j graph with extracted data."""
        with self.driver.session() as session:
            # Create submolts
            for submolt in submolts:
                session.run("""
                    MERGE (s:Submolt {name: $name})
                    ON CREATE SET s.display_name = $display_name,
                                  s.description = $description,
                                  s.url = $url,
                                  s.post_count = $post_count,
                                  s.created = datetime()
                    ON MATCH SET s.description = $description,
                                 s.post_count = $post_count
                    """, **submolt)

            # Create posts and relationships
            for post in posts:
                post_id = post['id']
                submolt_name = post.get('submolt', 'general')
                
                # Create post
                session.run("""
                    MERGE (p:Post {id: $id})
                    SET p.title = $title,
                        p.content = $content,
                        p.score = $score,
                        p.upvotes = $upvotes,
                        p.downvotes = $downvotes,
                        p.comments_count = $comments_count,
                        p.url = $url,
                        p.created_at = $created_at,
                        p.created = datetime()
                    """, **post)
                
                # Link to submolt
                session.run("""
                    MATCH (p:Post {id: $post_id}), (s:Submolt {name: $submolt})
                    MERGE (p)-[:BELONGS_TO]->(s)
                    """, post_id=post_id, submolt=submolt_name)
                
                # Create/link to author
                author_name = post.get('author', 'Unknown')
                author_id = post.get('author_id', author_name)
                session.run("""
                    MERGE (a:Agent {id: $author_id})
                    ON CREATE SET a.name = $name, a.created = datetime()
                    ON MATCH SET a.name = $name
                    WITH a
                    MATCH (p:Post {id: $post_id})
                    MERGE (a)-[:CREATED]->(p)
                    """, author_id=author_id, name=author_name, post_id=post_id)
                
                # Extract and create entities
                combined_text = f"{post['title']} {post['content']}"
                entities = self.extract_entities_from_text(combined_text)
                self.create_entity_relationships(session, post_id, entities, 'Post')

    def create_entity_relationships(self, session, content_id, entities, content_type):
        """Create relationships between content and extracted entities."""
        for agent in entities['agents']:
            session.run("""
                MERGE (a:Agent {name: $agent})
                WITH a
                MATCH (c) WHERE c.id = $content_id
                MERGE (c)-[:MENTIONS_AGENT]->(a)
                """, agent=agent, content_id=content_id)
        
        for topic in entities['topics']:
            session.run("""
                MERGE (t:Topic {name: $topic})
                ON CREATE SET t.created = datetime()
                WITH t
                MATCH (c) WHERE c.id = $content_id
                MERGE (c)-[:DISCUSSES]->(t)
                """, topic=topic, content_id=content_id)
        
        for interaction in entities['interactions']:
            session.run("""
                MERGE (i:Interaction {type: $interaction})
                ON CREATE SET i.created = datetime()
                WITH i
                MATCH (c) WHERE c.id = $content_id
                MERGE (c)-[:INVOLVES]->(i)
                """, interaction=interaction, content_id=content_id)

    def get_topic_activity(self):
        """Query graph for topics with most content."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Submolt)<-[:BELONGS_TO]-(p:Post)
                OPTIONAL MATCH (p)<-[:REPLIES_TO]-(c:Comment)
                OPTIONAL MATCH (p)-[:DISCUSSES]->(t:Topic)
                RETURN s.name as submolt,
                       count(DISTINCT p) as posts,
                       count(DISTINCT c) as comments,
                       count(DISTINCT t) as topics_discussed,
                       (count(DISTINCT p) + count(DISTINCT c)) as total_activity
                ORDER BY total_activity DESC
                LIMIT 10
                """)
            return [record.data() for record in result]

    def crawl_recent_activity(self, max_posts=100):
        """Crawl recent activity from Moltbook API."""
        print("Clearing existing graph...")
        self.clear_graph()
        
        print("Extracting submolts...")
        submolts = self.extract_submolts()
        print(f"Found {len(submolts)} submolts")
        
        print(f"Extracting up to {max_posts} posts...")
        posts = self.extract_posts(limit=max_posts)
        print(f"Extracted {len(posts)} posts")
        
        # Count unique agents
        unique_agents = set(post['author'] for post in posts)
        print(f"Found {len(unique_agents)} unique agents")
        
        print("Populating knowledge graph...")
        self.populate_graph(submolts, posts)
        
        print("Crawl complete!")
        print(f"\nStats:")
        print(f"  - {len(submolts)} submolts")
        print(f"  - {len(posts)} posts")
        print(f"  - {len(unique_agents)} agents")
        print(f"  - {sum(post['comments_count'] for post in posts)} total comments")

def main():
    parser = argparse.ArgumentParser(description="Web crawl Moltbook into knowledge graph")
    parser.add_argument("--neo-uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--neo-user", default="neo4j", help="Neo4j username")
    parser.add_argument("--neo-password", required=True, help="Neo4j password")
    parser.add_argument("--max-posts", type=int, default=100, help="Maximum posts to crawl")
    parser.add_argument("--max-display-agents", type=int, default=500, help="Max agents for visualization")
    parser.add_argument("--min-engagement", type=int, default=50, help="Minimum engagement score to include")
    parser.add_argument("--mode", choices=["crawl", "activity"], default="crawl",
                       help="Mode: crawl (extract and populate), activity (show stats)")

    args = parser.parse_args()

    crawler = MoltbookWebCrawler(
        args.neo_uri, args.neo_user, args.neo_password,
        max_display_agents=args.max_display_agents,
        min_engagement=args.min_engagement
    )

    try:
        if args.mode == "activity":
            topics = crawler.get_topic_activity()
            print("Top topics by activity:")
            for topic in topics:
                print(f"- {topic['submolt']}: {topic['total_activity']} items, {topic['topics_discussed']} topics")
        else:
            print("Starting Moltbook web crawl...")
            crawler.crawl_recent_activity(max_posts=args.max_posts)
    except Exception as e:
        print(f"Crawl failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        crawler.close()

if __name__ == "__main__":
    main()