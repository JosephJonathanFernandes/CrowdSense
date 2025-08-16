from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Dummy data (later replaced by Akaash & Ahmed’s backend)
mock_data = {
    "status": "ALERT",   # or "SAFE"
    "tweets": [
        {"user": "NDTV", "text": "Heavy rains in Mumbai causing waterlogging", "sentiment": "Negative"},
        {"user": "TOI", "text": "Traffic diversion announced in Bandra", "sentiment": "Neutral"},
        {"user": "ANI", "text": "Rescue teams deployed in low-lying areas", "sentiment": "Positive"}
    ],
    "news": [
        {"headline": "Mumbai faces severe waterlogging after downpour"},
        {"headline": "Schools declared holiday in affected areas"}
    ]
}

@app.route("/")
def index():
    return render_template("index.html", data=mock_data)

@app.route("/api/data")
def api_data():
    return jsonify(mock_data)

if __name__ == "__main__":
    app.run(debug=True)
