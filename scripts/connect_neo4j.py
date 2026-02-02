#!/usr/bin/env python3
"""
Neo4j Connection Script

Connect to a Neo4j database and execute basic operations.
Requires neo4j Python driver: pip install neo4j

Usage:
    python connect_neo4j.py --uri bolt://localhost:7687 --user neo4j --password password
"""

import argparse
from neo4j import GraphDatabase

class Neo4jConnector:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def test_connection(self):
        """Test database connection and return basic info."""
        with self.driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition")
            record = result.single()
            return {
                "name": record["name"],
                "versions": record["versions"],
                "edition": record["edition"]
            }

    def run_query(self, query):
        """Execute a Cypher query and return results."""
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

def main():
    parser = argparse.ArgumentParser(description="Connect to Neo4j database")
    parser.add_argument("--uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--user", default="neo4j", help="Username")
    parser.add_argument("--password", required=True, help="Password")

    args = parser.parse_args()

    connector = Neo4jConnector(args.uri, args.user, args.password)

    try:
        info = connector.test_connection()
        print(f"Connected to {info['name']} {info['versions'][0]} ({info['edition']})")

        # Example query
        query = "MATCH (n) RETURN count(n) as node_count"
        result = connector.run_query(query)
        print(f"Total nodes: {result[0]['node_count']}")

    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        connector.close()

if __name__ == "__main__":
    main()
