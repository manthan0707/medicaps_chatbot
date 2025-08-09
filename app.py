
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def chatbot_response():
    user_msg = request.json["msg"].lower()
    if "placement" in user_msg:
        reply = "Medicaps University placements are excellent with top companies like TCS, Infosys, and Wipro visiting every year."
    elif "admission" in user_msg:
        reply = "For admission, you need to apply online at Medicaps' official site and meet eligibility based on your 12th marks."
    elif "courses" in user_msg:
        reply = "Available courses include B.Tech, M.Tech, BBA, MBA, BCA, MCA, and Pharmacy."
    elif "about" in user_msg:
        reply = "Medicaps University, Indore, is a premier institute offering quality education and excellent campus facilities."
    else:
        reply = "I'm here to help with information about Medicaps University, admissions, courses, and placements."
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
