from pywebio.output import *
from pywebio import start_server
from utils import *
from navigation import navigate_to_main
from config import *


page_title = "Admins Overview"


def admin_overview(main_func=None):
    """Render header"""
    if main_func:
        page_init(back_to_main_text, page_title, lambda: navigate_to_main(main_func))
    else:
        page_init(back_to_main_text, page_title)

    """Fetch data"""
    data = fetch_admin_overview(dashboard, ORGANIZATION_ID)
    """Display data"""
    put_datatable(data)


def fetch_admin_overview(dashboard, organization_id):
    with put_loading():
        put_text("Fetching data, please wait...")
        admins = dashboard.organizations.getOrganizationAdmins(organization_id)
    return admins


def main():
    """Main function for standalone execution"""
    # Start the server with the admin_overview function
    start_server(lambda: admin_overview(), port=8999, debug=True)


if __name__ == "__main__":
    main()
