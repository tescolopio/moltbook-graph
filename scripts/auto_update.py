#!/usr/bin/env python3
"""
Auto-Update Moltbook Knowledge Graph

Runs crawler and generates visualizations on a configurable interval.
"""

import argparse
import time
import subprocess
import sys
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/moltbook-update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class MoltbookUpdater:
    def __init__(self, neo_uri, neo_user, neo_password, output_dir, 
                 interval_minutes=5, max_posts=100, max_display_agents=500, min_engagement=50):
        self.neo_uri = neo_uri
        self.neo_user = neo_user
        self.neo_password = neo_password
        self.output_dir = output_dir
        self.interval_seconds = interval_minutes * 60
        self.max_posts = max_posts
        self.max_display_agents = max_display_agents
        self.min_engagement = min_engagement
        self.script_dir = "/root/.openclaw/workspace/skills/knowledge-graph/scripts"
        
    def run_crawler(self):
        """Run the Moltbook crawler."""
        try:
            logger.info(f"Starting crawler (fetching up to {self.max_posts} posts)...")
            result = subprocess.run([
                "python3",
                f"{self.script_dir}/crawl_moltbook.py",
                "--neo-uri", self.neo_uri,
                "--neo-user", self.neo_user,
                "--neo-password", self.neo_password,
                "--max-posts", str(self.max_posts),
                "--max-display-agents", str(self.max_display_agents),
                "--min-engagement", str(self.min_engagement),
                "--mode", "crawl"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("Crawler completed successfully")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"Crawler failed with code {result.returncode}")
                logger.error(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Crawler timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"Crawler error: {e}")
            return False
    
    def generate_visualizations(self):
        """Generate visualizations from knowledge graph."""
        try:
            logger.info("Generating visualizations...")
            result = subprocess.run([
                "python3",
                f"{self.script_dir}/generate_visualizations.py",
                "--neo-uri", self.neo_uri,
                "--neo-user", self.neo_user,
                "--neo-password", self.neo_password,
                "--output-dir", self.output_dir,
                "--max-agents", str(self.max_display_agents),
                "--min-engagement", str(self.min_engagement)
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info("Visualizations generated successfully")
                return True
            else:
                logger.error(f"Visualization generation failed with code {result.returncode}")
                logger.error(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Visualization generation timed out")
            return False
        except Exception as e:
            logger.error(f"Visualization error: {e}")
            return False
    
    def generate_html_dashboard(self):
        """Generate HTML dashboard."""
        try:
            logger.info("Generating HTML dashboard...")
            result = subprocess.run([
                "python3",
                f"{self.script_dir}/generate_html.py",
                "--output-dir", self.output_dir
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("HTML dashboard generated successfully")
                return True
            else:
                logger.warning(f"HTML generation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.warning(f"HTML generation error (non-critical): {e}")
            return False
    
    def update_cycle(self):
        """Run one complete update cycle."""
        logger.info("="*60)
        logger.info(f"Starting update cycle at {datetime.now()}")
        logger.info("="*60)
        
        # Run crawler
        crawler_success = self.run_crawler()
        
        if not crawler_success:
            logger.error("Skipping visualization generation due to crawler failure")
            return False
        
        # Generate visualizations
        viz_success = self.generate_visualizations()
        
        # Generate HTML (non-critical)
        self.generate_html_dashboard()
        
        logger.info(f"Update cycle completed (crawler: {crawler_success}, viz: {viz_success})")
        return crawler_success and viz_success
    
    def run_continuous(self):
        """Run continuous updates."""
        logger.info("Starting continuous update loop")
        logger.info(f"Update interval: {self.interval_seconds/60} minutes")
        logger.info(f"Output directory: {self.output_dir}")
        
        cycle_count = 0
        success_count = 0
        
        while True:
            cycle_count += 1
            logger.info(f"\n[Cycle {cycle_count}] Starting...")
            
            try:
                success = self.update_cycle()
                if success:
                    success_count += 1
                
                logger.info(f"[Cycle {cycle_count}] Complete. Success rate: {success_count}/{cycle_count}")
                
            except Exception as e:
                logger.error(f"[Cycle {cycle_count}] Unexpected error: {e}")
            
            # Wait for next update
            logger.info(f"Waiting {self.interval_seconds/60} minutes until next update...")
            time.sleep(self.interval_seconds)

def main():
    parser = argparse.ArgumentParser(description="Auto-update Moltbook knowledge graph")
    parser.add_argument("--neo-uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--neo-user", default="neo4j", help="Neo4j username")
    parser.add_argument("--neo-password", required=True, help="Neo4j password")
    parser.add_argument("--output-dir", default="/mnt/d", help="Output directory for visualizations")
    parser.add_argument("--interval", type=int, default=5, help="Update interval in minutes")
    parser.add_argument("--max-posts", type=int, default=100, help="Maximum posts to crawl per update")
    parser.add_argument("--max-display-agents", type=int, default=500, help="Max agents to display in visualizations")
    parser.add_argument("--min-engagement", type=int, default=50, help="Minimum engagement score to include agent")
    parser.add_argument("--once", action="store_true", help="Run once and exit (no loop)")

    args = parser.parse_args()

    updater = MoltbookUpdater(
        args.neo_uri, args.neo_user, args.neo_password, 
        args.output_dir, args.interval, args.max_posts,
        args.max_display_agents, args.min_engagement
    )

    if args.once:
        logger.info("Running single update cycle...")
        success = updater.update_cycle()
        sys.exit(0 if success else 1)
    else:
        logger.info("Running in continuous mode...")
        updater.run_continuous()

if __name__ == "__main__":
    main()
