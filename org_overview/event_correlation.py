from pywebio.output import put_text, put_loading, put_datatable
from pywebio import start_server
from utils import page_init
from navigation import navigate_to_main
from config import dashboard, ORGANIZATION_ID
from datetime import datetime, timedelta
import pytz

page_title = "Ms Reboot Reason"
back_to_main_text = "Back to Main"

# Constants and configuration from previous script
FS = "---"
MAX_LEN = 100
alerts_type_of_devices = ["MS", "MX", "MR"]
alerts_type_of_alerts = []
orgAlertDaysDeltaTimes = 20
log_excluded_event_types = []
delta_times_minutes = {
    "changelogStart": 10,
    "changelogStop": 10,
    "deviceLogStart": 5,
    "deviceLogStop": 5,
    "deviceStatusNext": 5,
}
inTable = {"changeLog": True, "eventLog": True, "orgAlert": True, "deviceStatus": True}

log_device_type_mapping = {
    "Z": "appliance",
    "MX": "appliance",
    "VMX": "appliance",
    "MS": "switch",
    "Catalyst Switch": "switch",
    "Catalyst AP": "wireless",
    "MR": "wireless",
}

event_names = {
    "change": "Change Log",
    "event": "Event Log",
    "orgAlert": "Org Alert",
    "status": "Device Status",
}


def alert_correlation(main_func=None):
    """Render header and fetch data"""
    if main_func:
        page_init(back_to_main_text, page_title, lambda: navigate_to_main(main_func))
    else:
        page_init(back_to_main_text, page_title)

    data = fetch_function(dashboard, ORGANIZATION_ID)

    if not data:
        put_text("No data available to display.")
    else:
        column_order = ["Time", "Source", "Device", "Category", "Description", "Info"]
        put_datatable(data, column_order=column_order)


def fetch_function(dashboard, organization_id):
    with put_loading():
        put_text("Fetching data, please wait...")

        alert_tsStart = (
            datetime.now(pytz.timezone("UTC")) - timedelta(days=orgAlertDaysDeltaTimes)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        data = []

        function_args = {
            "total_pages": "all",
            "resolved": True,
            "active": False,
            "tsStart": alert_tsStart,
        }

        if alerts_type_of_alerts:
            function_args["types"] = alerts_type_of_alerts

        alerts = dashboard.organizations.getOrganizationAssuranceAlerts(
            organization_id, **function_args
        )

        for alert in alerts:
            if alert["deviceType"] not in alerts_type_of_devices:
                continue
            row = {
                "Time": alert["deviceType"],
                "Source": FS,
                "Device": FS,
                "Category": FS,
                "Description": FS,
                "Info": FS,
            }
            data.append(row)
            alert_data = []
            for device in alert["scope"]["devices"]:
                dt_eventStart = datetime.strptime(
                    alert["startedAt"], "%Y-%m-%dT%H:%M:%SZ"
                )
                dt_eventResolved = datetime.strptime(
                    alert["resolvedAt"], "%Y-%m-%dT%H:%M:%SZ"
                )

                # Add alert start and stop to data
                alert_data.append(
                    {
                        "Time": dt_eventStart.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        "Source": event_names["orgAlert"],
                        "Device": device["name"],
                        "Category": alert["type"],
                        "Description": ">>> STARTED",
                        "Info": FS,
                    }
                )

                alert_data.append(
                    {
                        "Time": dt_eventResolved.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                        "Source": event_names["orgAlert"],
                        "Device": device["name"],
                        "Category": alert["type"],
                        "Description": "<<< STOPPED",
                        "Info": FS,
                    }
                )

                # Fetch device status changes
                if inTable["deviceStatus"]:
                    logAfterString = (
                        dt_eventResolved
                        + timedelta(minutes=delta_times_minutes["deviceLogStop"])
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")

                    statusChanges = dashboard.organizations.getOrganizationDevicesAvailabilitiesChangeHistory(
                        organization_id,
                        total_pages="all",
                        t0=alert["startedAt"],
                        t1=logAfterString,
                        serials=device["serial"],
                    )

                    for stat in statusChanges:
                        row = {
                            "Time": stat["ts"],
                            "Source": event_names["status"],
                            "Device": stat["device"]["name"],
                            "Category": stat["details"]["new"][0]["value"],
                            "Description": (
                                stat["details"]["new"][1]["value"]
                                if len(stat["details"]["new"]) > 1
                                else FS
                            ),
                            "Info": FS,
                        }
                        alert_data.append(row)

                # Fetch admin changes
                if inTable["changeLog"]:
                    changeT0 = (
                        dt_eventStart
                        - timedelta(minutes=delta_times_minutes["changelogStart"])
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")

                    changeT1 = (
                        dt_eventStart
                        + timedelta(minutes=delta_times_minutes["changelogStop"])
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")

                    changes = (
                        dashboard.organizations.getOrganizationConfigurationChanges(
                            organization_id,
                            total_pages=3,
                            networkId=alert["network"]["id"],
                            t0=changeT0,
                            t1=changeT1,
                        )
                    )

                    for change in changes:
                        row = {
                            "Time": change["ts"],
                            "Source": event_names["change"],
                            "Device": change["adminName"],
                            "Category": change["page"],
                            "Description": change["label"],
                            "Info": str(change["newValue"])[:MAX_LEN],
                        }
                        alert_data.append(row)

                # Fetch device logs
                if inTable["eventLog"]:
                    logDeltaBeforeStr = (
                        dt_eventStart
                        - timedelta(minutes=delta_times_minutes["deviceLogStart"])
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")

                    logDeltaAfterStr = (
                        dt_eventResolved
                        + timedelta(minutes=delta_times_minutes["deviceLogStop"])
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")

                    events = dashboard.networks.getNetworkEvents(
                        alert["network"]["id"],
                        perPage=500,
                        deviceSerial=device["serial"],
                        productType=log_device_type_mapping[alert["deviceType"]],
                        excludedEventTypes=log_excluded_event_types,
                    )

                    for event in events["events"]:
                        event_time = datetime.strptime(
                            event["occurredAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
                        )
                        if event_time < datetime.strptime(
                            logDeltaBeforeStr, "%Y-%m-%dT%H:%M:%SZ"
                        ):
                            continue
                        if event_time > datetime.strptime(
                            logDeltaAfterStr, "%Y-%m-%dT%H:%M:%SZ"
                        ):
                            continue

                        client = (
                            event.get("clientDescription")
                            or event.get("clientMac")
                            or event.get("deviceName")
                            or "-"
                        )

                        row = {
                            "Time": event["occurredAt"],
                            "Source": event_names["event"],
                            "Device": client,
                            "Category": event["category"],
                            "Description": event["description"],
                            "Info": str(event["eventData"])[:MAX_LEN],
                        }
                        alert_data.append(row)

            # Sort the alert-related data by time
            alert_data.sort(key=lambda x: x["Time"])

            # Extend the main data list with the sorted alert data
            data.extend(alert_data)

        return data


def main():
    """Main function for standalone execution"""
    start_server(lambda: alert_correlation(), port=8999, debug=True)


if __name__ == "__main__":
    main()
