"""Simple web interface for the Airbnb Guest Assistant."""

from flask import Flask, render_template, request, jsonify, session
import os
from assistant import process_guest_message

app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    guest_message = data.get("message", "").strip()
    source_email = data.get("source_email", "host1@example.com")
    api_key = data.get("api_key", "").strip()
    sheet_link = data.get("sheet_link", "").strip()

    if not guest_message:
        return jsonify({"error": "Please enter a message."}), 400
    if not api_key:
        return jsonify({"error": "Please enter your Anthropic API key."}), 400

    os.environ["ANTHROPIC_API_KEY"] = api_key

    try:
        response = process_guest_message(
            guest_message=guest_message,
            source_email=source_email,
            sheet_link=sheet_link,
        )
        is_alert = response == "ALERT_HOST"
        return jsonify({"response": response, "is_alert": is_alert})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n✅ Airbnb Guest Assistant is running!")
    print("👉 Open your browser and go to: http://localhost:5000\n")
    app.run(debug=False, port=5000)
