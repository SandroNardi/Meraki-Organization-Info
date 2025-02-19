# Meraki Dashboard Monitoring Tool

This repository contains a Python-based application that utilizes the Meraki Dashboard API to provide insights into network configurations, security status, API usage, and firmware updates. The application employs the PyWebIO library for building a web-based user interface.

## Features

- **Networks Overview**: Displays a summary of networks associated with the specified organization.
- **MX Security Overview**: Provides an overview of security settings for MX appliances, including firewall rules, IDS, AMP, and content filtering.
- **API Usage**: Visualizes API request statistics using pie and bar charts.
- **Firmware Status**: Reports the firmware status of devices within the organization.

## Prerequisites

To run this application, ensure that you have the following:

- Python 3.6 or higher
- `pywebio`, `pyecharts`, and `meraki` Python packages
- A valid Meraki Dashboard API key and organization ID

## Setup

1. Clone the repository:

```bash
git clone https://github.com/your-username/meraki-dashboard-monitoring.git
```

2. Navigate to the project directory:

```bash
cd meraki-dashboard-monitoring
```

3. Install the required packages:

```bash
pip install pywebio pyecharts meraki
```

4. Set up your environment variables:

- MK_TEST_API: Your Meraki Dashboard API key
- MK_ORG_ID: Your organization ID

You can set these in your terminal session:

```bash
export MK_TEST_API='your_api_key' export MK_ORG_ID='your_org_id'
```

## Usage

Run the application using the following command:

```bash
python org_overview.py
```

The PyWebIO server will start, and you can access the application in your web browser at http://localhost:8999.
