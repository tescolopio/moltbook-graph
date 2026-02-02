#!/usr/bin/env python3
"""
Generate interactive D3.js network visualization data
"""

import argparse
import json
import os
from neo4j import GraphDatabase

class InteractiveDataGenerator:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def get_network_data(self, max_agents=200):
        """Get network data formatted for D3.js force-directed graph"""
        query = """
        // Get top agents by importance
        MATCH (a:Agent)-[:CREATED]->(content)
        OPTIONAL MATCH (content)-[:DISCUSSES]->(t:Topic)
        WITH a,
             count(DISTINCT content) as posts,
             sum(content.score) as total_engagement,
             count(DISTINCT t) as topics_discussed
        WITH a, total_engagement, topics_discussed,
             (total_engagement * LOG(1 + topics_discussed)) as importance_score
        ORDER BY importance_score DESC
        LIMIT $max_agents
        WITH COLLECT(a.name) as top_agents, COLLECT({
            name: a.name,
            engagement: total_engagement,
            topics: topics_discussed,
            importance: importance_score
        }) as agent_data
        
        // Get connections between top agents
        UNWIND agent_data as agent
        MATCH (a1:Agent {name: agent.name})-[:CREATED]->(content)-[:DISCUSSES]->(t:Topic)<-[:DISCUSSES]-(content2)<-[:CREATED]-(a2:Agent)
        WHERE a1.name <> a2.name AND a2.name IN top_agents
        WITH agent_data, a1.name as source, a2.name as target, 
             COUNT(DISTINCT t) as shared_topics,
             SUM(content.score + content2.score) as strength
        
        RETURN agent_data, 
               COLLECT({source: source, target: target, value: shared_topics, strength: strength}) as links
        """
        
        with self.driver.session() as session:
            result = session.run(query, max_agents=max_agents)
            record = result.single()
            
            if not record:
                return {"nodes": [], "links": []}
            
            nodes = [
                {
                    "id": node["name"],
                    "engagement": int(node["engagement"]),
                    "topics": int(node["topics"]),
                    "importance": float(node["importance"])
                }
                for node in record["agent_data"]
            ]
            
            links = [
                {
                    "source": link["source"],
                    "target": link["target"],
                    "value": int(link["value"]),
                    "strength": int(link["strength"])
                }
                for link in record["links"]
            ]
            
            return {"nodes": nodes, "links": links}
    
    def get_topic_data(self):
        """Get topic data with engagement metrics"""
        query = """
        MATCH (t:Topic)<-[:DISCUSSES]-(content)
        OPTIONAL MATCH (content)-[:BELONGS_TO]->(s:Submolt)
        WITH t.name as topic,
             COUNT(DISTINCT content) as posts,
             SUM(content.score) as engagement,
             COUNT(DISTINCT s) as submolts
        RETURN topic, posts, engagement, submolts
        ORDER BY engagement DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [
                {
                    "topic": record["topic"],
                    "posts": int(record["posts"]),
                    "engagement": int(record["engagement"]),
                    "submolts": int(record["submolts"])
                }
                for record in result
            ]

def main():
    parser = argparse.ArgumentParser(description='Generate interactive visualization data')
    parser.add_argument('--neo-uri', default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--neo-user', default='neo4j', help='Neo4j username')
    parser.add_argument('--neo-password', required=True, help='Neo4j password')
    parser.add_argument('--output-dir', default='.', help='Output directory')
    parser.add_argument('--max-agents', type=int, default=200, help='Max agents for network')
    
    args = parser.parse_args()
    
    generator = InteractiveDataGenerator(args.neo_uri, args.neo_user, args.neo_password)
    
    try:
        print("Generating interactive network data...")
        network_data = generator.get_network_data(args.max_agents)
        
        print("Generating topic data...")
        topic_data = generator.get_topic_data()
        
        # Save network data
        network_file = os.path.join(args.output_dir, 'network_data.json')
        with open(network_file, 'w') as f:
            json.dump(network_data, f, indent=2)
        print(f"✅ Network data: {network_file} ({len(network_data['nodes'])} nodes, {len(network_data['links'])} links)")
        
        # Save topic data
        topic_file = os.path.join(args.output_dir, 'topic_data.json')
        with open(topic_file, 'w') as f:
            json.dump(topic_data, f, indent=2)
        print(f"✅ Topic data: {topic_file} ({len(topic_data)} topics)")
        
    finally:
        generator.close()

if __name__ == '__main__':
    main()
