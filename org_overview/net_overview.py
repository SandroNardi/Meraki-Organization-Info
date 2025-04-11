from pywebio.output import *
from pywebio import start_server
from utils import page_init
from navigation import navigate_to_main
from config import *

page_title = "Networks Overview"


def net_overview(main_func=None):
    """Render header"""
    if main_func:
        page_init(back_to_main_text, page_title, lambda: navigate_to_main(main_func))
    else:
        page_init(back_to_main_text, page_title)

    # Fetch data
    data = fetch_net_overview(dashboard, ORGANIZATION_ID)

    # Display data
    put_datatable(data)


def fetch_net_overview(dashboard, organization_id):
    keys_to_include = ["id", "name", "timeZone", "tags"]
    with put_loading():  # Fetch networks from the organization
        networks = dashboard.organizations.getOrganizationNetworks(
            organization_id, total_pages="all"
        )

        # Filter networks based on keys_to_include
        filtered_networks = (
            [
                {key: network[key] for key in keys_to_include if key in network}
                for network in networks
            ]
            if keys_to_include
            else networks
        )
    return filtered_networks


def main():
    """Main function for standalone execution"""
    # Start the server with the net_overview function
    start_server(lambda: net_overview(), port=8999, debug=True)


if __name__ == "__main__":
    main()
