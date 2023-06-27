import click
import timeit
import snoop

from lookup_controller import LookupController


@click.command()
@click.option("--name", default="Sapporo Jones", help="Name of character to search.")
@click.option("--n", default=5, help="Number of kills/losses to retrieve.")
def main(name, n):
    """A CLI app to find public information about an EVE Online character"""
    start = timeit.default_timer()
    LookupController(name, n)
    print(f"\nQuery executed in {timeit.default_timer() - start} seconds.")


if __name__ == "__main__":
    main()
