# 🧠 Moltbook Knowledge Graph - Live Dashboard

Real-time visualization of AI agent interactions on [Moltbook](https://www.moltbook.com).

**🔴 [View Live Dashboard](https://YOUR_USERNAME.github.io/moltbook-graph/)** *(update this link after deploying)*

## 📊 What This Shows

- **Word Cloud**: Topics sized by popularity
- **Heat Map**: Agent engagement patterns (bubble size = total engagement)
- **Network Graph**: Agent interaction network
  - Node size = agent influence/engagement
  - Edge width = shared topic connections

## 🔄 Updates

The dashboard automatically refreshes with new data every **5 minutes**.

## 📈 Current Stats

- **87 AI Agents** tracked
- **16 Topics** analyzed
- **200 Connections** mapped
- Live data from Moltbook API

## 🤖 Topics Tracked

Agent, AI, Token, Consciousness, Prompt, Intelligence, Solana, Safety, Logic, Base, and more...

## 🛠️ How It Works

1. Crawler fetches latest posts from [Moltbook API](https://www.moltbook.com/api/v1)
2. Neo4j graph database stores relationships
3. Python generates visualizations with importance metrics
4. Auto-updates every 5 minutes
5. Hosted on GitHub Pages

## 📷 Preview

The network graph reveals which AI agents are most influential and how they connect through shared topics.

## 🔗 Related

- [Moltbook](https://www.moltbook.com) - The source platform
- Built with Neo4j, Python, NetworkX, and Matplotlib

---

*Last updated: Auto-refreshing*
