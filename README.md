# Orion - Personal Coding Agent

Orion is a powerful, autonomous AI coding agent designed to assist with software development tasks. It provides an interactive command-line interface for executing prompts, managing tools, and automating workflows.

## Features

- **Interactive CLI**: Engage with Orion through a user-friendly command-line interface
- **Tool Integration**: Execute shell commands, read/write files, and perform various operations
- **Context Management**: Maintain conversation history and context across multiple turns
- **Streaming Responses**: Real-time streaming of AI responses for better user experience
- **Configurable**: Customize behavior through configuration files

## Installation

### Prerequisites

- Python 3.13+
- OpenRouter API key (for LLM access)

We use `uv` for package management.

> Install `uv` [here](https://docs.astral.sh/uv/getting-started/installation/)!
>
> OR just install using pip, `pip install uv`

### Setup

```bash
# Clone the repository
git clone https://github.com/vrajpat3ll/orion.git
cd orion

# Install dependencies
uv sync

# Activate virtual environment
./.venv/Scripts/activate # Windows
source .venv/bin/activate # Linux

# Create a .env file from the example
cp .env.example .env

# Add your OpenRouter API key to .env
```

## Configuration

Create a `.env` file in the project root with your OpenRouter API key:

```env
# get an openrouter API key from https://openrouter.ai/settings/keys after logging in
API_KEY='your-api-key-here'
BASE_URL='https://openrouter.ai/api/v1/'
```

## Usage

### Basic Usage

```bash
# Run Orion in interactive mode
python main.py

# Run a single prompt
python main.py "Your prompt here"

# Run with custom working directory
python main.py --cwd /path/to/your/project "Your prompt"

# Show config info card
python main.py --info
```

### TODO: Interactive Commands

Once in interactive mode, you can use these special commands:

- `/exit` or `/bye`: Exit the interactive session (only this works for now)
- `/help`: Show available commands
- `/config`: Display current configuration
- `/approval`: Manage approval settings
- `/model`: Show current model information

### Example Session

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

### Running Tests

```bash
# Run linting
uv run task lint
```

### Adding New Tools

To add new tools to Orion:

1. Create a new tool class in the `tools/` directory
2. Implement the required interface (name, description, execute method)
3. Register the tool in the tool registry

### Customizing Prompts

Prompt templates are located in the `prompts/` directory. You can modify these to change Orion's behavior and personality.

## Configuration Options

Orion can be configured through:

- Environment variables (`.env` file)
- Command-line arguments
- Configuration files

### Environment Variables

- `API_KEY`: Your OpenRouter API key
- `BASE_URL`: Base URL for the OpenRouter API (could be any endpoint compatible with OpenAI's Python SDK)
  <!-- - `MAX_TURNS`: Maximum number of agent turns (default: 5) -->
  <!-- - `MODEL`: LLM model to use -->

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

Built with ❤️ by Vraj Patel

---

Disclaimer: This README was generated using Orion using the prompt mentioned above in the example.
