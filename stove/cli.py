import click

from .stove import fire_stove


@click.command("stove")
@click.argument("gileum_file")
@click.option(
    "-n",
    "--name",
    default="main",
    help="Gileum name to be targetted.",
)
def main(gileum_file: str, name: str) -> None:
    fire_stove(gileum_file, name)
