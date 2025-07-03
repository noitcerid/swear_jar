import json
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string


# ---------------------------------------------------------------------------- #
#                              ticJar Core Logic                             #
# ---------------------------------------------------------------------------- #
# This class is the same as before, containing all the logic for managing data.
class ticJar:
    """
    Manages the data logic for the tic jar.
    """

    def __init__(self, file_path='tic_jar.json', cost_per_tic=1.0):
        self.file_path = file_path
        self.cost_per_tic = cost_per_tic
        self.data = self._load_data()

    def _load_data(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({}, f)
            return {}
        try:
            with open(self.file_path, 'r') as f:
                content = f.read()
                return json.loads(content) if content else {}
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_data(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    def add_tic(self, user):
        user = user.lower()
        current_month_key = datetime.now().strftime('%Y-%m')
        if user not in self.data:
            self.data[user] = {}
        if current_month_key not in self.data[user]:
            self.data[user][current_month_key] = 0
        self.data[user][current_month_key] += 1
        self._save_data()
        return {"user": user, "message": f"tic added for {user}."}

    def get_user_history(self, user):
        user = user.lower()
        history = {
            "user": user, "total_tics": 0, "total_owed": 0.0,
            "monthly_breakdown": [], "cost_per_tic": self.cost_per_tic
        }
        if user in self.data:
            for month, count in sorted(self.data[user].items()):
                amount_owed = count * self.cost_per_tic
                history["total_tics"] += count
                history["total_owed"] += amount_owed
                history["monthly_breakdown"].append({
                    "month": month, "count": count, "amount_owed": amount_owed
                })
        return history

    def get_custom_range_report(self, start_month, end_month):
        report_title = f"{start_month} to {end_month}" if start_month != end_month else start_month
        report = {
            "month": report_title, "cost_per_tic": self.cost_per_tic,
            "users": {}, "total_tics": 0, "total_owed": 0.0
        }
        try:
            start_date = datetime.strptime(start_month, '%Y-%m')
            end_date = datetime.strptime(end_month, '%Y-%m')
        except ValueError:
            return {"error": "Invalid date format. Please use YYYY-MM."}

        for user, monthly_data in self.data.items():
            for month_key, count in monthly_data.items():
                try:
                    month_date = datetime.strptime(month_key, '%Y-%m')
                    if start_date <= month_date <= end_date:
                        if user not in report["users"]:
                            report["users"][user] = {"count": 0, "amount_owed": 0.0}
                        amount = count * self.cost_per_tic
                        report["users"][user]["count"] += count
                        report["users"][user]["amount_owed"] += amount
                        report["total_tics"] += count
                        report["total_owed"] += amount
                except ValueError:
                    continue
        report["users"] = [{"user": u, **d} for u, d in report["users"].items()]
        return report


# ---------------------------------------------------------------------------- #
#                                 Flask Web App                                #
# ---------------------------------------------------------------------------- #
app = Flask(__name__)
# You can change the cost per tic here.
jar = ticJar(cost_per_tic=0.50)

# ------------------------------ HTML Template ------------------------------- #
# This string contains the full HTML, CSS (via Tailwind), and JavaScript for the frontend.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>tic Jar</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .card { background-color: #1f2937; border: 1px solid #374151; }
        .btn {
            background-color: #3b82f6; /* bg-blue-600 */
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            font-weight: 600;
            transition: background-color 0.2s;
        }
        .btn:hover { background-color: #2563eb; } /* hover:bg-blue-700 */
        .btn-secondary { background-color: #4b5563; } /* bg-gray-600 */
        .btn-secondary:hover { background-color: #374151; } /* hover:bg-gray-700 */
        .input {
            background-color: #374151;
            border: 1px solid #4b5563;
            color: white;
            padding: 0.75rem;
            border-radius: 0.5rem;
            width: 100%;
        }
    </style>
</head>
<body class="bg-gray-900 text-gray-200 flex items-center justify-center min-h-screen p-4">

    <div class="w-full max-w-4xl mx-auto">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-white">The Critic Counter</h1>
            <p class="text-lg text-gray-400 mt-2">Be kind to yourself, not just others.</p>
        </header>

        <main class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <!-- Left Column: Actions -->
            <div class="flex flex-col gap-8">
                <!-- Add tic Card -->
                <div class="card p-6 rounded-lg shadow-lg">
                    <h2 class="text-2xl font-semibold mb-4 text-white">Add a "tic"</h2>
                    <div class="flex flex-col sm:flex-row gap-4">
                        <input type="text" id="user-input" placeholder="Enter user name" class="input flex-grow">
                        <button id="add-tic-btn" class="btn">Add a "tic"</button>
                    </div>
                </div>

                <!-- Reports Card -->
                <div class="card p-6 rounded-lg shadow-lg">
                    <h2 class="text-2xl font-semibold mb-4 text-white">Generate Reports</h2>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <button id="current-month-btn" class="btn btn-secondary">Current Month</button>
                        <button id="prev-month-btn" class="btn btn-secondary">Previous Month</button>
                    </div>
                    <div class="mt-4">
                        <input type="text" id="user-history-input" placeholder="Username for history" class="input">
                        <button id="user-history-btn" class="btn btn-secondary w-full mt-4">Get User History</button>
                    </div>
                </div>
            </div>

            <!-- Right Column: Results -->
            <div id="results-container" class="card p-6 rounded-lg shadow-lg min-h-[300px]">
                <h2 class="text-2xl font-semibold mb-4 text-white">Results</h2>
                <div id="results-content" class="text-gray-300">
                    <p>Reports and user history will be displayed here.</p>
                </div>
            </div>
        </main>

        <!-- Toast Notification -->
        <div id="toast" class="fixed bottom-5 right-5 bg-green-500 text-white py-2 px-4 rounded-lg shadow-lg opacity-0 transition-opacity duration-300">
            Notification
        </div>

    </div>

    <script>
        // DOM Elements
        const addticBtn = document.getElementById('add-tic-btn');
        const userInput = document.getElementById('user-input');
        const currentMonthBtn = document.getElementById('current-month-btn');
        const prevMonthBtn = document.getElementById('prev-month-btn');
        const userHistoryBtn = document.getElementById('user-history-btn');
        const userHistoryInput = document.getElementById('user-history-input');
        const resultsContent = document.getElementById('results-content');
        const toast = document.getElementById('toast');

        // --- Event Listeners ---
        addticBtn.addEventListener('click', addtic);
        currentMonthBtn.addEventListener('click', () => getReport('current'));
        prevMonthBtn.addEventListener('click', () => getReport('previous'));
        userHistoryBtn.addEventListener('click', getUserHistory);

        // --- API Functions ---
        async function addtic() {
            const user = userInput.value.trim();
            if (!user) {
                showToast('Username cannot be empty.', 'error');
                return;
            }
            try {
                const response = await fetch('/api/tic', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user: user })
                });
                const result = await response.json();
                if (response.ok) {
                    showToast(result.message);
                    userInput.value = '';
                    getReport('current'); // Refresh the report
                } else {
                    throw new Error(result.error || 'Failed to add tic');
                }
            } catch (error) {
                showToast(error.message, 'error');
            }
        }

        async function getReport(type) {
            let url = '/api/report';
            if (type === 'previous') {
                url += '?type=previous';
            }
            try {
                const response = await fetch(url);
                const report = await response.json();
                if (response.ok) {
                    displayReport(report);
                } else {
                    throw new Error(report.error || 'Failed to fetch report');
                }
            } catch (error) {
                showToast(error.message, 'error');
            }
        }

        async function getUserHistory() {
            const user = userHistoryInput.value.trim();
            if (!user) {
                showToast('Please enter a username for history lookup.', 'error');
                return;
            }
            try {
                const response = await fetch(`/api/history/${user}`);
                const history = await response.json();
                if (response.ok) {
                    displayUserHistory(history);
                } else {
                    throw new Error(history.error || 'Failed to fetch user history');
                }
            } catch (error) {
                showToast(error.message, 'error');
            }
        }

        // --- Display Functions ---
        function displayReport(report) {
            resultsContent.innerHTML = ''; // Clear previous results
            const cost = parseFloat(report.cost_per_tic).toFixed(2);
            let content = `<h3 class="text-xl font-bold mb-3">Report: ${report.month}</h3>`;

            if (!report.users || report.users.length === 0) {
                content += '<p>No tics recorded for this period. Great job!</p>';
            } else {
                content += '<ul class="space-y-2">';
                const sortedUsers = report.users.sort((a, b) => b.count - a.count);
                sortedUsers.forEach(u => {
                    const userName = u.user.charAt(0).toUpperCase() + u.user.slice(1);
                    content += `<li class="flex justify-between items-center">
                                    <span>${userName}</span>
                                    <span class="font-mono bg-gray-700 px-2 py-1 rounded">${u.count} tics | $${parseFloat(u.amount_owed).toFixed(2)}</span>
                               </li>`;
                });
                content += '</ul>';
                content += '<hr class="border-gray-600 my-4">';
                content += `<div class="font-bold text-lg">Total tics: ${report.total_tics}</div>`;
                content += `<div class="font-bold text-lg">Total Owed: $${parseFloat(report.total_owed).toFixed(2)}</div>`;
            }
            resultsContent.innerHTML = content;
        }

        function displayUserHistory(history) {
            resultsContent.innerHTML = '';
            const userName = history.user.charAt(0).toUpperCase() + history.user.slice(1);
            let content = `<h3 class="text-xl font-bold mb-3">All-Time History for ${userName}</h3>`;

            if (!history.monthly_breakdown || history.monthly_breakdown.length === 0) {
                content += '<p>This user has a clean record!</p>';
            } else {
                content += '<ul class="space-y-2">';
                history.monthly_breakdown.forEach(item => {
                    content += `<li class="flex justify-between items-center">
                                    <span>${item.month}</span>
                                    <span class="font-mono bg-gray-700 px-2 py-1 rounded">${item.count} tics | $${parseFloat(item.amount_owed).toFixed(2)}</span>
                               </li>`;
                });
                content += '</ul>';
                content += '<hr class="border-gray-600 my-4">';
                content += `<div class="font-bold text-lg">Total tics: ${history.total_tics}</div>`;
                content += `<div class="font-bold text-lg">Total Owed: $${parseFloat(history.total_owed).toFixed(2)}</div>`;
            }
            resultsContent.innerHTML = content;
        }

        function showToast(message, type = 'success') {
            toast.textContent = message;
            toast.className = toast.className.replace(/bg-\w+-500/, type === 'success' ? 'bg-green-500' : 'bg-red-500');
            toast.classList.remove('opacity-0');
            setTimeout(() => {
                toast.classList.add('opacity-0');
            }, 3000);
        }

        // Load initial report
        getReport('current');
    </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------- #
#                                 API Endpoints                                #
# ---------------------------------------------------------------------------- #
@app.route('/')
def home():
    """Serves the main HTML page."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/tic', methods=['POST'])
def api_add_tic():
    """Adds a tic for a user."""
    data = request.get_json()
    if not data or 'user' not in data:
        return jsonify({"error": "User not provided"}), 400
    result = jar.add_tic(data['user'])
    return jsonify(result)


@app.route('/api/report', methods=['GET'])
def api_get_report():
    """Gets a report for the current or previous month."""
    report_type = request.args.get('type', 'current')
    if report_type == 'current':
        month_key = datetime.now().strftime('%Y-%m')
        report = jar.get_custom_range_report(month_key, month_key)
    elif report_type == 'previous':
        now = datetime.now()
        first_day_current_month = now.replace(day=1)
        last_day_prev_month = first_day_current_month - timedelta(days=1)
        prev_month_key = last_day_prev_month.strftime('%Y-%m')
        report = jar.get_custom_range_report(prev_month_key, prev_month_key)
    else:
        return jsonify({"error": "Invalid report type"}), 400
    return jsonify(report)


@app.route('/api/history/<user>', methods=['GET'])
def api_get_user_history(user):
    """Gets the all-time history for a user."""
    if not user:
        return jsonify({"error": "User not provided"}), 400
    history = jar.get_user_history(user)
    return jsonify(history)


# ---------------------------------------------------------------------------- #
#                                 Main Execution                               #
# ---------------------------------------------------------------------------- #
if __name__ == '__main__':
    # Running in debug mode is useful for development.
    # For a real deployment, you would use a proper web server like Gunicorn.
    app.run(debug=True)
