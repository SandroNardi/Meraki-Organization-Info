from pywebio.output import *
from pywebio import start_server
from utils import page_init
from navigation import navigate_to_main
from config import *

page_title = "Ms reboot reason"

includedEventTypes = ["boot"]


def ms_reboot_reason(main_func=None):
    """Render header and fetch/display data"""
    if main_func:
        page_init(back_to_main_text, page_title, lambda: navigate_to_main(main_func))
    else:
        page_init(back_to_main_text, page_title)

    # Fetch data
    data = fetch_function(dashboard, ORGANIZATION_ID)

    # Display data
    put_datatable(data)


def fetch_function(dashboard, organization_id):
    with put_loading():
        put_text("Fetching data, please wait...")
        all_event_data = []
        # Fetch all networks for the organization
        networks = dashboard.organizations.getOrganizationNetworks(
            organization_id, total_pages="all"
        )

        for net in networks:
            if "switch" in net["productTypes"]:
                # Fetch network events for switches
                events = dashboard.networks.getNetworkEvents(
                    net["id"],
                    total_pages=10,
                    productType="switch",
                    includedEventTypes=includedEventTypes,
                )

                for event in events.get("events", []):
                    # Extract the reason from eventData if it exists
                    reason = event.get("eventData", {}).get("reason", "N/A")

                    # Add each event as a dictionary without nested structures
                    event_dict = {
                        "Time": event.get("occurredAt", "N/A"),
                        "Name": event.get("deviceName", "N/A"),
                        "Serial": event.get("deviceSerial", "N/A"),
                        "Description": event.get("description", "N/A"),
                        "Category": event.get("category", "N/A"),
                        "Reason": reason,
                    }
                    all_event_data.append(event_dict)

    return all_event_data


def main():
    """Main function for standalone execution"""
    # Start the server with the ms_reboot_reason function
    start_server(lambda: ms_reboot_reason(), port=8999, debug=True)


if __name__ == "__main__":
    main()
