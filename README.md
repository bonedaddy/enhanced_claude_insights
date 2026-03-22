# Enhanced Claude Insights

Enhanced Claude Insights is basically the `/insights` command from the claude code TUI, except it can be used to generate insights across all your usage data as opposed to a small subset of your usage data that `/insights` uses.

It uses a combination of statistical analysis for generating charts and metrics from your usage data, and LLM analysis to generate detailed insights + actionable steps you can take to improve your claude code usage.

## Features

- Statistical Analysis - Charts and metrics from your usage data
- LLM-Powered Narratives - Detailed analysis using your local llama.cpp server
- Friction Analysis - Identifies where things go wrong with session context
- Actionable Suggestions - CLAUDE.md additions, features to try, usage patterns
- Future Workflows - Ambitious autonomous workflow suggestions

## Prerequisites

This should work with any OpenAI compatible API, but I tested against llamma.cpp

### 1. llama.cpp Server

You need a local llama.cpp server running with OpenAI-compatible API:

```bash
# Example with Ollama (easiest)
ollama serve
ollama pull llama3.1  # or any model you prefer

# Or with llama.cpp directly
./server -m models/your-model.gguf -c 131072 --host 0.0.0.0 -p 8080
```

The server should be accessible at an endpoint like `http://localhost:8080/v1`.

### 2. Python 3.8+

No external dependencies required - uses only standard library.

### 3. Usage Data

Your usage data should be in `$HOME/.claude/usage-data` or where ever you ahve setup claude code to store that stuff.

Usage data analyzed:

- `session-meta/` - Session JSON files with timing, tools, languages
- `facets/` - Analyzed sessions with goals, outcomes, friction

## Installation

No installation needed - the tool uses Python's standard library.

## Usage

### Basic Usage (with LLM)

```bash
python report_generator.py --output insights.html
```

### Without LLM (Stats Only)

```bash
python report_generator.py --no-llm --output insights.html
```

### Custom Configuration

```bash
python report_generator.py \
    --output insights.html \
    --llm-url http://localhost:8080/v1 \
    --llm-model your-model-name \
    --data-dir /path/to/usage-data
```

### Environment Variables

```bash
export LLAMA_CPP_BASE_URL="http://localhost:8080/v1"
export LLAMA_CPP_MODEL="your-model-name"

python report_generator.py --output insights.html
```

## Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--output, -o` | `insights.html` | Output HTML file path |
| `--no-llm` | `false` | Skip LLM-based narrative generation |
| `--llm-url` | From env or `http://localhost:8080/v1` | Llama.cpp base URL |
| `--llm-model` | From env or `local-model` | Llama.cpp model name |
| `--data-dir` | `$HOME/.claude/usage-data` | Path to usage data directory |

## Report Sections

### At-a-Glance
Quick summary box showing:
- What's working well
- What's hindering you
- Quick wins to try
- Ambitious workflows

### What You Work On
- Project areas with session counts
- Goal categories chart
- Languages used
- Tools used
- Session types

### How You Use Claude Code
- Interaction style analysis
- Response time distribution
- Time of day activity (with timezone selector)
- Tool errors encountered
- Multi-clauding detection

### Impressive Things You Did
- Big wins and successful workflows
- What helped most (Claude's capabilities)
- Outcome distribution

### Where Things Go Wrong
- Friction categories with detailed examples
- Session context for each friction point
- Primary friction types chart
- Inferred satisfaction chart

### Features to Try
- CLAUDE.md additions (copyable with checkboxes)
- Existing CC features (Custom Skills, Hooks, Headless Mode)

### New Usage Patterns
- Copyable prompts to improve workflows
- Based on your specific friction points

### On the Horizon
- Ambitious future workflow suggestions
- Autonomous workflow examples
- Getting started tips

### Team Feedback
- Claude helpfulness ratings

### Fun Ending
- Lighthearted moment from your sessions

## Architecture

```
report_generator.py
├── DataAnalyzer (insights_generator.py)
│   ├── Loads session-meta/*.json
│   ├── Loads facets/*.json
│   ├── Statistical analysis methods
│   └── Friction context extraction
├── LLMClient (insights_generator.py)
│   └── OpenAI-compatible llama.cpp client
├── NarrativeGenerator (insights_generator.py)
│   ├── Project areas analysis
│   ├── Interaction style analysis
│   ├── What works analysis
│   ├── Friction analysis
│   ├── Features to try
│   ├── Usage patterns
│   ├── On the horizon
│   └── Fun ending
└── HTMLReportGenerator (report_generator.py)
    └── Combines stats + narratives into HTML
```

## Data Format

### Session Meta (`session-meta/*.json`)
```json
{
  "session_id": "abc123",
  "start_time": "2026-02-15T10:00:00Z",
  "duration_minutes": 30,
  "user_message_count": 10,
  "assistant_message_count": 10,
  "tool_counts": {"Read": 5, "Edit": 3},
  "languages": {"Rust": 45, "TypeScript": 12},
  "first_prompt": "Help me fix this bug...",
  "user_response_times": [10, 25, 5, ...]
}
```

### Facets (`facets/*.json`)
```json
{
  "session_id": "abc123",
  "underlying_goal": "Debug a bug",
  "goal_categories": {"bug_fix": 1},
  "outcome": "fully_achieved",
  "friction_counts": {"wrong_approach": 2},
  "brief_summary": "Fixed the bug after some iterations"
}
```

## Troubleshooting

### LLM Connection Fails
```bash
# Test connection
curl http://localhost:8080/v1/models

# Check server is running
ps aux | grep llama
```

### Report Generation Slow
- LLM generation can take 10-30 minutes depending on model speed
- Use `--no-llm` for instant stats-only report
- Increase llama.cpp threads: `-t 8`

### Missing Data
```bash
# Check data loaded
python -c "from insights_generator import DataAnalyzer; a = DataAnalyzer(); print(f'Sessions: {len(a.sessions)}, Facets: {len(a.facets)}')"
```

## Performance Notes

LLM used: 

- [Qwen3.5-27B Q4_K_M](https://huggingface.co/Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-GGUF/blob/main/Qwen3.5-27B.Q4_K_M.gguf)

Hardware: 

 - GPU: RTX 5090
 - CPU: 9950 X3D

To analyze 980 sessions and 280 faucets took ~109 seconds.

Startup script for the llama.cpp serve I used

```bash
$> /home/foobar/llama.cpp/build/bin/llama-server \
      -m /home/foobar/models/Qwen3.5-27B.Q4_K_M.gguf \
      --alias Qwen3.5-27B \
      --host 0.0.0.0 --port 8001 \
      --temp 0.6 \
      --top-p 0.95 \
      --top-k 20 \
      --min-p 0.00 \
      --jinja \
      --ctx-size 262144 \
      --n-gpu-layers all \
      --parallel 2 \
      --threads 8 --threads-batch 12 \
      --flash-attn on \
      --batch-size 2048 --ubatch-size 512 \
      --prio 3 --no-warmup \
      --swa-full \
      --no-mmap \
      --mlock \
      --cache-type-k q8_0 \
      --cache-type-v q8_0
```

## License

MIT
