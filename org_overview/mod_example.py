from pywebio.output import *
from pywebio import start_server
from utils import page_init
from navigation import navigate_to_main
from config import *

page_title = "Page title"


def display_function(main_func=None):
    """Render header"""
    if main_func:
        page_init(back_to_main_text, page_title, lambda: navigate_to_main(main_func))
    else:
        page_init(back_to_main_text, page_title)

    # Fetch data
    data = fetch_function(dashboard, ORGANIZATION_ID)

    # Display data
    put_datatable()


def fetch_function(dashboard, organization_id):
    with put_loading():
        put_text("Fetching data, please wait...")

    return


def main():
    """Main function for standalone execution"""
    # Start the server with the mx_sec_status function
    start_server(lambda: display_function(), port=8999, debug=True)


if __name__ == "__main__":
    main()
