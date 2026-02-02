#!/usr/bin/env python3
"""
Graph Query Script

Execute Cypher queries against Neo4j knowledge graph.

Usage:
    python query_graph.py --uri bolt://localhost:7687 --user neo4j --password password --query "MATCH (n) RETURN count(n)"
"""

import argparse
import json
from neo4j import GraphDatabase

class GraphQuerier:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def execute_query(self, query):
        """Execute Cypher query and return results as JSON."""
        with self.driver.session() as session:
            result = session.run(query)
            records = [record.data() for record in result]
            return records

def main():
    parser = argparse.ArgumentParser(description="Query Neo4j knowledge graph")
    parser.add_argument("--uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--user", default="neo4j", help="Username")
    parser.add_argument("--password", required=True, help="Password")
    parser.add_argument("--query", required=True, help="Cypher query")
    parser.add_argument("--output", choices=['json', 'table'], default='json', help="Output format")

    args = parser.parse_args()

    querier = GraphQuerier(args.uri, args.user, args.password)

    try:
        results = querier.execute_query(args.query)

        if args.output == 'json':
            print(json.dumps(results, indent=2, default=str))
        else:
            if results:
                # Simple table output
                headers = list(results[0].keys())
                print("\t".join(headers))
                for record in results:
                    row = [str(record.get(h, '')) for h in headers]
                    print("\t".join(row))
            else:
                print("No results")

    except Exception as e:
        print(f"Query failed: {e}")
    finally:
        querier.close()

if __name__ == "__main__":
    main()