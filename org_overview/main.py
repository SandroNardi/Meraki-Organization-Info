from pywebio import start_server, config
from pywebio.output import put_markdown, clear, put_buttons
from admin_overview import admin_overview
from net_overview import net_overview
from logs_overview import mx_logs_overview
from mx_sec_status import mx_sec_status
from api_usage import api_usage
from firmware_status import firmware_status


# Set configuration for PyWebIO
config(css_style="#output-container{max-width: none;}")


def main():
    """Main menu function for the application."""
    clear()
    put_markdown("# Meraki Dashboard")

    # Define menu buttons
    put_buttons(["Admins Overview"], onclick=[lambda: admin_overview(main)])
    put_buttons(["Networks Overview"], onclick=[lambda: net_overview(main)])
    put_buttons(["Logs Overview"], onclick=[lambda: mx_logs_overview(main)])
    put_buttons(["MX Sec Overview"], onclick=[lambda: mx_sec_status(main)])
    put_buttons(["API Usage"], onclick=[lambda: api_usage(main)])
    put_buttons(["Firmware status"], onclick=[lambda: firmware_status(main)])


if __name__ == "__main__":
    start_server(lambda: main(), port=8999, debug=True)
