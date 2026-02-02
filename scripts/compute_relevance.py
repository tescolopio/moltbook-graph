#!/usr/bin/env python3
"""
Compute Topic-Agent Relevance Scores

Calculate and store relevance scores between topics and agents based on discussion patterns.
"""

import argparse
from neo4j import GraphDatabase
from datetime import datetime

class RelevanceComputer:
    def __init__(self, neo_uri, neo_user, neo_password):
        self.driver = GraphDatabase.driver(neo_uri, auth=(neo_user, neo_password))

    def close(self):
        self.driver.close()

    def compute_relevance_scores(self):
        """Compute relevance scores for all agent-topic pairs."""
        with self.driver.session() as session:
            # Clear existing relevance nodes
            session.run("MATCH (r:Relevance) DETACH DELETE r")

            # Calculate relevance for each agent-topic pair
            query = """
            MATCH (a:Agent)-[:CREATED]->(content)-[:DISCUSSES]->(t:Topic)
            OPTIONAL MATCH (content:Post)-[:BELONGS_TO]->(s:Submolt)
            WITH a, t, 
                 count(content) as frequency,
                 sum(content.score) as total_engagement,
                 max(content.created) as last_discussion,
                 count(DISTINCT s) as diversity
            WHERE frequency > 0
            WITH a, t, frequency, total_engagement, last_discussion, diversity,
                 duration.between(last_discussion, datetime()).days as days_since_last
            // Calculate relevance score (weighted combination)
            WITH a, t, frequency, total_engagement, days_since_last, diversity,
                 (frequency * 0.4 + total_engagement * 0.001 + diversity * 0.3 + 
                  (30 - CASE WHEN days_since_last < 30 THEN days_since_last ELSE 30 END) * 0.3) as relevance_score
            CREATE (r:Relevance {
                score: relevance_score,
                frequency: frequency,
                engagement: total_engagement,
                recency: days_since_last,
                diversity: diversity,
                computed_at: datetime()
            })
            CREATE (a)-[:HAS_RELEVANCE]->(r)
            CREATE (r)-[:ABOUT_TOPIC]->(t)
            RETURN a.name, t.name, relevance_score
            ORDER BY relevance_score DESC
            """
            
            results = session.run(query)
            relevance_data = [record.data() for record in results]
            
            print(f"Computed relevance scores for {len(relevance_data)} agent-topic pairs")
            return relevance_data

    def get_relevance_summary(self):
        """Get summary of relevance scores."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Agent)-[:HAS_RELEVANCE]->(r:Relevance)-[:ABOUT_TOPIC]->(t:Topic)
                RETURN a.name as agent, 
                       t.name as topic, 
                       r.score as relevance_score,
                       r.frequency as frequency
                ORDER BY r.score DESC
                LIMIT 20
                """)
            return [record.data() for record in result]

def main():
    parser = argparse.ArgumentParser(description="Compute topic-agent relevance scores")
    parser.add_argument("--neo-uri", default="bolt://localhost:7688", help="Neo4j URI")
    parser.add_argument("--neo-user", default="neo4j", help="Neo4j username")
    parser.add_argument("--neo-password", required=True, help="Neo4j password")

    args = parser.parse_args()

    computer = RelevanceComputer(args.neo_uri, args.neo_user, args.neo_password)

    try:
        print("Computing relevance scores...")
        relevance_data = computer.compute_relevance_scores()
        
        print("\nTop Relevance Scores:")
        for item in relevance_data[:10]:
            print(f"Agent: {item['a.name']}, Topic: {item['t.name']}, Score: {item['relevance_score']:.2f}")
        
        summary = computer.get_relevance_summary()
        print(f"\nStored {len(summary)} relevance relationships")
        
    except Exception as e:
        print(f"Relevance computation failed: {e}")
    finally:
        computer.close()

if __name__ == "__main__":
    main()