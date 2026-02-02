#!/usr/bin/env python3
"""
Document Import Script for Knowledge Graph

Import text documents into Neo4j as graph nodes.
Extracts basic entities and creates relationships.

Usage:
    python import_documents.py --uri bolt://localhost:7687 --user neo4j --password password --file document.txt
"""

import argparse
import uuid
from neo4j import GraphDatabase
from pathlib import Path

class DocumentImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def import_document(self, file_path):
        """Import a document as a node with basic entity extraction."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text()
        doc_id = str(uuid.uuid4())

        with self.driver.session() as session:
            # Create document node
            session.run("""
                CREATE (d:Document {
                    id: $id,
                    title: $title,
                    content: $content,
                    created: datetime()
                })
                """,
                id=doc_id,
                title=path.name,
                content=content
            )

            # Simple entity extraction (persons mentioned)
            # In a real implementation, use NLP libraries like spaCy
            persons = self.extract_persons_simple(content)

            for person in persons:
                person_id = str(uuid.uuid4())
                session.run("""
                    MERGE (p:Person {name: $name})
                    ON CREATE SET p.id = $id, p.created = datetime()
                    CREATE (d:Document {id: $doc_id})-[:MENTIONS]->(p)
                    """,
                    name=person,
                    id=person_id,
                    doc_id=doc_id
                )

        return doc_id

    def extract_persons_simple(self, text):
        """Simple person extraction - look for capitalized words after common verbs."""
        # This is a very basic implementation
        # For production, use proper NER
        words = text.split()
        persons = set()

        # Look for patterns like "John said" or "with Alice"
        for i, word in enumerate(words[:-1]):
            if word[0].isupper() and len(word) > 1:
                next_word = words[i+1]
                if next_word in ['said', 'told', 'with', 'and', 'or']:
                    persons.add(word)

        return list(persons)

def main():
    parser = argparse.ArgumentParser(description="Import document to knowledge graph")
    parser.add_argument("--uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--user", default="neo4j", help="Username")
    parser.add_argument("--password", required=True, help="Password")
    parser.add_argument("--file", required=True, help="Document file path")

    args = parser.parse_args()

    importer = DocumentImporter(args.uri, args.user, args.password)

    try:
        doc_id = importer.import_document(args.file)
        print(f"Document imported with ID: {doc_id}")
    except Exception as e:
        print(f"Import failed: {e}")
    finally:
        importer.close()

if __name__ == "__main__":
    main()