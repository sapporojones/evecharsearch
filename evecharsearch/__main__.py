import click
import snoop

from lookup_controller import LookupController


@click.command()
@click.option("--name", default="Baldur Kilgannon", help="Name of character to search.")
def main(name):
    """A CLI app to find public information about an EVE Online character"""
    LookupController(name)


if __name__ == "__main__":
    main()
