import sys
import click

# Import the core scraper run function (will be implemented later)
try:
    from .scraper.keycrm_scraper import run
except ImportError:
    # Fallback placeholder for early development stage
    def run(*args, **kwargs):  # type: ignore
        click.echo('Core scraper not implemented yet.')
        sys.exit(0)

@click.command()
@click.option('--headless/--no-headless', default=True,
              help='Run browser in headless mode (default: headless).')
@click.option('--yes', '-y', 'skip_confirmation', is_flag=True, default=False,
              help='Skip interactive confirmations (for automated runs).')
@click.option('--managers', default='',
              help='Comma‑separated list of manager names to filter (default: empty → no manager filter).')
@click.option('--statuses', default='',
              help='Comma‑separated list of order statuses to filter (default: all).')
@click.option('--rows', default=100, type=int,
              help='Number of rows per page to display in the orders table.')
@click.option('--limit', default=None, type=int,
              help='Limit number of orders to scrape (for testing).')
def main(headless: bool, skip_confirmation: bool, managers: str, statuses: str, rows: int, limit: int | None) -> None:
    """Entry point for the KeyCRM scraper.

    The command collects CLI arguments, prepares them and invokes the core
    scraping routine. Interactive confirmations are handled inside the core
    workflow.
    """
    manager_list = [m.strip() for m in managers.split(',') if m.strip()]
    status_list = [s.strip() for s in statuses.split(',') if s.strip()]

    click.echo('Starting KeyCRM scraper with the following configuration:')
    click.echo(f'  Headless mode: {headless}')
    click.echo(f'  Managers filter: {manager_list or "(none)"}')
    click.echo(f'  Statuses filter: {status_list or "(all)"}')
    click.echo(f'  Rows per page: {rows}')
    if limit:
        click.echo(f'  Limit: {limit} orders')

    # Run the scraper – the function will raise click.Abort on user cancellation.
    run(
        headless=headless,
        managers=manager_list,
        statuses=status_list,
        rows_per_page=rows,
        skip_confirmation=skip_confirmation,
        limit=limit,
    )

if __name__ == '__main__':
    # When executed directly, invoke the click command.
    main()
