#!/usr/bin/env python3
"""
HTML Report Generator for Claude Code Usage Data Insights

Generates an HTML report with:
- Statistical charts and metrics
- LLM-generated narrative sections
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from insights_generator import (
    DataAnalyzer,
    LLMClient,
    NarrativeGenerator,
    USAGE_DATA_DIR,
)


class HTMLReportGenerator:
    """Generates HTML report from usage data analysis."""

    def __init__(self, analyzer: DataAnalyzer, llm_client: Optional[LLMClient] = None):
        self.analyzer = analyzer
        self.llm_client = llm_client
        self.narrative_gen = (
            NarrativeGenerator(analyzer, llm_client) if llm_client else None
        )
        self.narratives: Dict[str, Any] = {}

    def generate_narratives(self):
        """Generate all narrative sections using LLM."""
        if not self.narrative_gen:
            print("No LLM client available, skipping narrative generation.")
            return

        print("Generating project areas analysis...")
        self.narratives["project_areas"] = self.narrative_gen.generate_project_areas()

        print("Generating interaction style analysis...")
        self.narratives["interaction_style"] = (
            self.narrative_gen.generate_interaction_style()
        )

        print("Generating 'what works' analysis...")
        self.narratives["what_works"] = self.narrative_gen.generate_what_works()

        print("Generating friction analysis...")
        self.narratives["friction"] = self.narrative_gen.generate_friction_analysis()

        print("Generating 'at a glance' summary...")
        self.narratives["at_a_glance"] = self.narrative_gen.generate_at_a_glance()

        print("Generating 'features to try' suggestions...")
        self.narratives["features_to_try"] = (
            self.narrative_gen.generate_features_to_try()
        )

        print("Generating 'usage patterns' suggestions...")
        self.narratives["usage_patterns"] = self.narrative_gen.generate_usage_patterns()

        print("Generating 'on the horizon' suggestions...")
        self.narratives["horizon"] = self.narrative_gen.generate_horizon()

        print("Generating fun ending...")
        self.narratives["fun_ending"] = self.narrative_gen.generate_fun_ending()

    def get_stats(self) -> Dict:
        """Get all statistics for the report."""
        start_date, end_date = self.analyzer.get_date_range()
        lines_added, lines_removed = self.analyzer.get_lines_stats()
        total_messages = self.analyzer.get_total_messages()

        # Calculate days span
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            days_span = max(1, (end - start).days)
        except:
            days_span = 1

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_sessions": len(self.analyzer.sessions),
            "analyzed_sessions": len(self.analyzer.facets),
            "total_messages": total_messages,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "files_modified": self.analyzer.get_files_modified(),
            "git_commits": self.analyzer.get_git_commits(),
            "days_span": days_span,
            "msgs_per_day": round(total_messages / days_span, 1),
            "tool_counts": self.analyzer.get_tool_counts(),
            "language_counts": self.analyzer.get_language_counts(),
            "goal_categories": self.analyzer.get_goal_categories(),
            "outcome_counts": self.analyzer.get_outcome_counts(),
            "satisfaction_counts": self.analyzer.get_satisfaction_counts(),
            "friction_counts": self.analyzer.get_friction_counts(),
            "primary_success_counts": self.analyzer.get_primary_success_counts(),
            "session_type_counts": self.analyzer.get_session_type_counts(),
            "helpfulness_counts": self.analyzer.get_claude_helpfulness_counts(),
            "response_time_stats": self.analyzer.get_response_time_stats(),
            "hourly_distribution": self.analyzer.get_hourly_distribution(),
            "project_areas": self.analyzer.get_project_areas(),
            "multiclauding_stats": self.analyzer.get_multiclauding_stats(),
            "tool_error_counts": self.analyzer.get_tool_error_counts(),
        }

    def format_bar_chart_html(self, data: Dict[str, int], color: str) -> str:
        """Generate HTML for a bar chart."""
        if not data:
            return '<div class="empty">No data available</div>'

        sorted_items = sorted(data.items(), key=lambda x: -x[1])
        max_value = sorted_items[0][1] if sorted_items else 1

        html_parts = []
        for label, value in sorted_items:
            percentage = (value / max_value * 100) if max_value > 0 else 0
            html_parts.append(
                f"""<div class="bar-row">
        <div class="bar-label">{label}</div>
        <div class="bar-track"><div class="bar-fill" style="width:{percentage}%;background:{color}"></div></div>
        <div class="bar-value">{value}</div>
      </div>"""
            )
        return "\n".join(html_parts)

    def format_hourly_histogram_html(
        self, distribution: Dict[str, int], offset: int = 0
    ) -> str:
        """Generate HTML for hourly histogram."""
        hourly = defaultdict(int)
        for hour, count in distribution.items():
            hour_int = int(hour) if isinstance(hour, str) else hour
            adjusted_hour = (hour_int + offset) % 24
            hourly[adjusted_hour] += count

        if not hourly:
            return '<div class="empty">No data available</div>'

        # Group into periods
        periods = [
            (6, 12, "Morning (6-12)"),
            (12, 18, "Afternoon (12-18)"),
            (18, 24, "Evening (18-24)"),
            (0, 6, "Night (0-6)"),
        ]

        period_counts = {}
        for start, end, label in periods:
            count = sum(hourly.get(h, 0) for h in range(start, end))
            period_counts[label] = count

        max_count = max(period_counts.values()) if period_counts else 1

        html_parts = []
        for label, count in period_counts.items():
            percentage = (count / max_count * 100) if max_count > 0 else 0
            html_parts.append(
                f"""      <div class="bar-row">
        <div class="bar-label">{label}</div>
        <div class="bar-track"><div class="bar-fill" style="width:{percentage}%;background:#8b5cf6"></div></div>
        <div class="bar-value">{count}</div>
      </div>"""
            )
        return "\n".join(html_parts)

    def generate_html(self, output_path: str = "insights.html") -> str:
        """Generate the complete HTML report."""
        stats = self.get_stats()

        # Build HTML
        html = self._build_html(stats)

        # Write to file
        with open(output_path, "w") as f:
            f.write(html)

        print(f"Report written to {output_path}")
        return html

    def _build_html(self, stats: Dict) -> str:
        """Build the HTML content."""

        # Calculate totals for display
        total_sessions = stats["total_sessions"]
        analyzed_sessions = stats["analyzed_sessions"]
        total_messages = stats["total_messages"]

        # Extract narrative data
        at_a_glance = self.narratives.get("at_a_glance", {})

        # Build subtitle
        if analyzed_sessions < total_sessions:
            subtitle = f"{total_messages:,} messages across {analyzed_sessions} sessions ({total_sessions} total) | {stats['start_date']} to {stats['end_date']}"
        else:
            subtitle = f"{total_messages:,} messages across {total_sessions} sessions | {stats['start_date']} to {stats['end_date']}"

        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Claude Code Insights</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; color: #334155; line-height: 1.65; padding: 48px 24px; }}
    .container {{ max-width: 800px; margin: 0 auto; }}
    h1 {{ font-size: 32px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }}
    h2 {{ font-size: 20px; font-weight: 600; color: #0f172a; margin-top: 48px; margin-bottom: 16px; }}
    .subtitle {{ color: #64748b; font-size: 15px; margin-bottom: 32px; }}
    .nav-toc {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 24px 0 32px 0; padding: 16px; background: white; border-radius: 8px; border: 1px solid #e2e8f0; }}
    .nav-toc a {{ font-size: 12px; color: #64748b; text-decoration: none; padding: 6px 12px; border-radius: 6px; background: #f1f5f9; transition: all 0.15s; }}
    .nav-toc a:hover {{ background: #e2e8f0; color: #334155; }}
    .stats-row {{ display: flex; gap: 24px; margin-bottom: 40px; padding: 20px 0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; flex-wrap: wrap; }}
    .stat {{ text-align: center; }}
    .stat-value {{ font-size: 24px; font-weight: 700; color: #0f172a; }}
    .stat-label {{ font-size: 11px; color: #64748b; text-transform: uppercase; }}
    .at-a-glance {{ background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 1px solid #f59e0b; border-radius: 12px; padding: 20px 24px; margin-bottom: 32px; }}
    .glance-title {{ font-size: 16px; font-weight: 700; color: #92400e; margin-bottom: 16px; }}
    .glance-sections {{ display: flex; flex-direction: column; gap: 12px; }}
    .glance-section {{ font-size: 14px; color: #78350f; line-height: 1.6; }}
    .glance-section strong {{ color: #92400e; }}
    .see-more {{ color: #b45309; text-decoration: none; font-size: 13px; white-space: nowrap; }}
    .see-more:hover {{ text-decoration: underline; }}
    .project-areas {{ display: flex; flex-direction: column; gap: 12px; margin-bottom: 32px; }}
    .project-area {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }}
    .area-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
    .area-name {{ font-weight: 600; font-size: 15px; color: #0f172a; }}
    .area-count {{ font-size: 12px; color: #64748b; background: #f1f5f9; padding: 2px 8px; border-radius: 4px; }}
    .area-desc {{ font-size: 14px; color: #475569; line-height: 1.5; }}
    .narrative {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 24px; }}
    .narrative p {{ margin-bottom: 12px; font-size: 14px; color: #475569; line-height: 1.7; }}
    .key-insight {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px 16px; margin-top: 12px; font-size: 14px; color: #166534; }}
    .section-intro {{ font-size: 14px; color: #64748b; margin-bottom: 16px; }}
    .big-wins {{ display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }}
    .big-win {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px; }}
    .big-win-title {{ font-weight: 600; font-size: 15px; color: #166534; margin-bottom: 8px; }}
    .big-win-desc {{ font-size: 14px; color: #15803d; line-height: 1.5; }}
    .friction-categories {{ display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; }}
    .friction-category {{ background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; padding: 16px; }}
    .friction-title {{ font-weight: 600; font-size: 15px; color: #991b1b; margin-bottom: 6px; }}
    .friction-desc {{ font-size: 13px; color: #7f1d1d; margin-bottom: 10px; }}
    .friction-examples {{ margin: 0 0 0 20px; font-size: 13px; color: #334155; }}
    .friction-examples li {{ margin-bottom: 4px; }}
    .charts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin: 24px 0; }}
    .chart-card {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }}
    .chart-title {{ font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 12px; }}
    .bar-row {{ display: flex; align-items: center; margin-bottom: 6px; }}
    .bar-label {{ width: 100px; font-size: 11px; color: #475569; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .bar-track {{ flex: 1; height: 6px; background: #f1f5f9; border-radius: 3px; margin: 0 8px; }}
    .bar-fill {{ height: 100%; border-radius: 3px; }}
    .bar-value {{ width: 28px; font-size: 11px; font-weight: 500; color: #64748b; text-align: right; }}
    .empty {{ color: #94a3b8; font-size: 13px; }}
    .claude-md-section {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 16px; margin-bottom: 20px; }}
    .claude-md-section h3 {{ font-size: 14px; font-weight: 600; color: #1e40af; margin: 0 0 12px 0; }}
    .claude-md-actions {{ margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #dbeafe; }}
    .copy-all-btn {{ background: #2563eb; color: white; border: none; border-radius: 4px; padding: 6px 12px; font-size: 12px; cursor: pointer; font-weight: 500; transition: all 0.2s; }}
    .copy-all-btn:hover {{ background: #1d4ed8; }}
    .copy-all-btn.copied {{ background: #16a34a; }}
    .claude-md-item {{ display: flex; flex-wrap: wrap; align-items: flex-start; gap: 8px; padding: 10px 0; border-bottom: 1px solid #dbeafe; }}
    .claude-md-item:last-child {{ border-bottom: none; }}
    .cmd-checkbox {{ margin-top: 2px; }}
    .cmd-code {{ background: white; padding: 8px 12px; border-radius: 4px; font-size: 12px; color: #1e40af; border: 1px solid #bfdbfe; font-family: monospace; display: block; white-space: pre-wrap; word-break: break-word; flex: 1; }}
    .cmd-why {{ font-size: 12px; color: #64748b; width: 100%; padding-left: 24px; margin-top: 4px; }}
    .features-section, .patterns-section {{ display: flex; flex-direction: column; gap: 12px; margin: 16px 0; }}
    .feature-card {{ background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 16px; }}
    .pattern-card {{ background: #f0f9ff; border: 1px solid #7dd3fc; border-radius: 8px; padding: 16px; }}
    .feature-title, .pattern-title {{ font-weight: 600; font-size: 15px; color: #0f172a; margin-bottom: 6px; }}
    .feature-oneliner {{ font-size: 14px; color: #475569; margin-bottom: 8px; }}
    .pattern-summary {{ font-size: 14px; color: #475569; margin-bottom: 8px; }}
    .feature-why, .pattern-detail {{ font-size: 13px; color: #334155; line-height: 1.5; }}
    .feature-examples {{ margin-top: 12px; }}
    .feature-example {{ padding: 8px 0; border-top: 1px solid #d1fae5; }}
    .feature-example:first-child {{ border-top: none; }}
    .example-desc {{ font-size: 13px; color: #334155; margin-bottom: 6px; }}
    .example-code-row {{ display: flex; align-items: flex-start; gap: 8px; }}
    .example-code {{ flex: 1; background: #f1f5f9; padding: 8px 12px; border-radius: 4px; font-family: monospace; font-size: 12px; color: #334155; overflow-x: auto; white-space: pre-wrap; }}
    .copyable-prompt-section {{ margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e8f0; }}
    .copyable-prompt-row {{ display: flex; align-items: flex-start; gap: 8px; }}
    .copyable-prompt {{ flex: 1; background: #f8fafc; padding: 10px 12px; border-radius: 4px; font-family: monospace; font-size: 12px; color: #334155; border: 1px solid #e2e8f0; white-space: pre-wrap; line-height: 1.5; }}
    .feature-code {{ background: #f8fafc; padding: 12px; border-radius: 6px; margin-top: 12px; border: 1px solid #e2e8f0; display: flex; align-items: flex-start; gap: 8px; }}
    .feature-code code {{ flex: 1; font-family: monospace; font-size: 12px; color: #334155; white-space: pre-wrap; }}
    .pattern-prompt {{ background: #f8fafc; padding: 12px; border-radius: 6px; margin-top: 12px; border: 1px solid #e2e8f0; }}
    .pattern-prompt code {{ font-family: monospace; font-size: 12px; color: #334155; display: block; white-space: pre-wrap; margin-bottom: 8px; }}
    .prompt-label {{ font-size: 11px; font-weight: 600; text-transform: uppercase; color: #64748b; margin-bottom: 6px; }}
    .copy-btn {{ background: #e2e8f0; border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px; cursor: pointer; color: #475569; flex-shrink: 0; }}
    .copy-btn:hover {{ background: #cbd5e1; }}
    .horizon-section {{ display: flex; flex-direction: column; gap: 16px; }}
    .horizon-card {{ background: linear-gradient(135deg, #faf5ff 0%, #f5f3ff 100%); border: 1px solid #c4b5fd; border-radius: 8px; padding: 16px; }}
    .horizon-title {{ font-weight: 600; font-size: 15px; color: #5b21b6; margin-bottom: 8px; }}
    .horizon-possible {{ font-size: 14px; color: #334155; margin-bottom: 10px; line-height: 1.5; }}
    .horizon-tip {{ font-size: 13px; color: #6b21a8; background: rgba(255,255,255,0.6); padding: 8px 12px; border-radius: 4px; }}
    .fun-ending {{ background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 1px solid #fbbf24; border-radius: 12px; padding: 24px; margin-top: 40px; text-align: center; }}
    .fun-headline {{ font-size: 18px; font-weight: 600; color: #78350f; margin-bottom: 8px; }}
    .fun-detail {{ font-size: 14px; color: #92400e; }}
    @media (max-width: 640px) {{ .charts-row {{ grid-template-columns: 1fr; }} .stats-row {{ justify-content: center; }} }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Claude Code Insights</h1>
    <p class="subtitle">{subtitle}</p>

    <!-- At a Glance Section -->
    <div class="at-a-glance">
      <div class="glance-title">At a Glance</div>
      <div class="glance-sections">
        <div class="glance-section"><strong>What's working:</strong> {at_a_glance.get("whats_working", "Analysis unavailable.")} <a href="#section-wins" class="see-more">Impressive Things You Did →</a></div>
        <div class="glance-section"><strong>What's hindering you:</strong> {at_a_glance.get("whats_hindering", "Analysis unavailable.")} <a href="#section-friction" class="see-more">Where Things Go Wrong →</a></div>
        <div class="glance-section"><strong>Quick wins to try:</strong> {at_a_glance.get("quick_wins", "Analysis unavailable.")} <a href="#section-features" class="see-more">Features to Try →</a></div>
        <div class="glance-section"><strong>Ambitious workflows:</strong> {at_a_glance.get("ambitious_workflows", "Analysis unavailable.")} <a href="#section-horizon" class="see-more">On the Horizon →</a></div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="nav-toc">
      <a href="#section-work">What You Work On</a>
      <a href="#section-usage">How You Use CC</a>
      <a href="#section-wins">Impressive Things</a>
      <a href="#section-friction">Where Things Go Wrong</a>
      <a href="#section-features">Features to Try</a>
      <a href="#section-patterns">New Usage Patterns</a>
      <a href="#section-horizon">On the Horizon</a>
      <a href="#section-feedback">Team Feedback</a>
    </nav>

    <!-- Stats Row -->
    <div class="stats-row">
      <div class="stat"><div class="stat-value">{total_messages:,}</div><div class="stat-label">Messages</div></div>
      <div class="stat"><div class="stat-value">+{stats["lines_added"]:,}/-{stats["lines_removed"]:,}</div><div class="stat-label">Lines</div></div>
      <div class="stat"><div class="stat-value">{stats["files_modified"]:,}</div><div class="stat-label">Files</div></div>
      <div class="stat"><div class="stat-value">{stats["days_span"]}</div><div class="stat-label">Days</div></div>
      <div class="stat"><div class="stat-value">{stats["msgs_per_day"]}</div><div class="stat-label">Msgs/Day</div></div>
    </div>

    <!-- Navigation -->
    <nav class="nav-toc">
      <a href="#section-work">What You Work On</a>
      <a href="#section-usage">How You Use CC</a>
      <a href="#section-wins">Impressive Things</a>
      <a href="#section-friction">Where Things Go Wrong</a>
      <a href="#section-feedback">Team Feedback</a>
    </nav>
"""

        # === What You Work On Section ===
        html += """
    <!-- What You Work On -->
    <h2 id="section-work">What You Work On</h2>
    <div class="project-areas">
"""

        # Add project areas
        project_areas = (
            self.narratives.get("project_areas", []) or stats["project_areas"]
        )
        for area in project_areas[:5]:
            if isinstance(area, dict):
                name = area.get("name", "Unknown")
                count = area.get("session_count", 0)
                desc = area.get("description", "")
                html += f"""      <div class="project-area">
        <div class="area-header">
          <span class="area-name">{name}</span>
          <span class="area-count">~{count} sessions</span>
        </div>
"""
                if desc:
                    html += f"""        <div class="area-desc">{desc}</div>
"""
                html += """      </div>
"""

        html += """    </div>

    <!-- Charts Row 1 -->
    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">What You Wanted</div>
"""
        html += self.format_bar_chart_html(stats["goal_categories"], "#2563eb")
        html += """
      </div>
      <div class="chart-card">
        <div class="chart-title">Top Tools Used</div>
"""
        html += self.format_bar_chart_html(stats["tool_counts"], "#0891b2")
        html += """
      </div>
    </div>

    <!-- Charts Row 2 -->
    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">Languages</div>
"""
        html += self.format_bar_chart_html(stats["language_counts"], "#10b981")
        html += """
      </div>
      <div class="chart-card">
        <div class="chart-title">Session Types</div>
"""
        html += self.format_bar_chart_html(stats["session_type_counts"], "#8b5cf6")
        html += """
      </div>
    </div>
"""

        # === How You Use CC Section ===
        html += """
    <!-- How You Use CC -->
    <h2 id="section-usage">How You Use Claude Code</h2>
"""

        # Interaction style narrative
        interaction_style = self.narratives.get("interaction_style", {})
        if interaction_style and interaction_style.get("narrative"):
            narrative_text = interaction_style.get("narrative", "")
            # Convert to paragraphs
            paragraphs = narrative_text.replace("\n\n", "</p><p>").split("\n")
            html += """
    <div class="narrative">
"""
            for p in paragraphs:
                if p.strip():
                    html += f"""      <p>{p}</p>
"""
            if interaction_style.get("key_pattern"):
                html += f"""      <div class="key-insight"><strong>Key pattern:</strong> {interaction_style["key_pattern"]}</div>
"""
            html += """    </div>
"""
        else:
            html += """
    <div class="narrative">
      <p>Interaction style analysis requires LLM processing. Run with LLM enabled for detailed insights.</p>
    </div>
"""

        # Response time chart
        rt_stats = stats.get("response_time_stats", {})
        if rt_stats.get("distribution"):
            html += """
    <div class="chart-card" style="margin: 24px 0;">
      <div class="chart-title">User Response Time Distribution</div>
"""
            max_count = max(
                (d.get("count", 0) for d in rt_stats["distribution"]), default=1
            )
            for item in rt_stats["distribution"]:
                pct = (item.get("count", 0) / max_count * 100) if max_count > 0 else 0
                html += f"""      <div class="bar-row">
        <div class="bar-label">{item.get("label", "")}</div>
        <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:#6366f1"></div></div>
        <div class="bar-value">{item.get("count", 0)}</div>
      </div>
"""
            html += f"""      <div style="font-size: 12px; color: #64748b; margin-top: 8px;">
        Median: {rt_stats.get("median", 0):.1f}s &bull; Average: {rt_stats.get("average", 0):.1f}s
      </div>
    </div>
"""

        # Hourly distribution with timezone selector
        html += """
    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title" style="display: flex; align-items: center; gap: 12px;">
          User Messages by Time of Day
          <select id="timezone-select" style="font-size: 12px; padding: 4px 8px; border-radius: 4px; border: 1px solid #e2e8f0;">
            <option value="0">PT (UTC-8)</option>
            <option value="3">ET (UTC-5)</option>
            <option value="8">London (UTC)</option>
            <option value="9">CET (UTC+1)</option>
            <option value="17">Tokyo (UTC+9)</option>
            <option value="custom">Custom offset...</option>
          </select>
          <input type="number" id="custom-offset" placeholder="UTC offset" style="display: none; width: 80px; font-size: 12px; padding: 4px; border-radius: 4px; border: 1px solid #e2e8f0;">
        </div>
        <div id="hour-histogram">
"""
        html += self.format_hourly_histogram_html(stats.get("hourly_distribution", {}))
        html += """
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-title">Tool Errors Encountered</div>
"""
        tool_errors = stats.get("tool_error_counts", {})
        if tool_errors:
            html += self.format_bar_chart_html(tool_errors, "#dc2626")
        else:
            html += """<div class="empty">Tool error data not available</div>
"""
        html += """
      </div>
    </div>
"""

        # === Impressive Things Section ===
        html += """
    <!-- Impressive Things -->
    <h2 id="section-wins">Impressive Things You Did</h2>
"""

        what_works = self.narratives.get("what_works", {})
        if what_works.get("intro"):
            html += f"""    <p class="section-intro">{what_works.get("intro", "")}</p>
"""

        html += """    <div class="big-wins">
"""

        workflows = what_works.get("impressive_workflows", [])
        for wf in workflows:
            if isinstance(wf, dict):
                title = wf.get("title", "")
                desc = wf.get("description", "")
                if title:
                    html += f"""      <div class="big-win">
        <div class="big-win-title">{title}</div>
        <div class="big-win-desc">{desc}</div>
      </div>
"""

        html += """    </div>

    <!-- Wins Charts -->
    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">What Helped Most (Claude\'s Capabilities)</div>
"""
        html += self.format_bar_chart_html(stats["primary_success_counts"], "#16a34a")
        html += """
      </div>
      <div class="chart-card">
        <div class="chart-title">Outcomes</div>
"""
        html += self.format_bar_chart_html(stats["outcome_counts"], "#8b5cf6")
        html += """
      </div>
    </div>
"""

        # === Where Things Go Wrong Section ===
        html += """
    <!-- Friction Section -->
    <h2 id="section-friction">Where Things Go Wrong</h2>
"""

        friction = self.narratives.get("friction", {})
        if friction.get("intro"):
            html += f"""    <p class="section-intro">{friction.get("intro", "")}</p>
"""

        html += """    <div class="friction-categories">
"""

        categories = friction.get("categories", [])
        for cat in categories:
            if isinstance(cat, dict):
                title = cat.get("category", "")
                desc = cat.get("description", "")
                examples = cat.get("examples", [])
                if title:
                    html += f"""      <div class="friction-category">
        <div class="friction-title">{title}</div>
        <div class="friction-desc">{desc}</div>
        <ul class="friction-examples">
"""
                    for ex in examples:
                        if isinstance(ex, dict):
                            # New detailed format
                            session = ex.get("session", "")
                            context = ex.get("context", "")
                            issue = ex.get("issue", "")
                            consequence = ex.get("consequence", "")
                            ex_text = f"Session {session}: {context} — {issue} resulting in '{consequence}'"
                        else:
                            # Old string format
                            ex_text = str(ex)
                        html += f"""          <li>{ex_text}</li>
"""
                    html += """        </ul>
      </div>
"""

        html += """    </div>

    <!-- Friction Charts -->
    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">Primary Friction Types</div>
"""
        html += self.format_bar_chart_html(stats["friction_counts"], "#dc2626")
        html += """
      </div>
      <div class="chart-card">
        <div class="chart-title">Inferred Satisfaction (model-estimated)</div>
"""
        html += self.format_bar_chart_html(stats["satisfaction_counts"], "#eab308")
        html += """
      </div>
    </div>
"""

        # === Features to Try Section ===
        features_to_try = self.narratives.get("features_to_try", {})
        claude_md_additions = features_to_try.get("claude_md_additions", [])
        features = features_to_try.get("features", [])

        if claude_md_additions or features:
            html += """
    <!-- Features to Try -->
    <h2 id="section-features">Existing CC Features to Try</h2>
"""

            # CLAUDE.md additions
            if claude_md_additions:
                html += """
    <div class="claude-md-section">
      <h3>Suggested CLAUDE.md Additions</h3>
      <p style="font-size: 12px; color: #64748b; margin-bottom: 12px;">Just copy this into Claude Code to add it to your CLAUDE.md.</p>
      <div class="claude-md-actions">
        <button class="copy-all-btn" onclick="copyAllCheckedClaudeMd()">Copy All Checked</button>
      </div>
"""
                for idx, item in enumerate(claude_md_additions):
                    code = item.get("code", "")
                    why = item.get("why", "")
                    section = item.get("section", "")
                    full_text = f"Add under {section}\n\n{code}" if section else code
                    html += f"""
        <div class="claude-md-item">
          <input type="checkbox" id="cmd-{idx}" class="cmd-checkbox" checked="" data-text="{full_text}">
          <label for="cmd-{idx}">
            <code class="cmd-code">{code}</code>
            <button class="copy-btn" onclick="copyCmdItem({idx})">Copy</button>
          </label>
          <div class="cmd-why">{why}</div>
        </div>
"""
                html += """
      </div>
    </div>
"""

            # Features section
            if features:
                html += """
    <p style="font-size: 13px; color: #64748b; margin-bottom: 12px;">Just copy this into Claude Code and it'll set it up for you.</p>
    <div class="features-section">
"""
                for feature in features:
                    name = feature.get("name", "")
                    description = feature.get("description", "")
                    why_for_you = feature.get("why_for_you", "")
                    example = feature.get("example", "")
                    html += f"""
        <div class="feature-card">
          <div class="feature-title">{name}</div>
          <div class="feature-oneliner">{description}</div>
          <div class="feature-why">{why_for_you}</div>
          <div class="feature-examples">
            <div class="feature-example">
              <div class="example-code-row">
                <code class="example-code">{example}</code>
                <button class="copy-btn" onclick="copyText(this)">Copy</button>
              </div>
            </div>
          </div>
        </div>
"""
                html += """
      </div>
"""

        # === New Usage Patterns Section ===
        usage_patterns = self.narratives.get("usage_patterns", [])
        if usage_patterns:
            html += """
    <!-- New Usage Patterns -->
    <h2 id="section-patterns">New Ways to Use Claude Code</h2>
    <p style="font-size: 13px; color: #64748b; margin-bottom: 12px;">Just copy this into Claude Code and it'll walk you through it.</p>
    <div class="patterns-section">
"""
            for pattern in usage_patterns:
                title = pattern.get("title", "")
                summary = pattern.get("summary", "")
                detail = pattern.get("detail", "")
                prompt_text = pattern.get("prompt", "")
                html += f"""
        <div class="pattern-card">
          <div class="pattern-title">{title}</div>
          <div class="pattern-summary">{summary}</div>
          <div class="pattern-detail">{detail}</div>
          <div class="copyable-prompt-section">
            <div class="prompt-label">Paste into Claude Code:</div>
            <div class="copyable-prompt-row">
              <code class="copyable-prompt">{prompt_text}</code>
              <button class="copy-btn" onclick="copyText(this)">Copy</button>
            </div>
          </div>
        </div>
"""
            html += """
      </div>
"""

        # === On the Horizon Section ===
        horizon = self.narratives.get("horizon", [])
        if horizon:
            html += """
    <!-- On the Horizon -->
    <h2 id="section-horizon">On the Horizon</h2>
    <p class="section-intro">Your usage reveals a mature AI-assisted workflow ripe for deeper autonomy.</p>
    <div class="horizon-section">
"""
            for item in horizon:
                title = item.get("title", "")
                possible = item.get("possible", "")
                getting_started = item.get("getting_started", "")
                prompt_text = item.get("prompt", "")
                html += f"""
        <div class="horizon-card">
          <div class="horizon-title">{title}</div>
          <div class="horizon-possible">{possible}</div>
          <div class="horizon-tip"><strong>Getting started:</strong> {getting_started}</div>
          <div class="pattern-prompt"><div class="prompt-label">Paste into Claude Code:</div><code>{prompt_text}</code><button class="copy-btn" onclick="copyText(this)">Copy</button></div>
        </div>
"""
            html += """
      </div>
"""

        # === Team Feedback Section ===
        html += """
    <!-- Team Feedback -->
    <h2 id="section-feedback">Team Feedback</h2>
    <div class="chart-card">
      <div class="chart-title">Claude Helpfulness Ratings</div>
"""
        html += self.format_bar_chart_html(stats["helpfulness_counts"], "#ec4899")
        html += """
    </div>
"""

        # === Fun Ending Section ===
        fun_ending = self.narratives.get("fun_ending", {})
        if fun_ending.get("headline"):
            html += f"""
    <!-- Fun Ending -->
    <div class="fun-ending">
      <div class="fun-headline">"{fun_ending.get("headline", "")}"</div>
      <div class="fun-detail">{fun_ending.get("detail", "")}</div>
    </div>
"""

        # Close HTML with JavaScript
        html += """
  </div>
  <script>
    function toggleCollapsible(header) {
      header.classList.toggle('open');
      const content = header.nextElementSibling;
      content.classList.toggle('open');
    }
    function copyText(btn) {
      const code = btn.previousElementSibling;
      navigator.clipboard.writeText(code.textContent).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
      });
    }
    function copyCmdItem(idx) {
      const checkbox = document.getElementById('cmd-' + idx);
      if (checkbox) {
        const text = checkbox.dataset.text;
        navigator.clipboard.writeText(text).then(() => {
          const btn = checkbox.nextElementSibling.querySelector('.copy-btn');
          if (btn) { btn.textContent = 'Copied!'; setTimeout(() => { btn.textContent = 'Copy'; }, 2000); }
        });
      }
    }
    function copyAllCheckedClaudeMd() {
      const checkboxes = document.querySelectorAll('.cmd-checkbox:checked');
      const texts = [];
      checkboxes.forEach(cb => {
        if (cb.dataset.text) { texts.push(cb.dataset.text); }
      });
      const combined = texts.join('\n');
      const btn = document.querySelector('.copy-all-btn');
      if (btn) {
        navigator.clipboard.writeText(combined).then(() => {
          btn.textContent = 'Copied ' + texts.length + ' items!';
          btn.classList.add('copied');
          setTimeout(() => { btn.textContent = 'Copy All Checked'; btn.classList.remove('copied'); }, 2000);
        });
      }
    }
    // Timezone selector for time of day chart
    const rawHourCounts = "{}";
    function updateHourHistogram(offsetFromPT) {
      const periods = [
        { label: "Morning (6-12)", range: [6,7,8,9,10,11] },
        { label: "Afternoon (12-18)", range: [12,13,14,15,16,17] },
        { label: "Evening (18-24)", range: [18,19,20,21,22,23] },
        { label: "Night (0-6)", range: [0,1,2,3,4,5] }
      ];
      const adjustedCounts = {};
      for (const [hour, count] of Object.entries(rawHourCounts)) {
        const newHour = (parseInt(hour) + offsetFromPT + 24) % 24;
        adjustedCounts[newHour] = (adjustedCounts[newHour] || 0) + count;
      }
      const periodCounts = periods.map(p => ({
        label: p.label,
        count: p.range.reduce((sum, h) => sum + (adjustedCounts[h] || 0), 0)
      }));
      const maxCount = Math.max(...periodCounts.map(p => p.count)) || 1;
      const container = document.getElementById('hour-histogram');
      container.textContent = '';
      periodCounts.forEach(p => {
        const row = document.createElement('div');
        row.className = 'bar-row';
        const label = document.createElement('div');
        label.className = 'bar-label';
        label.textContent = p.label;
        const track = document.createElement('div');
        track.className = 'bar-track';
        const fill = document.createElement('div');
        fill.className = 'bar-fill';
        fill.style.width = (p.count / maxCount) * 100 + '%';
        fill.style.background = '#8b5cf6';
        track.appendChild(fill);
        const value = document.createElement('div');
        value.className = 'bar-value';
        value.textContent = p.count;
        row.appendChild(label);
        row.appendChild(track);
        row.appendChild(value);
        container.appendChild(row);
      });
    }
    document.getElementById('timezone-select').addEventListener('change', function() {
      const customInput = document.getElementById('custom-offset');
      if (this.value === 'custom') {
        customInput.style.display = 'inline-block';
        customInput.focus();
      } else {
        customInput.style.display = 'none';
        updateHourHistogram(parseInt(this.value));
      }
    });
    document.getElementById('custom-offset').addEventListener('change', function() {
      const offset = parseInt(this.value) + 8;
      updateHourHistogram(offset);
    });
  </script>
</body>
</html>
"""

        return html


def main():
    """Main entry point for generating the report."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate Claude Code insights report")
    parser.add_argument(
        "--output", "-o", default="insights.html", help="Output HTML file path"
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip LLM-based narrative generation (stats only)",
    )
    parser.add_argument(
        "--llm-url",
        default=os.environ.get("LLAMA_CPP_BASE_URL", "LLLM_API_HERE"),
        help="LLama.cpp base URL",
    )
    parser.add_argument(
        "--llm-model",
        default=os.environ.get("LLAMA_CPP_MODEL", "local-model"),
        help="LLama.cpp model name",
    )
    parser.add_argument(
        "--data-dir",
        default=str(USAGE_DATA_DIR),
        help="Path to usage data directory",
    )

    args = parser.parse_args()

    print("Loading usage data...")
    analyzer = DataAnalyzer(Path(args.data_dir))
    print(f"Loaded {len(analyzer.sessions)} sessions, {len(analyzer.facets)} facets")

    # Create LLM client if not disabled
    llm_client = None
    if not args.no_llm:
        print(f"Connecting to LLM at {args.llm_url}...")
        llm_client = LLMClient(args.llm_url, args.llm_model)

    # Create report generator
    generator = HTMLReportGenerator(analyzer, llm_client)

    # Generate narratives if LLM available
    if llm_client:
        print("\nGenerating narratives with LLM...")
        generator.generate_narratives()

    # Generate HTML report
    print("\nGenerating HTML report...")
    generator.generate_html(args.output)

    print("\nDone!")


if __name__ == "__main__":
    main()
