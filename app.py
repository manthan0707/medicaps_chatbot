from flask import Flask, render_template, request, jsonify
import json, os

app = Flask(__name__, static_folder='static', template_folder='templates')

# Load FAQs and placement data
with open(os.path.join(app.root_path, 'faqs.json'), 'r', encoding='utf-8') as f:
    faqs = json.load(f)

placement_data = {
    "2022": {
        "highest_package": "48 LPA",
        "average_package": "6.5 LPA",
        "top_companies": ["Amazon", "TCS", "Infosys"]
    },
    "2023": {
        "highest_package": "55 LPA",
        "average_package": "7 LPA",
        "top_companies": ["Microsoft", "Wipro", "Accenture"]
    },
    "2024": {
        "highest_package": "60 LPA",
        "average_package": "7.5 LPA",
        "top_companies": ["Google", "Deloitte", "Capgemini"]
    }
}

def find_faq_response(message):
    msg = message.lower()
    # simple keyword match for faqs
    for key, ans in faqs.items():
        if key in msg or all(word in msg for word in key.split()[:2]):
            return ans
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get', methods=['POST'])
def chatbot_response():
    data = request.get_json() or {}
    user_text = data.get('message','').strip().lower()
    if not user_text:
        return jsonify({'response':'Please type your question.'})

    # Check for placement queries
    if 'placement' in user_text or 'package' in user_text or 'placements' in user_text:
        # if user asked for a specific year
        for year in placement_data:
            if year in user_text:
                d = placement_data[year]
                resp = f"Placement {year}: Highest Package: {d['highest_package']}, Average Package: {d['average_package']}, Top Companies: {', '.join(d['top_companies'])}."
                return jsonify({'response': resp})
        # else return full summary
        lines = []
        for y, d in placement_data.items():
            lines.append(f"{y}: Highest {d['highest_package']}, Avg {d['average_package']}, Top: {', '.join(d['top_companies'])}")
        return jsonify({'response': ' | '.join(lines)})

    # Check FAQs
    faq_resp = find_faq_response(user_text)
    if faq_resp:
        return jsonify({'response': faq_resp})

    # Default fallback
    return jsonify({'response': "Sorry, I don't have that information. Please contact the university admission office at +91-731-4259500 or email info@medicaps.ac.in."})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
