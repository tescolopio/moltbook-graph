#!/usr/bin/env python3
"""
Generate Visualizations from Moltbook Knowledge Graph

Creates word cloud of topics and heat map of engagement.
"""

import argparse
from neo4j import GraphDatabase
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import networkx as nx
import os
from datetime import datetime

class GraphVisualizer:
    def __init__(self, neo_uri, neo_user, neo_password):
        self.driver = GraphDatabase.driver(neo_uri, auth=(neo_user, neo_password))

    def close(self):
        self.driver.close()

    def get_topic_data(self):
        """Get topic frequencies and engagement."""
        query = """
        MATCH (t:Topic)<-[:DISCUSSES]-(content)
        OPTIONAL MATCH (content)<-[:CREATED]-(a:Agent)
        OPTIONAL MATCH (content:Post)-[:BELONGS_TO]->(s:Submolt)
        RETURN t.name as topic,
               count(content) as mentions,
               sum(CASE WHEN content:Post THEN content.score ELSE content.score END) as total_engagement,
               count(DISTINCT a) as unique_agents,
               count(DISTINCT s) as submolts_discussed
        ORDER BY mentions DESC
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

    def get_agent_network(self, max_agents=500):
        """Get agent interaction network with importance weights (filtered for top agents)."""
        query = """
        // First get top agents by importance
        MATCH (a:Agent)-[:CREATED]->(content)
        WITH a, SUM(content.score) as engagement
        ORDER BY engagement DESC
        LIMIT $max_agents
        WITH COLLECT(a.name) as top_agents
        
        // Then get their interactions
        MATCH (a1:Agent)-[:CREATED]->(content)-[:DISCUSSES]->(t:Topic)<-[:DISCUSSES]-(content2)<-[:CREATED]-(a2:Agent)
        WHERE a1.name <> a2.name 
          AND a1.name IN top_agents 
          AND a2.name IN top_agents
        RETURN a1.name as agent1,
               a2.name as agent2,
               t.name as shared_topic,
               count(*) as interactions,
               sum(content.score + content2.score) as total_engagement
        ORDER BY interactions DESC
        LIMIT 1000
        """
        with self.driver.session() as session:
            result = session.run(query, max_agents=max_agents)
            return [record.data() for record in result]

    def get_total_agent_count(self):
        """Get the total number of unique agents in the database."""
        query = "MATCH (a:Agent) RETURN count(DISTINCT a) as total"
        with self.driver.session() as session:
            result = session.run(query)
            return result.single()["total"]

    def get_agent_stats(self, max_agents=500, min_engagement=50):
        """Get individual agent statistics for node sizing (filtered by importance)."""
        query = """
        MATCH (a:Agent)-[:CREATED]->(content)
        OPTIONAL MATCH (content)-[:DISCUSSES]->(t:Topic)
        WITH a,
             count(DISTINCT content) as posts,
             sum(content.score) as total_engagement,
             count(DISTINCT t) as topics_discussed
        WHERE total_engagement >= $min_engagement
        RETURN a.name as agent,
               posts,
               total_engagement,
               topics_discussed,
               (total_engagement * LOG(1 + topics_discussed)) as importance_score
        ORDER BY importance_score DESC
        LIMIT $max_agents
        """
        with self.driver.session() as session:
            result = session.run(query, max_agents=max_agents, min_engagement=min_engagement)
            return [record.data() for record in result]

    def generate_word_cloud(self, topic_data, output_file="wordcloud.png"):
        """Generate word cloud from topic frequencies."""
        if not topic_data:
            print("No topic data available")
            return

        # Create word-frequency dict
        word_freq = {item['topic']: item['mentions'] for item in topic_data}

        # Generate word cloud
        wordcloud = WordCloud(
            width=800, height=400,
            background_color='white',
            max_words=50,
            colormap='viridis'
        ).generate_from_frequencies(word_freq)

        # Save plot
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Moltbook Topics Word Cloud')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Word cloud saved to {output_file}")

    def generate_heat_map(self, topic_data, output_file="heatmap.png"):
        """Generate heat map of topic engagement."""
        if not topic_data:
            print("No topic data available")
            return

        # Create DataFrame
        df = pd.DataFrame(topic_data)

        # Pivot for heatmap (topics vs engagement metrics)
        # Use mentions as size, engagement as intensity
        plt.figure(figsize=(12, 8))

        # Scatter plot with size and color
        plt.scatter(df['unique_agents'], df['mentions'],
                   s=df['total_engagement']/10,  # Size by engagement
                   c=df['submolts_discussed'],   # Color by submolts
                   cmap='YlOrRd',
                   alpha=0.6)

        # Add labels
        for i, row in df.iterrows():
            plt.annotate(row['topic'],
                        (row['unique_agents'], row['mentions']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=8)

        plt.xlabel('Unique Agents Discussing')
        plt.ylabel('Total Mentions')
        plt.title('Moltbook Topic Engagement Heat Map')
        plt.colorbar(label='Submolts Discussed')

        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Heat map saved to {output_file}")

    def generate_network_graph(self, network_data, agent_stats, output_file="network.png"):
        """Generate network graph showing agent interactions with importance."""
        if not network_data or not agent_stats:
            print("No network data available")
            return

        # Build graph
        G = nx.Graph()

        # Create agent stats lookup
        agent_engagement = {a['agent']: a['total_engagement'] for a in agent_stats}

        # Add edges with weights
        edge_weights = {}
        for item in network_data:
            agent1, agent2 = item['agent1'], item['agent2']
            weight = item['interactions']
            
            if (agent1, agent2) not in edge_weights and (agent2, agent1) not in edge_weights:
                edge_weights[(agent1, agent2)] = weight
                G.add_edge(agent1, agent2, weight=weight)
            else:
                # Increment existing edge
                if (agent1, agent2) in edge_weights:
                    edge_weights[(agent1, agent2)] += weight
                    G[agent1][agent2]['weight'] += weight
                else:
                    edge_weights[(agent2, agent1)] += weight
                    G[agent2][agent1]['weight'] += weight

        if len(G.nodes()) == 0:
            print("No nodes in network")
            return

        # Layout
        plt.figure(figsize=(16, 12))
        pos = nx.spring_layout(G, k=0.5, iterations=50)

        # Node sizes based on engagement (with minimum size)
        node_sizes = [max(100, agent_engagement.get(node, 0) / 100) for node in G.nodes()]

        # Edge widths based on interaction count
        edges = G.edges()
        weights = [G[u][v]['weight'] for u, v in edges]
        max_weight = max(weights) if weights else 1
        edge_widths = [1 + (w / max_weight) * 3 for w in weights]

        # Draw network
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, 
                              node_color='lightblue', alpha=0.7)
        nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.3, edge_color='gray')
        nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')

        plt.title('Moltbook Agent Interaction Network\n(Node size = engagement, Edge width = shared topics)', 
                 fontsize=14)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Network graph saved to {output_file}")

    def print_topic_summary(self, topic_data):
        """Print topic summary statistics."""
        if not topic_data:
            print("No topic data found")
            return

        print("=== Moltbook Topic Analysis ===")
        print(f"Total topics found: {len(topic_data)}")
        print()

        for topic in topic_data[:10]:  # Top 10
            print(f"Topic: {topic['topic']}")
            print(f"  Mentions: {topic['mentions']}")
            print(f"  Total Engagement: {topic['total_engagement']}")
            print(f"  Unique Agents: {topic['unique_agents']}")
            print(f"  Submolts: {topic['submolts_discussed']}")
            print()

def main():
    parser = argparse.ArgumentParser(description="Generate visualizations from Moltbook graph")
    parser.add_argument("--neo-uri", default="bolt://localhost:7688", help="Neo4j URI")
    parser.add_argument("--neo-user", default="neo4j", help="Neo4j username")
    parser.add_argument("--neo-password", required=True, help="Neo4j password")
    parser.add_argument("--output-dir", default="./visualizations", help="Output directory")
    parser.add_argument("--max-agents", type=int, default=200, help="Max agents to visualize")
    parser.add_argument("--min-engagement", type=int, default=0, help="Min engagement to include")

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    visualizer = GraphVisualizer(args.neo_uri, args.neo_user, args.neo_password)

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Fetching data from knowledge graph (max {args.max_agents} agents)...")
        
        total_agents = visualizer.get_total_agent_count()
        topic_data = visualizer.get_topic_data()
        agent_stats = visualizer.get_agent_stats(max_agents=args.max_agents, min_engagement=args.min_engagement)
        network_data = visualizer.get_agent_network(max_agents=args.max_agents)
        
        print(f"Total agents in database: {total_agents}")
        print(f"Retrieved {len(agent_stats)} agents for visualization (filtered by importance)")

        visualizer.print_topic_summary(topic_data)

        print("Generating word cloud...")
        visualizer.generate_word_cloud(topic_data,
                                     os.path.join(args.output_dir, "topics_wordcloud.png"))

        print("Generating heat map...")
        visualizer.generate_heat_map(topic_data,
                                   os.path.join(args.output_dir, "topics_heatmap.png"))

        print("Generating network graph...")
        visualizer.generate_network_graph(network_data, agent_stats,
                                        os.path.join(args.output_dir, "agent_network.png"))

        # Save metadata
        with open(os.path.join(args.output_dir, "last_update.txt"), "w") as f:
            f.write(f"Last updated: {timestamp}\n")
            f.write(f"Topics: {len(topic_data)}\n")
            f.write(f"Agents: {total_agents}\n")
            f.write(f"Displayed: {len(agent_stats)}\n")
            f.write(f"Connections: {len(network_data)}\n")

        print(f"\n[{timestamp}] Visualizations saved to {args.output_dir}/")

    except Exception as e:
        print(f"Visualization failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        visualizer.close()

if __name__ == "__main__":
    main()