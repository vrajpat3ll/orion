import asyncio
import click
import sys
from typing import Union
from cmd.cli import CLI


@click.command()
@click.argument("prompt", required=False)
def main(
    prompt: Union[str, None],
):
    cli = CLI()
    if prompt:
        # print(f"{prompt = }")
        result = asyncio.run(cli.run_single(prompt))
        if result is None:
            sys.exit(1)
    # messages = [{"role": "user", "content": prompt}]


if __name__ == "__main__":
    print("Hello from orion!")
    main()
