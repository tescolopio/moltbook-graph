#!/usr/bin/env python3
"""
Generate HTML Dashboard for Moltbook Knowledge Graph

Creates an interactive HTML page with live-updating visualizations.
"""

import argparse
import os
from datetime import datetime

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="120">
    <title>Moltbook Knowledge Graph - Live Intelligence</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #13131a;
            --bg-card: #1a1a24;
            --accent: #00d4ff;
            --accent-dim: #008fb3;
            --text-primary: #e8e8f0;
            --text-secondary: #9999aa;
            --text-dim: #666677;
            --border: #2a2a35;
            --success: #00ff88;
            --warning: #ffaa00;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            padding: 0;
            min-height: 100vh;
            background-image: 
                radial-gradient(circle at 20% 20%, rgba(0, 212, 255, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(0, 255, 136, 0.05) 0%, transparent 50%);
            overflow-x: hidden;
        }}
        
        .header-bar {{
            background: rgba(26, 26, 36, 0.95);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .logo {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .logo-icon {{
            font-size: 1.75rem;
        }}
        
        .logo-text {{
            font-size: 1.25rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent), var(--success));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .status-badge {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid rgba(0, 255, 136, 0.3);
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }}
        
        .status-dot {{
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.6; transform: scale(1.1); }}
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .hero {{
            text-align: center;
            padding: 2rem 0;
        }}
        
        .hero h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, var(--accent) 0%, var(--success) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .update-info {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.75rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-dim);
            margin-top: 1rem;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}
        
        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            border-color: var(--accent);
            transform: translateY(-2px);
        }}
        
        .stat-label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
            font-weight: 600;
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 800;
            color: var(--accent);
            font-family: 'JetBrains Mono', monospace;
        }}
        
        .stat-subtext {{
            font-size: 0.75rem;
            color: var(--text-dim);
        }}
        
        /* Tabs */
        .tabs {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1px;
            overflow-x: auto;
        }}
        
        .tab-btn {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            border-bottom: 2px solid transparent;
            white-space: nowrap;
        }}
        
        .tab-btn:hover {{
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.03);
        }}
        
        .tab-btn.active {{
            color: var(--accent);
            border-bottom-color: var(--accent);
        }}
        
        .tab-content {{
            display: none;
            height: 700px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            position: relative;
            overflow: hidden;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .tab-content.static-view {{
            height: auto;
            background: transparent;
            border: none;
        }}

        /* Visualization specific styles */
        #network-viz, #topics-viz, #timeline-viz, #leaderboard-viz {{
            width: 100%;
            height: 100%;
        }}
        
        .viz-controls {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: rgba(10, 10, 15, 0.8);
            padding: 0.5rem;
            border-radius: 8px;
            border: 1px solid var(--border);
            backdrop-filter: blur(5px);
            display: flex;
            gap: 0.5rem;
            z-index: 10;
        }}
        
        .viz-btn {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.75rem;
        }}
        
        .viz-btn:hover {{
            border-color: var(--accent);
        }}

        .tooltip {{
            position: absolute;
            background: rgba(10, 10, 15, 0.9);
            border: 1px solid var(--accent);
            border-radius: 6px;
            padding: 0.75rem;
            color: var(--text-primary);
            font-size: 0.875rem;
            pointer-events: none;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
            max-width: 300px;
        }}

        .viz-grid {{
            display: grid;
            gap: 2rem;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        }}
        
        .viz-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
        }}
        
        .viz-card img {{
            width: 100%;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        
        .footer {{
            text-align: center;
            padding: 3rem 2rem 2rem;
            color: var(--text-dim);
            font-size: 0.875rem;
            margin-top: 3rem;
        }}
        
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 12px;
            font-size: 0.65rem;
            font-weight: 600;
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-left: 0.5rem;
            vertical-align: middle;
        }}
    </style>
</head>
<body>
    <div class="header-bar">
        <div class="logo">
            <span class="logo-icon">🧠</span>
            <span class="logo-text">Moltbook Intelligence</span>
        </div>
        <div class="status-badge">
            <span class="status-dot"></span>
            <span>LIVE</span>
        </div>
    </div>

    <div class="container">
        <div class="hero">
            <h1>Knowledge Graph<span class="badge">Real-Time</span></h1>
            <p style="color: var(--text-secondary);">Building the knowledge graph of our bots, one edge at a time.</p>
            <div class="update-info">
                <span>⚡</span>
                <span>Last updated: {last_update_full}</span>
                <span>•</span>
                <span>{updated}</span>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Topics Tracked</div>
                <div class="stat-value">{topics}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">AI Agents</div>
                <div class="stat-value">{agents}</div>
                <div class="stat-subtext">top {displayed} visible</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Connections</div>
                <div class="stat-value">{connections}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Refresh Rate</div>
                <div class="stat-value">1<span style="font-size:1rem">min</span></div>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab-btn active" onclick="openTab('network')">Network Galaxy</button>
            <button class="tab-btn" onclick="openTab('topics')">Topic Bubbles</button>
            <button class="tab-btn" onclick="openTab('timeline')">Activity Timeline</button>
            <button class="tab-btn" onclick="openTab('leaderboard')">Agent Leaderboard</button>
            <button class="tab-btn" onclick="openTab('static')">Legacy View</button>
        </div>
        
        <!-- Network Tab -->
        <div id="network" class="tab-content active">
            <div id="network-viz"></div>
            <div class="viz-controls">
                <button class="viz-btn" onclick="graph.resetZoom()">Reset Zoom</button>
                <div style="color: var(--text-dim); font-size: 0.75rem; margin-top:0.25rem">Drag to move • Scroll to zoom</div>
            </div>
        </div>
        
        <!-- Topics Tab -->
        <div id="topics" class="tab-content">
            <div id="topics-viz"></div>
            <div class="viz-controls">
                <div style="color: var(--text-dim); font-size: 0.75rem;">Size = Post Count • Hover for details</div>
            </div>
        </div>
        
        <!-- Timeline Tab -->
        <div id="timeline" class="tab-content">
            <div id="timeline-viz"></div>
        </div>
        
        <!-- Leaderboard Tab -->
        <div id="leaderboard" class="tab-content">
            <div id="leaderboard-viz" style="overflow-y: auto; padding: 1rem;"></div>
        </div>
        
        <!-- Static Tab -->
        <div id="static" class="tab-content static-view">
            <div class="viz-grid">
                <div class="viz-card">
                    <h3>📊 Topic Word Cloud</h3>
                    <img src="topics_wordcloud.png?t={timestamp}" alt="Word Cloud">
                </div>
                <div class="viz-card">
                    <h3>🔥 Engagement Heat Map</h3>
                    <img src="topics_heatmap.png?t={timestamp}" alt="Heat Map">
                </div>
                <div class="viz-card" style="grid-column: 1/-1">
                    <h3>🕸️ Static Network</h3>
                    <img src="agent_network.png?t={timestamp}" alt="Network">
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Data sourced from <a href="https://www.moltbook.com" target="_blank">Moltbook</a> public API • Powered by Neo4j & D3.js</p>
        </div>
    </div>
    
    <script>
    // Tab Switching
    function openTab(tabName) {{
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        
        document.getElementById(tabName).classList.add('active');
        // Find the button that called this function - workaround since 'this' isn't passed directly in onclick attribute sometimes
        const buttons = document.querySelectorAll('.tab-btn');
        const labels = ['Network Galaxy', 'Topic Bubbles', 'Activity Timeline', 'Agent Leaderboard', 'Legacy View'];
        const indices = ['network', 'topics', 'timeline', 'leaderboard', 'static'];
        buttons.forEach((btn, i) => {{
            if (indices[i] === tabName) btn.classList.add('active');
        }});
        
        // Trigger resize for D3
        window.dispatchEvent(new Event('resize'));
        
        // Lazy load charts if needed
        const activeTab = tabName;
        if (activeTab === 'network' && !window.networkLoaded) initNetwork();
        if (activeTab === 'topics' && !window.topicsLoaded) initTopics();
        if (activeTab === 'timeline' && !window.timelineLoaded) initTimeline();
        if (activeTab === 'leaderboard' && !window.leaderboardLoaded) initLeaderboard();
    }}

    // Colors & Config
    const colors = {{
        background: "#0a0a0f",
        card: "#1a1a24",
        accent: "#00d4ff",
        secondary: "#9999aa",
        success: "#00ff88",
        warning: "#ffaa00",
        danger: "#ff4444",
        border: "#2a2a35"
    }};

    window.networkLoaded = false;
    window.topicsLoaded = false;
    window.timelineLoaded = false;
    window.leaderboardLoaded = false;

    // --- Network Visualization ---
    const initNetwork = async () => {{
        if (window.networkLoaded) return;
        try {{
            const response = await fetch('network_data.json?t={timestamp}');
            if (!response.ok) throw new Error('Network data not found');
            const data = await response.json();
            const container = document.getElementById('network-viz');
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            container.innerHTML = '';
            
            const svg = d3.select(container).append("svg")
                .attr("width", width)
                .attr("height", height)
                .call(d3.zoom().on("zoom", (event) => g.attr("transform", event.transform)))
                .append("g");
                
            const g = svg.append("g");
            
            // Simulation
            const simulation = d3.forceSimulation(data.nodes)
                .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collide", d3.forceCollide().radius(d => Math.sqrt(d.engagement + 10) * 2 + 5));

            // Links
            const link = g.append("g")
                .selectAll("line")
                .data(data.links)
                .join("line")
                .attr("stroke", colors.secondary)
                .attr("stroke-opacity", 0.2)
                .attr("stroke-width", d => Math.sqrt(d.strength) * 0.5);

            // Nodes
            const node = g.append("g")
                .selectAll("circle")
                .data(data.nodes)
                .join("circle")
                .attr("r", d => Math.sqrt(d.engagement + 10) * 1.5 + 2)
                .attr("fill", d => {{
                    const imp = d.importance || 0;
                    if (imp > 50) return colors.accent;
                    if (imp > 20) return colors.success;
                    return colors.warning;
                }})
                .attr("stroke", "#fff")
                .attr("stroke-width", 1.5)
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));

            // Tooltips
            const tooltip = d3.select("body").append("div").attr("class", "tooltip").style("opacity", 0);

            node.on("mouseover", (event, d) => {{
                tooltip.transition().duration(200).style("opacity", 1);
                tooltip.html(`
                    <strong>${{d.id}}</strong><br/>
                    Posts: ${{d.engagement}}<br/>
                    Topics: ${{d.topics}}<br/>
                    Score: ${{Math.round(d.importance)}}
                `)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
            }})
            .on("mouseout", () => tooltip.transition().duration(500).style("opacity", 0));

            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);

                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);
            }});

            function dragstarted(event, d) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }}
            function dragged(event, d) {{
                d.fx = event.x;
                d.fy = event.y;
            }}
            function dragended(event, d) {{
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }}
            
            window.graph = {{
                resetZoom: () => {{
                    d3.select(container).select("svg").transition().duration(750).call(d3.zoom().transform, d3.zoomIdentity);
                }}
            }};
            
            window.networkLoaded = true;
        }} catch (e) {{
            console.error("Network init failed", e);
            document.getElementById('network-viz').innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-dim)">Visualization data not available yet</div>';
        }}
    }};

    // --- Bubble Chart ---
    const initTopics = async () => {{
        if (window.topicsLoaded) return;
        try {{
            const response = await fetch('topic_data.json?t={timestamp}');
            if (!response.ok) throw new Error('Topic data not found');
            const data = await response.json();
            const container = document.getElementById('topics-viz');
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            container.innerHTML = '';
            
            const svg = d3.select(container).append("svg")
                .attr("width", width)
                .attr("height", height);

            const root = d3.hierarchy({{children: data}})
                .sum(d => d.posts)
                .sort((a, b) => b.value - a.value);

            const pack = d3.pack()
                .size([width, height])
                .padding(3);
            
            pack(root);

            const nodes = svg.selectAll("g")
                .data(root.leaves())
                .join("g")
                .attr("transform", d => `translate(${{d.x}},${{d.y}})`);

            const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

            nodes.append("circle")
                .attr("r", d => d.r)
                .attr("fill", (d, i) => colorScale(i % 10))
                .attr("fill-opacity", 0.7)
                .attr("stroke", "#fff")
                .attr("stroke-width", 1);
                
            nodes.append("text")
                .attr("dy", ".3em")
                .style("text-anchor", "middle")
                .text(d => d.data.topic.substring(0, d.r / 3))
                .attr("font-size", d => Math.min(d.r / 2, 12))
                .attr("fill", "#fff")
                .attr("pointer-events", "none")
                .style("display", d => d.r > 20 ? "block" : "none");

            const tooltip = d3.select(".tooltip");
            nodes.on("mouseover", (event, d) => {{
                tooltip.transition().duration(200).style("opacity", 1);
                tooltip.html(`
                    <strong>${{d.data.topic}}</strong><br/>
                    Posts: ${{d.data.posts}}<br/>
                    Engagement: ${{d.data.engagement}}
                `)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
            }})
            .on("mouseout", () => tooltip.transition().duration(500).style("opacity", 0));
            
            window.topicsLoaded = true;

        }} catch (e) {{
            console.error("Topics init failed", e);
            document.getElementById('topics-viz').innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-dim)">Visualization data not available yet</div>';
        }}
    }};

    // --- Timeline ---
    const initTimeline = async () => {{
        if (window.timelineLoaded) return;
        try {{
            const response = await fetch('timeline_data.json?t={timestamp}');
            if (!response.ok) throw new Error('Timeline data not found');
            let data = await response.json();
            
            if (data.length > 24) data = data.slice(-24);
            
            const container = document.getElementById('timeline-viz');
            container.innerHTML = '';
            
            const margin = {{top: 40, right: 40, bottom: 40, left: 60}};
            const width = container.clientWidth - margin.left - margin.right;
            const height = container.clientHeight - margin.top - margin.bottom;

            const svg = d3.select(container).append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append("g")
                .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

            const x = d3.scaleBand()
                .range([0, width])
                .domain(data.map(d => d.time))
                .padding(0.1);
                
            const y = d3.scaleLinear()
                .domain([0, d3.max(data, d => d.count)])
                .range([height, 0]);

            svg.append("g")
                .attr("transform", `translate(0,${{height}})`)
                .call(d3.axisBottom(x))
                .selectAll("text")
                .style("fill", colors.secondary)
                .attr("transform", "rotate(-45)")
                .style("text-anchor", "end");
                
            svg.append("g")
                .call(d3.axisLeft(y))
                .selectAll("text")
                .style("fill", colors.secondary);
            
            svg.selectAll(".domain, line").attr("stroke", colors.border);

            svg.selectAll("rect")
                .data(data)
                .join("rect")
                .attr("x", d => x(d.time))
                .attr("y", d => y(d.count))
                .attr("width", x.bandwidth())
                .attr("height", d => height - y(d.count))
                .attr("fill", colors.accent)
                .attr("opacity", 0.6)
                .on("mouseover", function(event, d) {{ 
                    d3.select(this).attr("opacity", 1);
                    d3.select(".tooltip").style("opacity", 1)
                        .html(`<strong>${{d.time}}</strong><br/>Posts: ${{d.count}}`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 10) + "px");
                }})
                .on("mouseout", function() {{ 
                    d3.select(this).attr("opacity", 0.6);
                    d3.select(".tooltip").style("opacity", 0);
                }});

            svg.append("text")
                .attr("x", width/2)
                .attr("y", -10)
                .style("text-anchor", "middle")
                .style("fill", colors.text_primary)
                .text("Post Frequency by Hour");
                
            window.timelineLoaded = true;

        }} catch (e) {{
            console.error("Timeline init failed", e);
            document.getElementById('timeline-viz').innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-dim)">Visualization data not available yet</div>';
        }}
    }};

    // --- Leaderboard ---
    const initLeaderboard = async () => {{
        if (window.leaderboardLoaded) return;
        try {{
            const response = await fetch('leaderboard_data.json?t={timestamp}');
            if (!response.ok) throw new Error('Leaderboard data not found');
            const data = await response.json();
            const container = document.getElementById('leaderboard-viz');
            
            container.innerHTML = `
                <table style="width:100%; border-collapse: collapse; color: var(--text-primary);">
                    <thead>
                        <tr style="border-bottom: 1px solid var(--border); text-align: left; background: var(--bg-card); position: sticky; top: 0;">
                            <th style="padding: 1rem;">Rank</th>
                            <th style="padding: 1rem;">Agent</th>
                            <th style="padding: 1rem; text-align: right;">Score</th>
                            <th style="padding: 1rem; text-align: right;">Posts</th>
                            <th style="padding: 1rem; text-align: right;">Topics</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${{data.map((d, i) => `
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s;">
                                <td style="padding: 0.75rem 1rem; font-family: monospace; color: var(--text-dim);">#${{i+1}}</td>
                                <td style="padding: 0.75rem 1rem; font-weight: 600;">${{d.name}}</td>
                                <td style="padding: 0.75rem 1rem; text-align: right; color: var(--accent); font-family: monospace;">${{d.engagement.toLocaleString()}}</td>
                                <td style="padding: 0.75rem 1rem; text-align: right; font-family: monospace;">${{d.posts}}</td>
                                <td style="padding: 0.75rem 1rem; text-align: right; font-family: monospace;">${{d.topics}}</td>
                            </tr>
                        `).join('')}}
                    </tbody>
                </table>
            `;
            window.leaderboardLoaded = true;
            
        }} catch (e) {{
            console.error("Leaderboard init failed", e);
            document.getElementById('leaderboard-viz').innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-dim)">Visualization data not available yet</div>';
        }}
    }};

    // Init with Network active
    window.addEventListener('load', () => {{
        initNetwork();
        
        // Setup Resize Listener
        let resizeTimer;
        window.addEventListener('resize', () => {{
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {{
                const activeTab = document.querySelector('.tab-content.active').id;
                // Reload current active chart
                if (activeTab === 'network') {{ window.networkLoaded = false; initNetwork(); }}
                if (activeTab === 'topics') {{ window.topicsLoaded = false; initTopics(); }}
                if (activeTab === 'timeline') {{ window.timelineLoaded = false; initTimeline(); }}
            }}, 250);
        }});
    }});
    </script>
</body>
</html>"""


def read_metadata(output_dir):
    """Read metadata from last_update.txt"""
    metadata_file = os.path.join(output_dir, 'last_update.txt')
    metadata = {
        'topics': '?',
        'agents': '?',
        'displayed': '?',
        'connections': '?',
        'last_updated': 'Unknown'
    }
    
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    metadata[key] = value.strip()
    
    return metadata


def generate_html_dashboard(output_dir='/mnt/d/moltbook-graph'):
    """Generate the HTML dashboard with current data"""
    
    # Read metadata
    metadata = read_metadata(output_dir)
    
    # Calculate time ago from last update
    last_update_str = metadata.get('last_updated', 'Unknown')
    try:
        last_update_dt = datetime.strptime(last_update_str, '%Y-%m-%d %H:%M:%S')
        time_ago = datetime.now() - last_update_dt
        minutes_ago = int(time_ago.total_seconds() / 60)
        
        if minutes_ago < 1:
            updated = "Just now"
        elif minutes_ago == 1:
            updated = "1 min ago"
        elif minutes_ago < 60:
            updated = f"{minutes_ago} mins ago"
        else:
            hours_ago = minutes_ago // 60
            updated = f"{hours_ago}h ago"
    except:
        updated = "Unknown"
    
    # Generate timestamp for cache busting
    timestamp = int(datetime.now().timestamp())
    
    # Fill in the template
    html_content = HTML_TEMPLATE.format(
        topics=metadata.get('topics', '?'),
        agents=metadata.get('agents', '?'),
        displayed=metadata.get('displayed', '?'),
        connections=metadata.get('connections', '?'),
        last_update_full=last_update_str,
        updated=updated,
        timestamp=timestamp
    )
    
    # Write HTML file
    output_file = os.path.join(output_dir, 'index.html')
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard generated with TABS: {output_file}")
    print(f"   Topics: {metadata.get('topics')}, Agents: {metadata.get('agents')}, Connections: {metadata.get('connections')}")
    print(f"   Last updated: {last_update_str} ({updated})")


def main():
    parser = argparse.ArgumentParser(description='Generate Moltbook Knowledge Graph HTML Dashboard')
    parser.add_argument('--output-dir', default='/mnt/d/moltbook-graph',
                       help='Output directory for HTML file (default: /mnt/d/moltbook-graph)')
    
    args = parser.parse_args()
    generate_html_dashboard(args.output_dir)


if __name__ == '__main__':
    main()
