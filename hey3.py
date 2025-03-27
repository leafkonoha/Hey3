import requests
import threading
import openpyxl
from openpyxl.styles import PatternFill

# Function to check HP iLO server health
def check_hp_ilo_health(ip, username, password):
    url = f"https://{ip}/redfish/v1/Systems/1"
    try:
        response = requests.get(url, auth=(username, password), verify=False, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("Status", {}).get("Health", "Unknown")
    except Exception as e:
        return f"Error: {str(e)}"

# Function to check Dell Redfish server health
def check_dell_redfish_health(ip, username, password):
    url = f"https://{ip}/redfish/v1/Systems/System.Embedded.1"
    try:
        response = requests.get(url, auth=(username, password), verify=False, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("Status", {}).get("Health", "Unknown")
    except Exception as e:
        return f"Error: {str(e)}"

# Function to determine server type and check health
def check_server_health(ip, username, password, results):
    if ip.lower().startswith("uname"):  # HP servers
        health_status = check_hp_ilo_health(ip, username, password)
    elif ip.lower().startswith("bltwa"):  # Dell servers
        health_status = check_dell_redfish_health(ip, username, password)
    else:
        health_status = "Unknown server type"

    results.append([ip, health_status])

# Function to save results in an Excel file
def save_to_xlsx(results):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Server Health Report"

    # ✅ Headers
    headers = ["Server", "Health Status"]
    ws.append(headers)

    # ✅ Define color fills
    green_fill = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")  # Green for OK
    yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")  # Yellow for Warning
    red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")  # Red for Error

    for row in results:
        ws.append(row)
        cell = ws.cell(row=ws.max_row, column=2)

        # Apply color coding
        if row[1].lower() == "ok":
            cell.fill = green_fill
        elif row[1].lower() == "warning":
            cell.fill = yellow_fill
        elif "error" in row[1].lower():
            cell.fill = red_fill

    # ✅ Save XLSX file
    wb.save("server_health_report.xlsx")
    print("Report saved: server_health_report.xlsx")

# Main function to read server list and check health
def main():
    servers = [
        "uname-server1.example.com",  # HP server
        "bltwa-server2.example.com",  # Dell server
        "random-server3.example.com"  # Unknown type
    ]
    username = "admin"
    password = "password"

    results = []
    threads = []

    for ip in servers:
        thread = threading.Thread(target=check_server_health, args=(ip, username, password, results))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    # Save results to XLSX
    save_to_xlsx(results)

    print("Health check completed. Results saved in server_health_report.xlsx.")

if __name__ == "__main__":
    main()
