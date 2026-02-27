# Orion — Personal AI Coding Agent

![CI](https://github.com/vrajpat3ll/orion/actions/workflows/ci.yml/badge.svg)

Orion is an autonomous AI coding agent designed to assist with software development workflows. It provides an interactive command-line interface for executing prompts, managing tools, and automating development tasks.

## Features

- **Interactive CLI** — run prompts and workflows directly from your terminal
- **Tool Integration** — execute shell commands, read/write files, and automate tasks
- **Context Management** — maintains conversation state across multiple turns
- **Streaming Responses** — real-time output for improved responsiveness
- **Configurable** — environment variables and config-based customization
- **Docker Support** — reproducible and dependency-free deployment

## Installation

### Prerequisites

- Python **3.12+**
- OpenRouter API key

We use **uv** for dependency management.

Install uv:

```bash
pip install uv
```

or follow official instructions:
[https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

### Setup

```bash
git clone https://github.com/vrajpat3ll/orion.git
cd orion

uv sync

# activate virtual environment
./.venv/Scripts/activate   # Windows
source .venv/bin/activate  # macOS/Linux

cp .env.example .env
```

Add your API key to `.env`.

## Configuration

Create a `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here
LLM_BASE_URL=https://openrouter.ai/api/v1/
TAVILY_API_KEY=optional_key
```

## Quickstart (Docker — Recommended)

Run Orion without installing dependencies:

```bash
docker build -t orion .
docker run -it --env-file .env orion
```

## Usage

### Interactive Mode

```bash
uv run main.py
```

### Run a Single Prompt

```bash
uv run main.py "Explain this repository"
```

### Use a Custom Working Directory

```bash
uv run main.py --cwd /path/to/project "Fix imports"
```

### Show Configuration Info

```bash
uv run main.py --info
```

## Docker Usage

### Run a single prompt

```bash
docker run -it --env-file .env orion run "Explain this repo"
```

### Work on a local project

#### macOS / Linux

```bash
docker run -it \
  --env-file .env \
  -v $(pwd):/workspace \
  -w /workspace \
  orion
```

#### Windows PowerShell

```powershell
docker run -it `
  --env-file .env `
  -v ${PWD}:/workspace `
  -w /workspace `
  orion
```

### Pass CLI flags

```bash
docker run -it orion run "fix imports"
docker run -it orion --help
```

## Interactive Commands

These are **yet to be implemented**.
Once in interactive mode:

- `/exit` or `/bye` — exit session
- `/help` — show commands
- `/config` — display configuration
- `/approval` — manage approval settings
- `/model` — show model information

## Example Session

```bash
$ python main.py --info

Hello from orion!
██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗       ╭─────────────────── Config Info Card ────────────────────╮
██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║      │                                                         │
██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║      │              model mistralai/devstral-2512:free         │
██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║      │                cwd C:\CODING\personal\projects\orion    │
╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║      │ Available commands /help /config /approval /model /exit │
 ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝      │                                                         │
               O R I O N                     ╰─────────────────────────────────────────────────────────╯


>> read the contents of this directory and create a README.md file accordingly that showcases how to use this project...
```

## Development

### Run lint checks

```bash
uv run task lint
```

### Adding New Tools

1. Create a tool in `tools/builtin/`
2. Implement required interface
3. Register using `@register_tool`

```python
from orion.tools.base import Tool, ToolInvocation, ToolResult
from orion.tools.registry import register_tool
from pydantic import BaseModel, Field

class Params(BaseModel):
    example: str = Field(...)

@register_tool
class ExampleTool(Tool):
    name = "example"
    description = "Example tool"
    schema = Params

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = Params(**invocation.params)
        ...
```

## Customizing Prompts

Prompt templates are located in:

```
prompts/
```

Modify them to change Orion’s behavior.

## Configuration Sources

Orion can be configured through:

- `.env` environment variables
- CLI arguments
- configuration files

### Environment Variables

| Variable             | Description               |
| -------------------- | ------------------------- |
| `OPENROUTER_API_KEY` | **Required** API key      |
| `LLM_BASE_URL`       | **Required** API endpoint |
| `TAVILY_API_KEY`     | **Optional** web search   |

---

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make changes
4. Run lint/tests
5. Submit a pull request

## License

MIT License

## Support

Open an issue for bugs, questions, or feature requests.

Built with ❤️ by Vraj Patel

## ⚠️ Disclaimer

This README was generated using Orion itself.
