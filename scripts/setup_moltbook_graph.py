#!/usr/bin/env python3
"""
Moltbook Knowledge Graph Setup

Initialize Neo4j database with Moltbook content type schema and sample data.

Usage:
    python setup_moltbook_graph.py --uri bolt://localhost:7687 --user neo4j --password password
"""

import argparse
from neo4j import GraphDatabase
import re

class MoltbookGraphSetup:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def setup_schema(self):
        """Create constraints and indexes for Moltbook content types."""
        with self.driver.session() as session:
            # Constraints
            session.run("CREATE CONSTRAINT agent_id IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE")
            session.run("CREATE CONSTRAINT post_id IF NOT EXISTS FOR (p:Post) REQUIRE p.id IS UNIQUE")
            session.run("CREATE CONSTRAINT comment_id IF NOT EXISTS FOR (c:Comment) REQUIRE c.id IS UNIQUE")
            session.run("CREATE CONSTRAINT submolt_name IF NOT EXISTS FOR (s:Submolt) REQUIRE s.name IS UNIQUE")

            # Indexes
            session.run("CREATE INDEX agent_name IF NOT EXISTS FOR (a:Agent) ON (a.name)")
            session.run("CREATE INDEX post_title IF NOT EXISTS FOR (p:Post) ON (p.title)")
            session.run("CREATE INDEX submolt_name_idx IF NOT EXISTS FOR (s:Submolt) ON (s.name)")

    def extract_entities_from_text(self, text):
        """Extract AI agent names, topics, and interactions from text."""
        agents = re.findall(r'\b(Agent_\d+|Clawd|Forge|MoltBot|OpenClaw)\b', text, re.IGNORECASE)
        topics = re.findall(r'\b(AI|AGI|machine learning|neural network|knowledge graphs?|reasoning|consciousness|prompt|token)\b', text, re.IGNORECASE)
        
        interactions = []
        if 'reply' in text.lower() or 'comment' in text.lower():
            interactions.append('reply')
        if 'upvote' in text.lower() or 'downvote' in text.lower():
            interactions.append('vote')
        if 'follow' in text.lower():
            interactions.append('follow')
            
        return {
            'agents': list(set(agents)),
            'topics': list(set(topics)),
            'interactions': interactions
        }

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

    def insert_sample_data(self):
        """No sample data - ready for live crawling."""
        print("Schema ready for live Moltbook data population")

def main():
    parser = argparse.ArgumentParser(description="Setup Moltbook knowledge graph")
    parser.add_argument("--uri", default="bolt://localhost:7688", help="Neo4j URI")
    parser.add_argument("--user", default="neo4j", help="Username")
    parser.add_argument("--password", required=True, help="Password")

    args = parser.parse_args()

    setup = MoltbookGraphSetup(args.uri, args.user, args.password)

    try:
        print("Setting up schema...")
        setup.setup_schema()
        print("Inserting sample data...")
        setup.insert_sample_data()
        print("Moltbook knowledge graph initialized successfully!")
    except Exception as e:
        print(f"Setup failed: {e}")
    finally:
        setup.close()

if __name__ == "__main__":
    main()