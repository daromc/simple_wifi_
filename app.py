from flask import Flask, jsonify, render_template
import requests
import subprocess
import re

app = Flask(__name__)

def get_location():
    """Get the geographic location (latitude and longitude) based on IP address."""
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        location = data.get('loc', 'Location not found').split(',')
        latitude = location[0]
        longitude = location[1]
        return latitude, longitude
    except Exception as e:
        return str(e), str(e)

def get_connected_wifi_info():
    """Retrieve information about the currently connected WiFi network."""
    try:
        result = subprocess.check_output(["netsh", "wlan", "show", "interfaces"]).decode("utf-8")
        connected_info = {}

        connected_info["SSID"] = re.search(r"SSID\s*:\s*(.+)", result).group(1)
        connected_info["MAC Address"] = re.search(r"BSSID\s*:\s*([0-9A-Fa-f:]+)", result).group(1)
        connected_info["Band"] = re.search(r"Radio type\s*:\s*(.+)", result).group(1)
        connected_info["Channel"] = re.search(r"Channel\s*:\s*(\d+)", result).group(1)
        connected_info["Receive Rate (Mbps)"] = re.search(r"Receive rate \(Mbps\)\s*:\s*(\d+)", result).group(1)
        connected_info["Transmit Rate (Mbps)"] = re.search(r"Transmit rate \(Mbps\)\s*:\s*(\d+)", result).group(1)

        ip_address = re.search(r"IPv4 Address\s*:\s*([\d.]+)", result)
        if ip_address:
            connected_info["IP Address"] = ip_address.group(1)

        signal_percentage = re.search(r"Signal\s*:\s*(\d+)%", result)
        if signal_percentage:
            connected_info["Signal (dBm)"] = int(signal_percentage.group(1)) - 100  # Approximation for dBm

        return connected_info

    except subprocess.CalledProcessError:
        return None


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/rssi", methods=["GET"])
def rssi():
    """Return the RSSI value."""
    try:
        connected_info = get_connected_wifi_info()
        if connected_info and "Signal (dBm)" in connected_info:
            return jsonify({"rssi": connected_info["Signal (dBm)"]})
        else:
            return jsonify({"error": "Unable to retrieve RSSI value."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/wifi_info", methods=["GET"])
def wifi_info():
    """Return the connected WiFi info along with location."""
    try:
        latitude, longitude = get_location()
        connected_info = get_connected_wifi_info()

        if connected_info:
            return jsonify({
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "wifi_info": connected_info
            })
        else:
            return jsonify({"error": "Unable to retrieve WiFi information."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
