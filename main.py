import asyncio
from pathlib import Path
import click
import sys
from typing import Any, Dict, Optional
from cmd.cli import CLI
from config.loader import load_config
from ui.tui import get_console

console = get_console()


@click.command()
@click.argument("prompt", required=False)
@click.option(
    "--cwd",
    "-c",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Current working directory",
    required=False,
)
@click.option(
    "--info",
    is_flag=True,
    default=False,
    help="Show config info card",
    required=False,
)
def main(
    prompt: Optional[str],
    cwd: Optional[Path] = None,
    info: bool = False,
):
    if cwd:
        cwd = cwd.resolve()
    try:
        config = load_config(cwd=cwd)
        errors = config.validate()
        if errors:
            for e in errors:
                console.print(f"\n[error]{e}[/error]")
            sys.exit(1)
    except Exception as e:
        console.print(f"\n[error] Configuration Error: {e}[/error]")
        sys.exit(1)

    kwargs: Dict[str, Any] = {
        "info": info,
    }

    cli = CLI(config=config, **kwargs)

    if prompt:
        result = asyncio.run(cli.run_single(prompt))
        if result is None:
            sys.exit(1)
    else:
        asyncio.run(cli.run_interactive())


if __name__ == "__main__":
    print("Hello from orion!")
    main()
