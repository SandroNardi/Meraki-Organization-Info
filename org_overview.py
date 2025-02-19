from pywebio.input import *  # For input elements like DATE
from pywebio.output import *  # For output elements like put_text, put_buttons
from pywebio import start_server, config
from datetime import datetime, timedelta
import os
from pyecharts.charts import Bar, Pie
from pyecharts import options as opts
import meraki
from collections import Counter, defaultdict

# Retrieve API key from environment variable
API_KEY = os.getenv("MK_TEST_API")
organization_id = os.getenv("MK_ORG_ID")
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)


def page_init(text, target, title):
    clear()
    put_buttons([text], onclick=[target])
    put_markdown(f"## {title}")


def net_overview():
    """Render header"""
    page_init("Back to Menu", main, "Networks Overview")
    """Fetch data"""
    data = fetch_net_overview(dashboard, organization_id)
    """Display data"""
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


def mx_sec_status():
    """Render header"""
    page_init("Back to Menu", main, "MX Security Overview")

    """Fetch data"""
    data = fetch_mx_sec_status(dashboard, organization_id)

    """Display data"""
    put_datatable(
        data,
        actions=[
            (
                "View Firewall Rules",
                lambda row_id: firewall_rules(
                    dashboard,
                    data[row_id]["general"]["networkId"],
                    data[row_id]["general"]["serial"],
                ),
            )
        ],
    )


def fetch_mx_sec_status(dashboard, organization_id):
    with put_loading():
        put_text("Fetching data, please wait...")

        # Fetch networks and uplinks
        networks = dashboard.organizations.getOrganizationNetworks(
            organization_id, total_pages="all"
        )
        org_uplinks = dashboard.appliance.getOrganizationApplianceUplinkStatuses(
            organization_id, total_pages="all"
        )

        data = []
        for net in networks:
            if "appliance" not in net["productTypes"]:
                continue

            network_id = net["id"]
            mx_uplinks = next(
                (x for x in org_uplinks if x["networkId"] == network_id), "none"
            )

            if mx_uplinks == "none" or mx_uplinks.get("model") == "CPSC-HUB":
                continue

            # Retrieve firewall rules count
            fw_rules = dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(
                network_id
            )
            fw_rules_count = len(fw_rules["rules"])

            # Retrieve IDS and AMP data
            ids = dashboard.appliance.getNetworkApplianceSecurityIntrusion(network_id)
            amp = dashboard.appliance.getNetworkApplianceSecurityMalware(network_id)

            # Retrieve content filtering data
            content_filtering = dashboard.appliance.getNetworkApplianceContentFiltering(
                network_id
            )
            allowed_url_count = len(content_filtering.get("allowedUrlPatterns", []))
            blocked_url_count = len(content_filtering.get("blockedUrlPatterns", []))
            blocked_categories_count = len(
                content_filtering.get("blockedUrlCategories", [])
            )

            # Compile data for each network
            row = {
                "general": {
                    "networkId": mx_uplinks["networkId"],
                    "serial": mx_uplinks["serial"],
                    "model": mx_uplinks["model"],
                    "lastReportedAt": mx_uplinks["lastReportedAt"],
                    "firewallRulesCount": fw_rules_count,
                },
                "highAvailability": mx_uplinks["highAvailability"],
                "uplinks": {},
                "security": {
                    "IDS": (
                        ids["mode"] if ids["mode"] == "disabled" else ids["idsRulesets"]
                    ),
                    "AMP": amp["mode"],
                },
                "URL Filtering": {
                    "Allowed URLs": allowed_url_count,
                    "Blocked URLs": blocked_url_count,
                    "Blocked Categories": blocked_categories_count,
                },
            }

            # Add uplinks information
            for uplink in mx_uplinks.get("uplinks", []):
                interface = uplink["interface"]
                status = uplink["status"]
                status_with_emoji = (
                    f"\U0001F7E2 {status}"
                    if status == "active"
                    else f"\U0001F534 {status}"
                )
                row["uplinks"][interface] = status_with_emoji

            data.append(row)
    return data


def firewall_rules(dashboard, network_id, serial):
    """Fetch firewall rules for a specific network."""
    data = fetch_firewall_rules(dashboard, network_id)
    """Displays firewall rules for a specific network."""
    put_scope(network_id)
    close_btn = put_buttons(["Close"], onclick=[lambda: remove(network_id)])
    put_row(
        [put_text(f"Firewall Rules for Serial: {serial}"), close_btn],
        scope=network_id,
    )
    put_datatable(data, height=300, scope=network_id)


def fetch_firewall_rules(dashboard, network_id):
    with put_loading():
        fw_rules = dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(
            network_id
        )
    return fw_rules["rules"]


def api_usage():
    """Displays API usage statistics in various charts."""
    page_init("Back to Menu", main, "API Usage Overview")

    """Data ranges input"""
    date_range = date_range_input()

    page_init("Back to Menu", main, "API Usage Overview")

    data = fetch_api_statistics(dashboard, organization_id, date_range)

    display_api_usage_pie_chart(data["api_overview"])
    display_api_usage_stacked_bar_chart(data["api_details"])
    display_method_usage_stacked_bar_chart(data["api_details"])
    display_admin_response_code_table(data["api_details"], data["admins_info"])


def fetch_api_statistics(dashboard, organization_id, date_range):
    with put_loading():
        put_text("Fetching data, please wait...")
        api_overview = dashboard.organizations.getOrganizationApiRequestsOverview(
            organization_id, t0=date_range["t0"], t1=date_range["t1"]
        )
        api_details = dashboard.organizations.getOrganizationApiRequests(
            organization_id, t0=date_range["t0"], t1=date_range["t1"], total_pages="all"
        )
        admins_info = dashboard.organizations.getOrganizationAdmins(organization_id)
    return {
        "api_overview": api_overview,
        "api_details": api_details,
        "admins_info": admins_info,
    }


def date_range_input():
    put_markdown("##### The time range is defaulted to the last 30 days")
    # Prompt for date range
    t0_str = input(
        "Enter the start date (YYYY-MM-DD):",
        type=DATE,
        value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
    )
    t1_str = input(
        "Enter the end date (YYYY-MM-DD):",
        type=DATE,
        value=datetime.now().strftime("%Y-%m-%d"),
    )

    # Convert date strings to Unix timestamps
    t0 = int(
        datetime.strptime(t0_str, "%Y-%m-%d")
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )
    t1 = int(
        datetime.strptime(t1_str, "%Y-%m-%d")
        .replace(hour=23, minute=59, second=59, microsecond=999999)
        .timestamp()
    )
    clear()
    return {"t0": t0, "t1": t1}


def display_api_usage_pie_chart(data):
    """Renders a pie chart for API usage data."""
    if "responseCodeCounts" in data:
        response_code_counts = data["responseCodeCounts"]
        filtered_data = {
            code: count for code, count in response_code_counts.items() if count > 0
        }

        categories = list(filtered_data.keys())
        values = list(filtered_data.values())

        pie = (
            Pie()
            .add("", [list(z) for z in zip(categories, values)])
            .set_global_opts(title_opts=opts.TitleOpts(title="API Usage Overview"))
        )
        put_html(pie.render_notebook())
    else:
        put_error("No API usage data available.")


def display_api_usage_stacked_bar_chart(data):
    """Renders a stacked bar chart for API usage data based on response codes."""
    dates = sorted(set(entry["ts"][:10] for entry in data))
    response_codes = sorted(set(entry["responseCode"] for entry in data))

    counts = {date: {code: 0 for code in response_codes} for date in dates}

    for entry in data:
        date = entry["ts"][:10]
        code = entry["responseCode"]
        counts[date][code] += 1

    x_data = dates
    y_data = {code: [counts[date][code] for date in dates] for code in response_codes}

    bar = Bar()
    bar.add_xaxis(x_data)
    for code, values in y_data.items():
        bar.add_yaxis(str(code), values, stack="stack1")
    bar.set_global_opts(title_opts=opts.TitleOpts(title="API Usage over time"))

    put_html(bar.render_notebook())


def display_method_usage_stacked_bar_chart(data):
    """Renders a stacked bar chart for HTTP method usage."""
    dates = sorted(set(entry["ts"][:10] for entry in data))
    methods = sorted(set(entry["method"] for entry in data))

    counts = {date: {method: 0 for method in methods} for date in dates}

    for entry in data:
        date = entry["ts"][:10]
        method = entry["method"]
        counts[date][method] += 1

    x_data = dates
    y_data = {method: [counts[date][method] for date in dates] for method in methods}

    bar = Bar()
    bar.add_xaxis(x_data)
    for method, values in y_data.items():
        bar.add_yaxis(method, values, stack="stack1")
    bar.set_global_opts(title_opts=opts.TitleOpts(title="HTTP Method Usage over time"))

    put_html(bar.render_notebook())


def display_admin_response_code_table(data, admins_info):
    """Displays a table with admin response code occurrences."""
    admin_details = {
        admin["id"]: {"name": admin["name"], "email": admin["email"]}
        for admin in admins_info
    }

    admin_response_counts = defaultdict(lambda: defaultdict(int))

    for entry in data:
        admin_id = entry["adminId"]
        response_code = entry["responseCode"]
        admin_response_counts[admin_id][response_code] += 1

    response_codes = sorted(set(entry["responseCode"] for entry in data))
    table_data = []
    for admin_id, responses in admin_response_counts.items():
        admin_info = admin_details.get(
            admin_id, {"name": "Unknown", "email": "Unknown"}
        )

        row = {
            "Admin ID": admin_id,
            "Name": admin_info["name"],
            "Email": admin_info["email"],
        }
        row.update({f"Code {code}": responses.get(code, 0) for code in response_codes})
        table_data.append(row)

    put_text("Admins breakdown")
    put_datatable(table_data)


def firmware_status():
    page_init("Back to Menu", main, "Firmware overview")
    data = fetch_firmware_status(dashboard, organization_id)
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
                f"\U0001F7E2 {status}" if status == "online" else f"\U0001F534 {status}"
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


# Set configuration for PyWebIO
config(css_style="#output-container{max-width: none;}")


def main():
    """Main menu function for the application."""
    clear()
    put_markdown("# Meraki Dashboard")

    # Define menu buttons
    put_buttons(["Networks Overview"], onclick=[net_overview])
    put_buttons(["MX Sec Overview"], onclick=[mx_sec_status])
    put_buttons(["API Usage"], onclick=[api_usage])
    put_buttons(["Firmware status"], onclick=[firmware_status])


# Start the PyWebIO server
if __name__ == "__main__":
    start_server(main, port=8999, debug=True)
