from pywebio.input import *  # For input elements like DATE
from pywebio.output import *  # For output elements like put_text, put_buttons
from pywebio import start_server, config
from utils import page_init
from navigation import navigate_to_main
from collections import Counter, defaultdict
from config import *

page_title = "Logs Overview"


def logs_overview(main_func=None):
    """Render header"""
    if main_func:
        page_init(back_to_main_text, page_title, lambda: navigate_to_main(main_func))
    else:
        page_init(back_to_main_text, page_title)

    productType = select_product_type(dashboard, ORGANIZATION_ID, product_types_logs)

    selected_events = fetch_log_type(
        dashboard, ORGANIZATION_ID, productType, logs_events_selected[productType]
    )

    # Fetch data
    data = fetch_log_overview(dashboard, ORGANIZATION_ID, productType, selected_events)

    # Display data
    put_datatable(data["org_data"])
    put_datatable(data["net_data"])


def select_product_type(dashboard, organization_id, product_types_logs):
    with put_loading():
        put_text("Fetching data, please wait...")
        # Fetch networks and their event types
        networks = dashboard.organizations.getOrganizationNetworks(
            organization_id, total_pages="all"
        )

        # Initialize a set to store unique product types
        unique_product_types = set()

        for network in networks:
            # Iterate over each product type in the network
            for productType in network["productTypes"]:
                # Check if the product type is in the product_types_logs
                if productType in product_types_logs:
                    # Add to the set to ensure uniqueness
                    unique_product_types.add(productType)

    # Convert set to list for radio options
    options = list(unique_product_types)

    # Display radio button selection
    selected_product_type = radio(
        label="Select a product type:", options=options, required=True
    )

    return selected_product_type


def fetch_log_type(dashboard, organization_id, productType, logs_events_selected):
    with put_loading():
        put_text("Fetching data, please wait...")
        # Fetch networks and their event types
        networks = dashboard.organizations.getOrganizationNetworks(
            organization_id, total_pages="all"
        )
        all_event_types = set()
        for network in networks:
            productType = productType
            event_types = dashboard.networks.getNetworkEventsEventTypes(network["id"])
            all_event_types.update(
                (e["category"], e["type"], e["description"])
                for e in event_types
                if productType in network["productTypes"]
            )

        # Sort and organize the event types
        sorted_event_types = sorted(
            all_event_types, key=lambda x: (x[0], x[1])
        )  # Sort by category, then type

        # Prepare options for checkboxes
        options = [
            {"label": f"{cat} - {desc}", "value": typ}
            for cat, typ, desc in sorted_event_types
        ]
        checked_values = [
            typ for _, typ, _ in sorted_event_types if typ in logs_events_selected
        ]

        # Display the checkboxes for event selection
    selected_values = input_group(
        "Select Events",
        [
            actions(
                name="top_buttons",
                buttons=[
                    {"label": "Submit", "value": "submit", "color": "primary"},
                    {"label": "Reset", "type": "reset", "color": "warning"},
                ],
            ),
            checkbox(options=options, value=checked_values, name="events"),
        ],
    )

    # Collect selected types
    return selected_values.get("events", [])


def fetch_log_overview(dashboard, organization_id, productType, includedEventTypes):
    with put_loading():
        put_text("Fetching data, please wait...")
        # Retrieve all networks in the organization
        networks = dashboard.organizations.getOrganizationNetworks(
            organization_id, total_pages="all"
        )

        # Create a dictionary to map network ID to network name
        network_id_to_name = {network["id"]: network["name"] for network in networks}

        event_list = []
        for network in networks:
            if productType in network["productTypes"]:
                response = dashboard.networks.getNetworkEvents(
                    network["id"],
                    productType=productType,
                    includedEventTypes=includedEventTypes,
                )

                for event in response["events"]:
                    # Creating the filtered dictionary
                    filtered_event = {
                        "networkId": event["networkId"],
                        "type": event["type"],
                        "description": event["description"],
                    }
                    event_list.append(filtered_event)

        # Counting occurrences based on description
        description_counter = Counter(event["description"] for event in event_list)

        # Counting occurrences based on description and networkId
        network_description_counter = Counter(
            (event["networkId"], event["description"]) for event in event_list
        )

        # Prepare data for the description-based table
        description_data = [
            {"Description": desc, "Count": count}
            for desc, count in description_counter.items()
        ]

        # Prepare data for the network description-based table with network name
        network_description_data = [
            {
                "Network ID": net_desc[0],
                "Network Name": network_id_to_name.get(
                    net_desc[0], "Unknown"
                ),  # Retrieve network name
                "Description": net_desc[1],
                "Count": count,
            }
            for net_desc, count in network_description_counter.items()
        ]
    return {"org_data": description_data, "net_data": network_description_data}


def main():
    """Main function for standalone execution"""
    # Set configuration for PyWebIO
    config(css_style=css_style)
    # Start the server with the mx_logs_overview function
    start_server(lambda: logs_overview(), port=8999, debug=True)


if __name__ == "__main__":
    main()
