from pywebio.output import *
from pywebio import start_server
from utils import page_init
from navigation import navigate_to_main
from config import *

page_title = "Firmware Overview"


def firmware_status(main_func=None):
    """Render header"""
    if main_func:
        page_init(back_to_main_text, page_title, lambda: navigate_to_main(main_func))
    else:
        page_init(back_to_main_text, page_title)

    data = fetch_firmware_status(dashboard, ORGANIZATION_ID)
    put_datatable(data)


def fetch_firmware_status(dashboard, organization_id):
    with put_loading():
        put_text("Fetching data, please wait...")

        # Get devices
        devices = dashboard.organizations.getOrganizationDevices(
            organization_id, total_pages="all"
        )

        # Get devices availabilities
        devices_availabilities = (
            dashboard.organizations.getOrganizationDevicesAvailabilities(
                organization_id, total_pages="all"
            )
        )

        # Get networks
        networks = dashboard.organizations.getOrganizationNetworks(
            organization_id, total_pages="all"
        )

        # Create a mapping of network ID to network name
        network_id_to_name = {network["id"]: network["name"] for network in networks}

        # Initialize data list
        data = []

        # For each device
        for device in devices:
            # Find the availability
            availability_list = [
                d for d in devices_availabilities if d["serial"] == device["serial"]
            ]

            # Default status values
            status = "offline"
            firmware_status = "ok"

            # Determine the firmware status
            if device["firmware"] == "Not running configured version":
                firmware_status = "mismatch"
            elif device["firmware"] == "Firmware locked. Please contact support.":
                firmware_status = "locked"

            # Determine the device status
            if availability_list and availability_list[0]["status"] == "online":
                status = "online"

            # Add emoji to the status
            status_with_emoji = (
                f"\U0001f7e2 {status}" if status == "online" else f"\U0001f534 {status}"
            )

            # Get network name using networkId
            network_name = network_id_to_name.get(
                device.get("networkId", ""), "Unknown"
            )

            # Compile data for each device
            row = {
                "general": {
                    "deviceName": device.get("name", "Unknown"),
                    "serial": device["serial"],
                    "model": device.get("model", "Unknown"),
                    "networkName": network_name,
                },
                "Status": {
                    "deviceStatus": status_with_emoji,
                },
                "Firmware": {
                    "configuredFirmware": device.get("firmware", "Unknown"),
                    "firmwareStatus": firmware_status,
                },
            }

            # Append the row to data
            data.append(row)
    return data


def main():
    """Main function for standalone execution"""
    # Start the server with the firmware_status function
    start_server(lambda: firmware_status(), port=8999, debug=True)


if __name__ == "__main__":
    main()
