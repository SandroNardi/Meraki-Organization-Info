from pywebio import start_server, config
from pywebio.output import *
from pywebio import start_server
from utils import page_init
from navigation import navigate_to_main
from config import *
import json
import requests

page_title = "MX Security Overview"


def mx_sec_status(main_func=None):
    """Render header"""
    if main_func:
        page_init(back_to_main_text, page_title, lambda: navigate_to_main(main_func))
    else:
        page_init(back_to_main_text, page_title)

    # Fetch data
    data = fetch_mx_sec_status(dashboard, ORGANIZATION_ID)

    # Display data
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
        xdr_status = get_org_xdr_status()
        print(xdr_status)
        data = []
        for net in networks:
            if "appliance" not in net["productTypes"]:
                continue

            network_id = net["id"]
            network_name = net["name"]  # Retrieve network name

            # Use a list comprehension to get all uplinks for the network_id
            mx_uplinks_list = [x for x in org_uplinks if x["networkId"] == network_id]

            # If no uplinks found or if all models are CPSC-HUB, skip
            if not mx_uplinks_list or all(
                uplink.get("model") == "CPSC-HUB" for uplink in mx_uplinks_list
            ):
                continue

            # Process each uplink
            for mx_uplinks in mx_uplinks_list:
                # Compile data for each uplink in the network
                row = {
                    "general": {
                        "networkId": mx_uplinks["networkId"],
                        "name": network_name,  # Include network name
                        "serial": mx_uplinks["serial"],
                        "model": mx_uplinks["model"],
                        "lastReportedAt": mx_uplinks["lastReportedAt"],
                        "firewallRulesCount": "-",
                    },
                    "highAvailability": mx_uplinks["highAvailability"],
                    "uplinks": {},
                    "security": {
                        "IDS": "unavailable",
                        "AMP": "unavailable",
                    },
                    "URL Filtering": {
                        "Allowed URLs": "-",
                        "Blocked URLs": "-",
                        "Blocked Categories": "-",
                    },
                }

                # Add uplinks information
                for uplink in mx_uplinks.get("uplinks", []):
                    interface = uplink["interface"]
                    status = uplink["status"]

                    if status == "active" or status == "ready":
                        status_with_emoji = f"\U0001f7e2 {status}"
                    else:
                        status_with_emoji = f"\U0001f534 {status}"

                    row["uplinks"][interface] = status_with_emoji

                # Check if highAvailability role is "spare"
                if mx_uplinks["highAvailability"]["role"] == "spare":
                    row["security"] = {
                        "IDS": "spare",
                        "AMP": "spare",
                    }
                    row["URL Filtering"] = {
                        "Allowed URLs": "spare",
                        "Blocked URLs": "spare",
                        "Blocked Categories": "spare",
                    }
                    data.append(row)
                    continue

                # Retrieve firewall rules count
                fw_rules = (
                    dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(
                        network_id
                    )
                )
                fw_rules_count = len(fw_rules["rules"])
                row["general"]["firewallRulesCount"] = fw_rules_count

                security_fetch_error = False
                try:
                    # Retrieve IDS and AMP data
                    ids = dashboard.appliance.getNetworkApplianceSecurityIntrusion(
                        network_id
                    )
                    amp = dashboard.appliance.getNetworkApplianceSecurityMalware(
                        network_id
                    )
                    # Retrieve content filtering data
                    content_filtering = (
                        dashboard.appliance.getNetworkApplianceContentFiltering(
                            network_id
                        )
                    )
                    allowed_url_count = len(
                        content_filtering.get("allowedUrlPatterns", [])
                    )
                    blocked_url_count = len(
                        content_filtering.get("blockedUrlPatterns", [])
                    )
                    blocked_categories_count = len(
                        content_filtering.get("blockedUrlCategories", [])
                    )

                except:
                    security_fetch_error = True

                # Modify based on security_fetch_error being False
                if not security_fetch_error:
                    # Update "security" section
                    row["security"] = {
                        "IDS": (
                            (
                                ids["mode"]
                                if ids["mode"] == "disabled"
                                else f"{ids['mode']} - {ids['idsRulesets']}"
                            ),
                        ),
                        "AMP": amp["mode"],
                    }
                    # Update "URL Filtering" section
                    row["URL Filtering"] = {
                        "Allowed URLs": allowed_url_count,
                        "Blocked URLs": blocked_url_count,
                        "Blocked Categories": blocked_categories_count,
                    }

                data.append(row)
    return data


def get_org_xdr_status():
    url = (
        "https://api.meraki.com/api/v1/organizations/"
        + ORGANIZATION_ID
        + "/integrations/xdr/networks"
    )

    payload = None
    authB = "Bearer " + API_KEY

    headers = {
        "Authorization": authB,
        "Accept": "application/json",
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text.encode("utf8"))
    return json.loads(response.text.encode("utf8"))


def firewall_rules(dashboard, network_id, serial):
    """Fetch and display firewall rules for a specific network."""
    data = fetch_firewall_rules(dashboard, network_id)
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


def main():
    """Main function for standalone execution"""
    # Set configuration for PyWebIO
    config(css_style=css_style)
    # Start the server with the mx_sec_status function
    start_server(lambda: mx_sec_status(), port=8999, debug=True)


if __name__ == "__main__":
    main()
