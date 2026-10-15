from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Simulated Sealer Drum Database (Steps 6 & 7: Inventory & FEFO)[cite: 1]
drum_database = [
    {"drum_id": "D001", "lot_no": "L123", "expiry_date": "12-2026", "qty": "200 L", "status": "In Storage"},[cite: 1]
    {"drum_id": "D002", "lot_no": "L124", "expiry_date": "01-2027", "qty": "200 L", "status": "Next (FEFO)"},[cite: 1]
    {"drum_id": "D003", "lot_no": "L125", "expiry_date": "03-2027", "qty": "200 L", "status": "In Storage"}[cite: 1]
]

# HTML Template embedded directly for a single-file deployment
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sealer Drum Flow - Digital Twin Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.js"></script>
</head>
<body class="bg-gray-100 font-sans">
    <div class="container mx-auto p-6">
        <!-- Header -->
        <header class="bg-blue-900 text-white p-4 rounded-lg shadow-md mb-6 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-bold">Sealer Drum Flow & Storage Area</h1>
                <p class="text-sm text-blue-200">Plant Process & Digital Twin Simulation (Arrival to Line Issue)[cite: 1]</p>
            </div>
            <span class="bg-green-500 px-3 py-1 rounded text-sm font-semibold">Python/Flask Active</span>
        </header>

        <!-- Metrics Grid -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div class="bg-white p-4 rounded-lg shadow">
                <h3 class="text-gray-500 text-sm">Active Drums in Storage</h3>
                <p id="metric-storage" class="text-3xl font-bold text-blue-900">3</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
                <h3 class="text-gray-500 text-sm">Active Line Consumption</h3>
                <p id="metric-consumption" class="text-3xl font-bold text-green-600">182 L</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
                <h3 class="text-gray-500 text-sm">Active Logic Rule</h3>
                <p class="text-lg font-semibold text-purple-700">FEFO (First Expiring First Out)[cite: 1]</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
                <h3 class="text-gray-500 text-sm">System Alerts</h3>
                <p class="text-xl font-bold text-green-600">None[cite: 1]</p>
            </div>
        </div>

        <!-- Inventory Table (Step 6 & 7) -->
        <div class="bg-white p-6 rounded-lg shadow mb-6">
            <h2 class="text-lg font-bold mb-4 text-gray-800">Inventory Monitoring & FIFO/FEFO Queue[cite: 1]</h2>
            <table class="w-full text-left border-collapse">
                <thead>
                    <tr class="bg-gray-200 text-gray-700">
                        <th class="p-2">Drum ID</th>
                        <th class="p-2">Lot No.</th>
                        <th class="p-2">Expiry Date</th>
                        <th class="p-2">Quantity</th>
                        <th class="p-2">Status</th>
                    </tr>
                </thead>
                <tbody id="inventory-table">
                    {% for drum in drums %}
                    <tr class="border-b">
                        <td class="p-2 font-medium">{{ drum.drum_id }}</td>
                        <td class="p-2">{{ drum.lot_no }}</td>
                        <td class="p-2">{{ drum.expiry_date }}</td>
                        <td class="p-2">{{ drum.qty }}</td>
                        <td class="p-2 font-semibold {% if 'Next' in drum.status %}text-purple-600{% else %}text-blue-600{% endif %}">
                            {{ drum.status }}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Process Flow Reference Steps -->
        <div class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-lg">
            <h3 class="font-bold text-blue-900 mb-1">Process Overview</h3>
            <p class="text-sm text-blue-800">
                Covers all stages from Plant Arrival (Step 1) -> Quality Check & SAP GRN (Steps 2-3) -> Storage & Tagging (Steps 4-5) -> Real-time Monitoring & FEFO Issue (Steps 6-8) -> Line-Side Consumption via Load Cells (Step 9) to Empty Return (Steps 10-11)[cite: 1].
            </p>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, drums=drum_database)

@app.route("/api/status")
def api_status():
    return jsonify({
        "status": "online",
        "inventory": drum_database,
        "active_rule": "FEFO",[cite: 1]
        "alerts": 0[cite: 1]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
