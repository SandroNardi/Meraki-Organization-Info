from pywebio.output import *
from pywebio.input import input, DATE
from pywebio import start_server
from datetime import datetime, timedelta
from pyecharts.charts import Bar, Pie
from pyecharts import options as opts
from utils import page_init
from navigation import navigate_to_main
from collections import defaultdict
from config import *

page_title = "API Usage Overview"


def api_usage(main_func=None):
    """Render header"""
    if main_func:
        page_init(back_to_main_text, page_title, lambda: navigate_to_main(main_func))
    else:
        page_init(back_to_main_text, page_title)

    """Data ranges input"""
    date_range = date_range_input()

    """Render header"""
    if main_func:
        page_init(back_to_main_text, page_title, lambda: navigate_to_main(main_func))
    else:
        page_init(back_to_main_text, page_title)

    data = fetch_api_statistics(dashboard, ORGANIZATION_ID, date_range)

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


def main():
    """Main function for standalone execution"""
    # Start the server with the api_usage function
    start_server(lambda: api_usage(), port=8999, debug=True)


if __name__ == "__main__":
    main()
