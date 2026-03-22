#!/usr/bin/env python3
"""
Claude Code Usage Data Insights Generator

Generates an HTML report analyzing Claude Code usage data using:
- Statistical analysis for charts and metrics
- Local LLM (llama.cpp) for narrative sections
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import urllib.request
import urllib.error
import time

# Configuration
LLAMA_CPP_BASE_URL = os.environ.get(
    "LLAMA_CPP_BASE_URL", "REPLACE_HERE"
)
LLAMA_CPP_MODEL = os.environ.get("LLAMA_CPP_MODEL", "local-model")
USAGE_DATA_DIR = Path("~/.claude/usage-data")


class DataAnalyzer:
    """Loads and analyzes usage data from session-meta and facets directories."""

    def __init__(self, data_dir: Path = USAGE_DATA_DIR):
        self.data_dir = data_dir
        self.sessions: List[Dict] = []
        self.facets: Dict[str, Dict] = {}
        self._load_data()

    def _load_data(self):
        """Load all session metadata and facets data."""
        # Load session metadata
        session_meta_dir = self.data_dir / "session-meta"
        if session_meta_dir.exists():
            for json_file in session_meta_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        session = json.load(f)
                        session["_source_file"] = json_file.name
                        self.sessions.append(session)
                except Exception as e:
                    print(f"Warning: Failed to load {json_file}: {e}")

        # Load facets (analyzed session data)
        facets_dir = self.data_dir / "facets"
        if facets_dir.exists():
            for json_file in facets_dir.glob("*.json"):
                try:
                    with open(json_file) as f:
                        facet = json.load(f)
                        session_id = facet.get("session_id")
                        if session_id:
                            self.facets[session_id] = facet
                except Exception as e:
                    print(f"Warning: Failed to load facet {json_file}: {e}")

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session metadata by ID."""
        for session in self.sessions:
            if session.get("session_id") == session_id:
                return session
        return None

    def get_facet(self, session_id: str) -> Optional[Dict]:
        """Get facet data by session ID."""
        return self.facets.get(session_id)

    def get_merged_sessions(self) -> List[Dict]:
        """Get all sessions merged with their facets."""
        merged = []
        for session in self.sessions:
            session_id = session.get("session_id")
            merged_session = session.copy()
            if session_id and session_id in self.facets:
                merged_session["facet"] = self.facets[session_id]
            merged.append(merged_session)
        return merged

    # === Statistical Analysis Methods ===

    def get_date_range(self) -> Tuple[str, str]:
        """Get the date range of all sessions."""
        if not self.sessions:
            return "", ""

        timestamps = []
        for session in self.sessions:
            start_time = session.get("start_time", "")
            if start_time:
                timestamps.append(start_time)

        if not timestamps:
            return "", ""

        timestamps.sort()
        start = timestamps[0][:10] if len(timestamps[0]) >= 10 else timestamps[0]
        end = timestamps[-1][:10] if len(timestamps[-1]) >= 10 else timestamps[-1]
        return start, end

    def get_total_messages(self) -> int:
        """Get total message count across all sessions."""
        total = 0
        for session in self.sessions:
            total += session.get("user_message_count", 0) or 0
            total += session.get("assistant_message_count", 0) or 0
        return total

    def get_lines_stats(self) -> Tuple[int, int]:
        """Get total lines added and removed."""
        added, removed = 0, 0
        for session in self.sessions:
            added += session.get("lines_added", 0) or 0
            removed += session.get("lines_removed", 0) or 0
        return added, removed

    def get_files_modified(self) -> int:
        """Get total unique files modified."""
        # This would require more detailed tracking; return sum for now
        return sum(s.get("files_modified", 0) or 0 for s in self.sessions)

    def get_git_commits(self) -> int:
        """Get total git commits."""
        return sum(s.get("git_commits", 0) or 0 for s in self.sessions)

    def get_tool_counts(self) -> Dict[str, int]:
        """Aggregate tool counts across all sessions."""
        totals = defaultdict(int)
        for session in self.sessions:
            tool_counts = session.get("tool_counts", {})
            for tool, count in tool_counts.items():
                totals[tool] += count
        return dict(totals)

    def get_language_counts(self) -> Dict[str, int]:
        """Aggregate language counts across all sessions."""
        totals = defaultdict(int)
        for session in self.sessions:
            languages = session.get("languages", {})
            for lang, count in languages.items():
                totals[lang] += count
        return dict(totals)

    def get_goal_categories(self) -> Dict[str, int]:
        """Aggregate goal categories from facets."""
        totals = defaultdict(int)
        for facet in self.facets.values():
            categories = facet.get("goal_categories", {})
            for cat, count in categories.items():
                totals[cat] += count
        return dict(totals)

    def get_outcome_counts(self) -> Dict[str, int]:
        """Count outcomes from facets."""
        counts = defaultdict(int)
        for facet in self.facets.values():
            outcome = facet.get("outcome", "")
            if outcome:
                counts[outcome] += 1
        return dict(counts)

    def get_satisfaction_counts(self) -> Dict[str, int]:
        """Aggregate satisfaction counts from facets."""
        totals = defaultdict(int)
        for facet in self.facets.values():
            counts = facet.get("user_satisfaction_counts", {})
            for sat, count in counts.items():
                totals[sat] += count
        return dict(totals)

    def get_friction_counts(self) -> Dict[str, int]:
        """Aggregate friction counts from facets."""
        totals = defaultdict(int)
        for facet in self.facets.values():
            counts = facet.get("friction_counts", {})
            for friction, count in counts.items():
                totals[friction] += count
        return dict(totals)

    def get_primary_success_counts(self) -> Dict[str, int]:
        """Count primary success categories from facets."""
        counts = defaultdict(int)
        for facet in self.facets.values():
            success = facet.get("primary_success", "")
            if success:
                counts[success] += 1
        return dict(counts)

    def get_session_type_counts(self) -> Dict[str, int]:
        """Count session types from facets."""
        counts = defaultdict(int)
        for facet in self.facets.values():
            stype = facet.get("session_type", "")
            if stype:
                counts[stype] += 1
        return dict(counts)

    def get_claude_helpfulness_counts(self) -> Dict[str, int]:
        """Count claude helpfulness ratings from facets."""
        counts = defaultdict(int)
        for facet in self.facets.values():
            helpful = facet.get("claude_helpfulness", "")
            if helpful:
                counts[helpful] += 1
        return dict(counts)

    def get_response_time_stats(self) -> Dict:
        """Calculate user response time statistics."""
        response_times = []
        for session in self.sessions:
            times = session.get("user_response_times", [])
            if times:
                response_times.extend(times)

        if not response_times:
            return {"median": 0, "average": 0, "distribution": []}

        response_times.sort()
        median = response_times[len(response_times) // 2]
        average = sum(response_times) / len(response_times)

        # Distribution buckets
        buckets = [
            (2, 10, "2-10s"),
            (10, 30, "10-30s"),
            (30, 60, "30s-1m"),
            (60, 120, "1-2m"),
            (120, 300, "2-5m"),
            (300, 900, "5-15m"),
            (900, float("inf"), ">15m"),
        ]

        distribution = []
        for min_t, max_t, label in buckets:
            count = sum(1 for t in response_times if min_t <= t < max_t)
            distribution.append({"label": label, "count": count})

        return {"median": median, "average": average, "distribution": distribution}

    def get_hourly_distribution(self, offset_hours: int = 0) -> Dict[str, int]:
        """Get message distribution by hour of day."""
        hourly = defaultdict(int)

        for session in self.sessions:
            timestamps = session.get("user_message_timestamps", [])
            for ts in timestamps:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    hour = (dt.hour + offset_hours) % 24
                    hourly[hour] += 1
                except:
                    pass

        return dict(hourly)

    def get_project_areas(self) -> List[Dict]:
        """Extract project areas from session data."""
        # Group by project path
        project_sessions = defaultdict(list)
        for session in self.sessions:
            project_path = session.get("project_path", "unknown")
            if project_path:
                # Simplify path to just the last few components
                parts = Path(project_path).parts
                simplified = "/".join(parts[-3:]) if len(parts) > 3 else project_path
                project_sessions[simplified].append(session)

        areas = []
        for project, sessions in sorted(
            project_sessions.items(), key=lambda x: -len(x[1])
        ):
            if len(sessions) >= 2:  # Only include projects with 2+ sessions
                # Get primary language
                lang_counts = defaultdict(int)
                for s in sessions:
                    for lang, count in s.get("languages", {}).items():
                        lang_counts[lang] += count
                primary_lang = (
                    max(lang_counts.items(), key=lambda x: x[1])[0]
                    if lang_counts
                    else "Unknown"
                )

                areas.append(
                    {
                        "name": project,
                        "session_count": len(sessions),
                        "primary_language": primary_lang,
                    }
                )

        return areas[:10]  # Top 10

    def get_multiclauding_stats(self) -> Dict:
        """Detect parallel session usage (multi-clauding)."""
        if len(self.sessions) < 2:
            return {"overlap_events": 0, "sessions_involved": 0, "percentage": 0}

        # Build session time ranges
        session_ranges = []
        for session in self.sessions:
            start_str = session.get("start_time", "")
            duration = session.get("duration_minutes", 0) or 0
            if start_str:
                try:
                    start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    end = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    # Add duration to end time (rough estimate)
                    from datetime import timedelta

                    end = end + timedelta(minutes=duration + 5)  # +5 min buffer
                    session_ranges.append(
                        {"id": session.get("session_id"), "start": start, "end": end}
                    )
                except:
                    pass

        # Count overlaps
        overlap_events = 0
        sessions_with_overlaps = set()

        for i, r1 in enumerate(session_ranges):
            for r2 in session_ranges[i + 1 :]:
                # Check if ranges overlap
                if r1["start"] < r2["end"] and r2["start"] < r1["end"]:
                    overlap_events += 1
                    sessions_with_overlaps.add(r1["id"])
                    sessions_with_overlaps.add(r2["id"])

        total_messages = self.get_total_messages()
        percentage = (
            (len(sessions_with_overlaps) / len(self.sessions) * 100)
            if self.sessions
            else 0
        )

        return {
            "overlap_events": overlap_events,
            "sessions_involved": len(sessions_with_overlaps),
            "percentage": round(percentage, 1),
        }

    def get_friction_context(self) -> List[Dict]:
        """Extract friction events with full session context."""
        friction_events = []

        for session in self.sessions:
            session_id = session.get("session_id", "")
            facet = self.facets.get(session_id, {})

            # Get friction types for this session
            friction_counts = facet.get("friction_counts", {})
            if not friction_counts:
                continue

            # Get session context
            first_prompt = session.get("first_prompt", "")[:200]
            goal = facet.get("underlying_goal", "")
            brief_summary = facet.get("brief_summary", "")
            outcome = facet.get("outcome", "")
            primary_success = facet.get("primary_success", "")

            # Get project area
            project_path = session.get("project_path", "")
            if project_path:
                parts = Path(project_path).parts
                project_name = "/".join(parts[-3:]) if len(parts) > 3 else project_path
            else:
                project_name = "unknown"

            # Build friction event for each friction type
            for friction_type, count in friction_counts.items():
                if count > 0:
                    friction_events.append(
                        {
                            "session_id": session_id[:8],
                            "friction_type": friction_type,
                            "friction_count": count,
                            "first_prompt": first_prompt,
                            "goal": goal,
                            "brief_summary": brief_summary,
                            "outcome": outcome,
                            "primary_success": primary_success,
                            "project_name": project_name,
                        }
                    )

        return friction_events

    def get_tool_error_counts(self) -> Dict[str, int]:
        """Extract tool error counts from session data."""
        error_counts = defaultdict(int)

        for session in self.sessions:
            # Check for tool error data in session
            tool_errors = session.get("tool_errors", {})
            if isinstance(tool_errors, dict):
                for error_type, count in tool_errors.items():
                    error_counts[error_type] += count
            elif isinstance(tool_errors, int):
                error_counts["Other"] += tool_errors

            # Also check rejected actions
            rejected = session.get("user_rejected_action_count", 0) or 0
            if rejected > 0:
                error_counts["User Rejected"] += rejected

        return dict(error_counts)

    def get_session_examples_by_friction(
        self, friction_type: str, limit: int = 5
    ) -> List[Dict]:
        """Get example sessions for a specific friction type with context."""
        examples = []

        for session in self.sessions:
            session_id = session.get("session_id", "")
            facet = self.facets.get(session_id, {})
            friction_counts = facet.get("friction_counts", {})

            if friction_counts.get(friction_type, 0) > 0:
                examples.append(
                    {
                        "session_id": session_id[:8],
                        "first_prompt": session.get("first_prompt", "")[:150],
                        "goal": facet.get("underlying_goal", ""),
                        "brief_summary": facet.get("brief_summary", ""),
                        "outcome": facet.get("outcome", ""),
                        "friction_count": friction_counts.get(friction_type, 0),
                    }
                )
                if len(examples) >= limit:
                    break

        return examples


class LLMClient:
    """Client for llama.cpp OpenAI-compatible endpoint."""

    def __init__(
        self, base_url: str = LLAMA_CPP_BASE_URL, model: str = LLAMA_CPP_MODEL
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def call(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        max_tokens: int = 30000,
        temperature: float = 0.7,
        retry_count: int = 3,
        retry_delay: float = 5.0,
    ) -> str:
        """Make a call to the llama.cpp endpoint with retry logic."""
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        for attempt in range(retry_count):
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/chat/completions",
                    data=json.dumps(data).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=300) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    return result["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"LLM call failed (attempt {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        raise Exception(f"LLM call failed after {retry_count} attempts")


class NarrativeGenerator:
    """Generates narrative sections using LLM calls."""

    def __init__(self, analyzer: DataAnalyzer, llm_client: LLMClient):
        self.analyzer = analyzer
        self.llm = llm_client

    def _prepare_session_context(self, max_sessions: int = 50) -> str:
        """Prepare session data context for LLM prompts."""
        merged = self.analyzer.get_merged_sessions()
        context_parts = []

        for session in merged[:max_sessions]:
            sid = session.get("session_id", "unknown")[:8]
            first_prompt = session.get("first_prompt", "")[:200]
            facet = session.get("facet", {})
            goal = facet.get("underlying_goal", "")[:200]
            brief = facet.get("brief_summary", "")[:200]
            outcome = facet.get("outcome", "")

            context_parts.append(
                f"Session {sid}:\n"
                f"  First prompt: {first_prompt}...\n"
                f"  Goal: {goal}\n"
                f"  Summary: {brief}\n"
                f"  Outcome: {outcome}"
            )

        return "\n\n".join(context_parts)

    def generate_project_areas(self) -> List[Dict]:
        """Generate project areas analysis using LLM."""
        context = self._prepare_session_context(30)

        prompt = f"""Analyze this Claude Code usage data and identify project areas.

RESPOND WITH ONLY A VALID JSON OBJECT:
{{
  "areas": [
    {{"name": "Area name", "session_count": N, "description": "2-3 sentences about what was worked on and how Claude Code was used."}}
  ]
}}

Include 4-5 areas. Skip internal CC operations.

SESSION DATA:
{context}"""

        try:
            result = self.llm.call(prompt, max_tokens=2048)
            # Extract JSON from response
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                data = json.loads(json_str)
                return data.get("areas", [])
        except Exception as e:
            print(f"Failed to generate project areas: {e}")

        # Fallback to statistical analysis
        return self.analyzer.get_project_areas()

    def generate_interaction_style(self) -> Dict:
        """Generate interaction style analysis using LLM."""
        context = self._prepare_session_context(40)
        stats = self._get_summary_stats()

        prompt = f"""Analyze this Claude Code usage data and describe the user's interaction style.

RESPOND WITH ONLY A VALID JSON OBJECT:
{{
  "narrative": "2-3 paragraphs analyzing HOW the user interacts with Claude Code. Use second person 'you'. Describe patterns: iterate quickly vs detailed upfront specs? Interrupt often or let Claude run? Include specific examples. Use **bold** for key insights.",
  "key_pattern": "One sentence summary of most distinctive interaction style"
}}"

SESSION DATA:
{context}

SUMMARY STATS:
{stats}"""

        try:
            result = self.llm.call(prompt, max_tokens=2048)
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Failed to generate interaction style: {e}")

        return {
            "narrative": "Analysis unavailable.",
            "key_pattern": "Pattern detection unavailable.",
        }

    def generate_what_works(self) -> Dict:
        """Generate 'what works' analysis using LLM."""
        context = self._prepare_session_context(30)

        prompt = f"""Analyze this Claude Code usage data and identify what's working well for this user. Use second person ("you").

RESPOND WITH ONLY A VALID JSON OBJECT:
{{
  "intro": "1 sentence of context",
  "impressive_workflows": [
    {{"title": "Short title (3-6 words)", "description": "2-3 sentences describing the impressive workflow or approach. Use 'you' not 'the user'."}}
  ]
}}

Include 3 impressive workflows.

SESSION DATA:
{context}"""

        try:
            result = self.llm.call(prompt, max_tokens=2048)
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Failed to generate what_works: {e}")

        return {
            "intro": "Analysis unavailable.",
            "impressive_workflows": [],
        }

    def generate_friction_analysis(self) -> Dict:
        """Generate friction analysis using LLM with session context."""
        # Get friction context with session details
        friction_context = self.analyzer.get_friction_context()

        # Group by friction type for analysis
        friction_by_type = defaultdict(list)
        for event in friction_context:
            friction_by_type[event["friction_type"]].append(event)

        # Prepare compact context for top friction types
        top_friction_types = sorted(
            friction_by_type.keys(),
            key=lambda t: sum(e["friction_count"] for e in friction_by_type[t]),
            reverse=True,
        )[:3]  # Only top 3 friction types

        context_parts = []
        for friction_type in top_friction_types:
            events = friction_by_type[friction_type][:2]  # Top 2 sessions per type
            context_parts.append(f"{friction_type.upper()}:")
            for event in events:
                goal = event.get("goal", "")[:80]
                summary = event.get("brief_summary", "")[:80]
                context_parts.append(f"  [{event['session_id']}] {goal} -> {summary}")

        context = "\n".join(context_parts)

        prompt = f"""Analyze this Claude Code friction data. Use second person ("you").

JSON format ONLY:
{{
  "intro": "1 sentence on main friction pattern",
  "categories": [
    {{
      "category": "Category name (5-8 words)",
      "description": "What friction and suggestion. Use 'you'.",
      "examples": [{{"session": "id", "context": "topic", "issue": "problem", "consequence": "impact"}}]
    }}
  ]
}}

3 categories, 2 examples each.

FRICTION DATA:
{context}"""

        try:
            result = self.llm.call(prompt, max_tokens=2000)
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Failed to generate friction analysis: {e}")

        return {"intro": "Analysis unavailable.", "categories": []}

    def _get_summary_stats(self) -> str:
        """Get summary statistics for context."""
        tool_counts = self.analyzer.get_tool_counts()
        lang_counts = self.analyzer.get_language_counts()
        goal_cats = self.analyzer.get_goal_categories()
        friction = self.analyzer.get_friction_counts()

        return f"""Sessions: {len(self.analyzer.sessions)}
Total messages: {self.analyzer.get_total_messages()}
Top tools: {dict(sorted(tool_counts.items(), key=lambda x: -x[1])[:3])}
Top languages: {dict(sorted(lang_counts.items(), key=lambda x: -x[1])[:3])}
Top goals: {dict(sorted(goal_cats.items(), key=lambda x: -x[1])[:3])}
Friction: {dict(sorted(friction.items(), key=lambda x: -x[1])[:3])}"""

    def generate_features_to_try(self) -> Dict:
        """Generate 'Features to Try' suggestions using LLM."""
        friction = self.analyzer.get_friction_counts()
        goal_cats = self.analyzer.get_goal_categories()
        tool_counts = self.analyzer.get_tool_counts()

        prompt = f"""Suggest Claude Code features for this user based on stats.

JSON ONLY:
{{
  "claude_md_additions": [{{"code": "text for CLAUDE.md", "why": "reason", "section": "section name"}}],
  "features": [{{"name": "feature", "description": "what it does", "why_for_you": "why", "example": "example"}}]
}}

Stats:
Friction: {dict(sorted(friction.items(), key=lambda x: -x[1])[:3])}
Goals: {dict(sorted(goal_cats.items(), key=lambda x: -x[1])[:3])}
Tools: {dict(sorted(tool_counts.items(), key=lambda x: -x[1])[:3])}

4 CLAUDE.md additions, 2-3 features. Keep concise."""

        try:
            result = self.llm.call(prompt, max_tokens=2000)
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Failed to generate features to try: {e}")

        return {"claude_md_additions": [], "features": []}

    def generate_usage_patterns(self) -> List[Dict]:
        """Generate 'New Usage Patterns' suggestions using LLM."""
        goal_cats = self.analyzer.get_goal_categories()
        friction = self.analyzer.get_friction_counts()

        prompt = f"""Suggest 3 new usage patterns this user could adopt based on their data.

JSON format:
{{
  "patterns": [
    {{
      "title": "Short title (5-8 words)",
      "summary": "One sentence what pattern to adopt",
      "detail": "2-3 sentences explaining the pattern and why it helps their specific workflow",
      "prompt": "A copyable prompt they can paste into Claude Code to try this pattern"
    }}
  ]
}}

Their top goals: {dict(sorted(goal_cats.items(), key=lambda x: -x[1])[:3])}
Their top friction: {dict(sorted(friction.items(), key=lambda x: -x[1])[:3])}

Focus on patterns that address their friction points or amplify their successful workflows."""

        try:
            result = self.llm.call(prompt, max_tokens=2500)
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                data = json.loads(json_str)
                return data.get("patterns", [])
        except Exception as e:
            print(f"Failed to generate usage patterns: {e}")

        return []

    def generate_horizon(self) -> List[Dict]:
        """Generate 'On the Horizon' ambitious workflow suggestions."""
        goal_cats = self.analyzer.get_goal_categories()
        tool_counts = self.analyzer.get_tool_counts()
        multiclauding = self.analyzer.get_multiclauding_stats()

        prompt = f"""Suggest 3 ambitious future workflows this user could adopt as models become more capable.

JSON format:
{{
  "horizon": [
    {{
      "title": "Ambitious workflow title",
      "possible": "2-3 sentences describing what becomes possible and how it transforms their workflow",
      "getting_started": "One sentence on how to start moving in this direction now",
      "prompt": "A detailed prompt they can try now that points toward this future"
    }}
  ]
}}

Their usage context:
- Top goals: {dict(sorted(goal_cats.items(), key=lambda x: -x[1])[:3])}
- Top tools: {dict(sorted(tool_counts.items(), key=lambda x: -x[1])[:3])}
- Multi-clauding: {multiclauding}

Focus on autonomous workflows, multi-agent orchestration, or test-driven iteration loops."""

        try:
            result = self.llm.call(prompt, max_tokens=2500)
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                data = json.loads(json_str)
                return data.get("horizon", [])
        except Exception as e:
            print(f"Failed to generate horizon: {e}")

        return []

    def generate_at_a_glance(self) -> Dict:
        """Generate 'At a Glance' summary section."""
        stats = self._get_summary_stats()
        friction = self.analyzer.get_friction_counts()
        outcomes = self.analyzer.get_outcome_counts()

        prompt = f"""Generate a concise 'At a Glance' summary for this user's Claude Code usage.

JSON format:
{{
  "whats_working": "2-3 sentences highlighting their most impressive workflows. Use 'you'.",
  "whats_hindering": "2 sentences summarizing main friction points (both Claude's and user's side). Use 'you'.",
  "quick_wins": "1-2 sentences with specific actionable suggestions. Use 'you'.",
  "ambitious_workflows": "1-2 sentences pointing toward future autonomous workflows. Use 'you'."
}}

Usage stats:
{stats}

Friction: {dict(sorted(friction.items(), key=lambda x: -x[1])[:3])}
Outcomes: {dict(sorted(outcomes.items(), key=lambda x: -x[1])[:3])}

Keep each section under 400 characters. Be specific and actionable."""

        try:
            result = self.llm.call(prompt, max_tokens=2000)
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Failed to generate at-a-glance: {e}")

        return {
            "whats_working": "Analysis unavailable.",
            "whats_hindering": "Analysis unavailable.",
            "quick_wins": "Analysis unavailable.",
            "ambitious_workflows": "Analysis unavailable.",
        }

    def generate_fun_ending(self) -> Dict:
        """Generate a fun/humorous ending based on session data."""
        # Look for interesting moments in sessions
        merged = self.analyzer.get_merged_sessions()

        # Find sessions with interesting patterns
        funny_moments = []
        for session in merged[:50]:  # Check first 50 sessions
            facet = session.get("facet", {})
            first_prompt = session.get("first_prompt", "")
            brief = facet.get("brief_summary", "")

            # Look for denial/correction patterns
            if any(
                word in brief.lower()
                for word in ["denied", "wrong", "incorrect", "actually"]
            ):
                funny_moments.append(
                    {
                        "session_id": session.get("session_id", "")[:8],
                        "prompt": first_prompt[:100],
                        "summary": brief,
                    }
                )

        prompt = f"""Find or create a fun, lighthearted moment from this user's Claude Code sessions.

JSON format:
{{
  "headline": "A catchy, humorous headline (max 150 chars)",
  "detail": "1-2 sentences explaining the funny moment (max 200 chars)"
}}

Session highlights to work with:
{str(funny_moments[:3]) if funny_moments else "No particularly funny moments found - create something light and encouraging instead."}

Keep it positive and playful. If no real funny moment exists, create an encouraging message."""

        try:
            result = self.llm.call(prompt, max_tokens=1000)
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Failed to generate fun ending: {e}")

        return {
            "headline": "Keep up the great work!",
            "detail": "Your Claude Code journey continues to evolve. Happy coding!",
        }


def main():
    """Main entry point for testing data loading."""
    print("Loading usage data...")
    analyzer = DataAnalyzer()

    print(f"\nLoaded {len(analyzer.sessions)} sessions")
    print(f"Loaded {len(analyzer.facets)} facets")

    start_date, end_date = analyzer.get_date_range()
    print(f"Date range: {start_date} to {end_date}")

    print(f"\nTotal messages: {analyzer.get_total_messages()}")
    lines_added, lines_removed = analyzer.get_lines_stats()
    print(f"Lines: +{lines_added}/-{lines_removed}")

    print(f"\nGit commits: {analyzer.get_git_commits()}")

    print("\nTop tools:")
    tool_counts = analyzer.get_tool_counts()
    for tool, count in sorted(tool_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"  {tool}: {count}")

    print("\nLanguages:")
    lang_counts = analyzer.get_language_counts()
    for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"  {lang}: {count}")

    print("\nGoal categories:")
    goal_cats = analyzer.get_goal_categories()
    for cat, count in sorted(goal_cats.items(), key=lambda x: -x[1])[:5]:
        print(f"  {cat}: {count}")

    print("\nOutcomes:")
    outcomes = analyzer.get_outcome_counts()
    for outcome, count in sorted(outcomes.items(), key=lambda x: -x[1]):
        print(f"  {outcome}: {count}")

    print("\nProject areas:")
    areas = analyzer.get_project_areas()
    for area in areas[:5]:
        print(f"  {area['name']}: {area['session_count']} sessions")


if __name__ == "__main__":
    main()
