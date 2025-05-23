# config.py
import os
import meraki

# Retrieve API key and organization ID from environment variables
if True:  # Modify this condition based on your configuration needs
    API_KEY = os.getenv("MK_CSM_KEY")
    ORGANIZATION_ID = os.getenv("MK_CSM_ORG")
else:
    API_KEY = os.getenv("MK_TEST_API")
    ORGANIZATION_ID = os.getenv("MK_MAIN_ORG")

# Initialize the Meraki Dashboard API
dashboard = meraki.DashboardAPI(API_KEY, suppress_logging=True)

back_to_main_text = "Back to Menu"


product_types_logs = [
    "appliance",
    "camera",
    "cellularGateway",
    "wirelessController",
    "switch",
    "wireless",
]

# Event types selected for logging
logs_events_selected = {
    "appliance": [
        "vpn_connectivity_change",
        "failover_event",
        "vrrp_state_change",
        "vrrp_vrid_collision",
        "dhcp_problem",
        "nbar_block",
        "cf_block",
        "sf_url_block",
        "8021x_eap_failure",
        "8021x_radius_timeout",
        "8021x_client_timeout",
        "radius_server_attribute_mismatch",
        "radius_mab_timeout",
        "radius_invalid_vlan_name",
    ],
    "wireless": [],
    "switch": [],
}

css_style = "#output-container{max-width: none;}"
