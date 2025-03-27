import redfish
import pandas as pd
import json
import csv
import socket

# File Paths
SERVER_LIST = "servers.csv"
CREDENTIALS_FILE = "credentials.json"
OUTPUT_CSV = "dell_servers_health.csv"

def load_credentials(file_path):
    """Load credentials from JSON file."""
    with open(file_path, "r") as file:
        return json.load(file)

def resolve_hostname(hostname):
    """Resolve hostname to IP address."""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None

def fetch_redfish_data(client, uri):
    """Helper function to fetch Redfish data with error handling."""
    try:
        response = client.get(uri)
        return response.dict if response.status == 200 else None
    except Exception:
        return None

def get_server_health(hostname, username, password):
    """Fetch health status of a single Dell server."""
    ip = resolve_hostname(hostname)
    if not ip:
        return [[hostname, "Error", "Hostname resolution failed", "-", "-", "-"]]

    base_url = f"https://{ip}"
    data_list = []

    try:
        # Establish Redfish session
        client = redfish.redfish_client(base_url=base_url, username=username, password=password)
        client.login()

        # Fetch system health
        system_data = fetch_redfish_data(client, "/redfish/v1/Systems/System.Embedded.1")
        if system_data:
            data_list.append([hostname, "System", "Overall", system_data.get("Status", {}).get("Health", "Unknown"),
                              system_data.get("Status", {}).get("State", "Unknown"), system_data.get("PowerState", "Unknown")])

        # Fetch thermal (fan) health
        thermal_data = fetch_redfish_data(client, "/redfish/v1/Chassis/1/Thermal")
        if thermal_data:
            for fan in thermal_data.get("Fans", []):
                data_list.append([hostname, "Thermal", fan.get("Name", "Unknown"), fan.get("Status", {}).get("Health", "Unknown"), "-", "-"])

        # Fetch power supply health
        power_data = fetch_redfish_data(client, "/redfish/v1/Chassis/1/Power")
        if power_data:
            for psu in power_data.get("PowerSupplies", []):
                data_list.append([hostname, "Power", psu.get("Name", "Unknown"), psu.get("Status", {}).get("Health", "Unknown"), "-", "-"])

        # Logout session
        client.logout()

    except Exception as e:
        data_list.append([hostname, "Error", str(e), "-", "-", "-"])

    return data_list

def process_servers(server_file, credentials_file, output_file):
    """Read servers from CSV, fetch health data, and save to CSV."""
    credentials = load_credentials(credentials_file)
    username, password = credentials["username"], credentials["password"]
    all_data = []

    with open(server_file, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            hostname = row["Hostname"]
            all_data.extend(get_server_health(hostname, username, password))

    # Save to CSV
    df = pd.DataFrame(all_data, columns=["Hostname", "Category", "Component", "Health", "State", "Power State"])
    df.to_csv(output_file, index=False)
    print(f"Health data saved to {output_file}")

# Run the script
process_servers(SERVER_LIST, CREDENTIALS_FILE, OUTPUT_CSV)
