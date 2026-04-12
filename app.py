import requests
from bs4 import BeautifulSoup
import os
import csv
import io
from flask import Flask, render_template, jsonify, request, Response, redirect, url_for
from dotenv import load_dotenv # type: ignore
import google.generativeai as genai # type: ignore

# Load secret variables from the .env file
load_dotenv()

# Configure Gemini with your API key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Initialize the Flask app ONLY ONCE
app = Flask(__name__)

@app.before_request
def redirect_railway_to_custom():
    # Check if the user is accessing the site via the old Railway URL
    if request.host == 'adam-saleh-web-app-portfolio.up.railway.app':
        # Instantly bounce them to the custom domain, keeping the rest of the URL intact
        # (e.g., /finance stays /finance)
        return redirect('https://hearhear.agency' + request.full_path, code=301)

# --- AI CHATBOT SETUP ---
law_firm_prompt = """You are the empathetic first point of contact for the Rahgozar Law Firm.
Your goal is to listen to the user's situation, validate their distress, and determine if they have a viable case.
Ask ONE gentle follow-up question at a time to find out:
1) Date of the injury.
2) Type of accident (e.g., car crash, slip and fall).
3) If they sought medical treatment.
Once you have got that info, just ask for their name and phone number so attorney Pegah Rahgozar can give them a call. 
NEVER give legal advice. If they ask a legal question, politely explain that an attorney will need to answer that during their consultation."""

# Initialize the Gemini model with the system instructions
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=law_firm_prompt
)

# Temporary memory to keep track of active user sessions
active_chats = {}

# --- SEO AUDITOR AI SETUP ---
seo_prompt = """You are an expert Technical SEO and WCAG Accessibility Auditor.
Review the provided scraped website data, including the Google Lighthouse Performance and SEO scores. 
Provide a brief, professional analysis.

CRITICAL: Structure your response entirely in raw HTML format (using <h3>, <p>, <ul>, <li>, and <strong> tags). Do NOT use Markdown formatting like ** or ##. 

Include these four sections exactly:
<h3>📊 Score Analysis</h3>
(Provide a 1-2 sentence breakdown of their Lighthouse Performance and SEO scores. Explain what these numbers mean for the user experience and search ranking in plain English.)

<h3>🟢 What Looks Good</h3>
(List what they did right based on the scraped data and scores)

<h3>🔴 Areas for Improvement</h3>
(List what is missing or problematic, highlighting specific scraped data like missing Alt text, H1s, or low performance metrics)

<h3>🚀 Actionable Next Steps</h3>
(Provide 2-3 specific, non-generic steps the webmaster should take immediately to improve their scores, SEO, and accessibility)
"""

seo_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=seo_prompt
)


# --- MOCK DATABASES ---

TRANSACTIONS_DB = [
    {"id": 1, "type": "income", "amount": 5000.00, "category": "Salary", "date": "2026-04-01"},
    {"id": 2, "type": "expense", "amount": 1200.00, "category": "Rent", "date": "2026-04-02"},
    {"id": 3, "type": "expense", "amount": 300.00, "category": "Groceries", "date": "2026-04-05"},
    {"id": 4, "type": "expense", "amount": 150.00, "category": "Entertainment", "date": "2026-04-08"}
]

# Monthly budget limits per category
BUDGETS_DB = {
    "Rent": 1200.00,
    "Groceries": 250.00, # Deliberately set low to trigger an alert!
    "Entertainment": 200.00
}

# All available topics users can subscribe to
AVAILABLE_TOPICS = ["technology", "business", "health", "science"]

# Mock database of articles
ARTICLES_DB = [
    {"id": 101, "title": "New AI Model Released", "topic": "technology", "author": "Alice"},
    {"id": 102, "title": "Market Trends 2026", "topic": "business", "author": "Bob"},
    {"id": 103, "title": "Healthy Eating Habits", "topic": "health", "author": "Charlie"},
    {"id": 104, "title": "Quantum Computing Advances", "topic": "technology", "author": "Alice"},
    {"id": 105, "title": "The Future of Space Travel", "topic": "science", "author": "Dr. Smith"}
]

# Tracks which user is subscribed to which topics
USER_SUBSCRIPTIONS = {
    "user_1": ["technology", "science"]
}

# Mock database to store user settings
USER_SETTINGS_DB = {
    "user_1": {
        "theme": "dark",
        "language": "en",
        "notifications": True
    }
}

# Sample data representing your projects
PROJECTS = [
    {
        "id": 5,
        "title": "AI SEO & Accessibility Auditor",
        "description": "An intelligent web scraping tool that reads live website HTML and leverages the Gemini API to provide actionable SEO and WCAG accessibility improvements.",
        "tech_stack": ["Python", "Flask", "BeautifulSoup", "Gemini API"],
        "github_url": "https://github.com/asalehtx/adam-saleh-web-app-portfolio",
        "dashboard_url": "/seo-auditor",
        "button_label": "Run an Audit"
    },
    {
        "id": 4,
        "title": "AI Legal Intake Agent",
        "description": "An intelligent, empathetic chatbot designed for personal injury law firms. Built using the Google Gemini API, it captures leads, validates user distress, and pre-qualifies potential cases through natural conversation before routing them to a human attorney.",
        "tech_stack": ["Python", "Flask", "Gemini API", "JavaScript", "CSS"],
        "github_url": "https://github.com/asalehtx/adam-saleh-web-app-portfolio",
        "dashboard_url": "/legal-chat",
        "button_label": "Test Live Chat"
    },
    {
        "id": 3,
        "title": "Personal Finance Dashboard & API",
        "description": "A full-stack financial tracking application. The backend is powered by a Flask REST API that handles data aggregation, checks spending against dynamic budget limits, and generates CSV reports. The frontend features a fully responsive UI with asynchronous CRUD operations and real-time Chart.js data visualization, including categorical pie charts and interactive time-series line graphs with custom data grouping.",
        "tech_stack": ["Python", "Flask", "JavaScript", "Chart.js", "CSS Flexbox"],
        "github_url": "https://github.com/asalehtx/adam-saleh-web-app-portfolio",
        "live_demo": "/api/finance/summary",
        "dashboard_url": "/finance-dashboard",
        "button_label": "View Dashboard Demo"
    },
    {
        "id": 2,
        "title": "Content Feed & Subscription API",
        "description": "A RESTful service that implements a basic Pub/Sub model. Users can subscribe to topics of interest, retrieve a personalized feed of articles, and receive topic recommendations.",
        "tech_stack": ["Python", "Flask", "Data Filtering"],
        "github_url": "https://github.com/asalehtx/adam-saleh-web-app-portfolio",
        "live_demo": "/api/users/user_1/feed" 
    },
    {
        "id": 1,
        "title": "User Configuration Manager",
        "description": "A complete CRUD REST API that allows applications to store, retrieve, modify, and delete user preferences (theme, language, etc).",
        "tech_stack": ["Python", "Flask", "REST API"],
        "github_url": "https://github.com/asalehtx/adam-saleh-web-app-portfolio",
        "live_demo": "/api/users/user_1/settings"
    }
]


# --- ROUTES ---

@app.route('/')
def home():
    """Renders the portfolio homepage."""
    return render_template('index.html', projects=PROJECTS)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Renders a detailed page for a specific project."""
    project = next((p for p in PROJECTS if p['id'] == project_id), None)
    if project:
        return render_template('project.html', project=project)
    return "Project not found", 404

# --- USER CONFIGURATION MANAGER API ---
@app.route('/api/users/<user_id>/settings', methods=['GET'])
def get_settings(user_id):
    settings = USER_SETTINGS_DB.get(user_id)
    if not settings:
        return jsonify({"error": "User settings not found"}), 404
    return jsonify({"message": "Settings retrieved successfully", "data": settings}), 200

@app.route('/api/users/<user_id>/settings', methods=['POST'])
def create_settings(user_id):
    if user_id in USER_SETTINGS_DB:
        return jsonify({"error": "Settings already exist for this user"}), 400
    data = request.get_json()
    USER_SETTINGS_DB[user_id] = {
        "theme": data.get("theme", "light"),
        "language": data.get("language", "en"),
        "notifications": data.get("notifications", True)
    }
    return jsonify({"message": f"Settings created for {user_id}", "data": USER_SETTINGS_DB[user_id]}), 201

@app.route('/api/users/<user_id>/settings', methods=['PUT'])
def update_settings(user_id):
    if user_id not in USER_SETTINGS_DB:
        return jsonify({"error": "User settings not found"}), 404
    data = request.get_json()
    if "theme" in data:
        USER_SETTINGS_DB[user_id]["theme"] = data["theme"]
    if "language" in data:
        USER_SETTINGS_DB[user_id]["language"] = data["language"]
    if "notifications" in data:
        USER_SETTINGS_DB[user_id]["notifications"] = data["notifications"]
    return jsonify({"message": f"Settings updated for {user_id}", "data": USER_SETTINGS_DB[user_id]}), 200

@app.route('/api/users/<user_id>/settings', methods=['DELETE'])
def delete_settings(user_id):
    if user_id in USER_SETTINGS_DB:
        del USER_SETTINGS_DB[user_id]
        return jsonify({"message": f"Settings deleted for {user_id}"}), 200
    return jsonify({"error": "User settings not found"}), 404

# --- CONTENT SUBSCRIPTION API ---
@app.route('/api/users/<user_id>/subscriptions', methods=['POST'])
def add_subscription(user_id):
    data = request.get_json()
    topic = data.get("topic")
    if topic not in AVAILABLE_TOPICS:
        return jsonify({"error": f"Topic '{topic}' does not exist."}), 400
    if user_id not in USER_SUBSCRIPTIONS:
        USER_SUBSCRIPTIONS[user_id] = []
    if topic not in USER_SUBSCRIPTIONS[user_id]:
        USER_SUBSCRIPTIONS[user_id].append(topic)
        return jsonify({"message": f"Successfully subscribed to {topic}", "subscriptions": USER_SUBSCRIPTIONS[user_id]}), 201
    return jsonify({"message": f"Already subscribed to {topic}"}), 200

@app.route('/api/users/<user_id>/feed', methods=['GET'])
def get_personalized_feed(user_id):
    user_topics = USER_SUBSCRIPTIONS.get(user_id, [])
    if not user_topics:
        return jsonify({"message": "You are not subscribed to any topics yet.", "data": []}), 200
    personalized_articles = [article for article in ARTICLES_DB if article["topic"] in user_topics]
    return jsonify({"message": "Your personalized feed", "subscribed_topics": user_topics, "data": personalized_articles}), 200

@app.route('/api/users/<user_id>/recommendations', methods=['GET'])
def get_recommendations(user_id):
    user_topics = USER_SUBSCRIPTIONS.get(user_id, [])
    recommended_topics = [topic for topic in AVAILABLE_TOPICS if topic not in user_topics]
    return jsonify({"message": "Topics you might like", "data": recommended_topics}), 200

# --- FINANCE TRACKER API ---
@app.route('/api/finance/transactions', methods=['POST'])
def add_transaction():
    data = request.get_json()
    new_id = len(TRANSACTIONS_DB) + 1
    new_transaction = {
        "id": new_id,
        "type": data.get("type"), 
        "amount": float(data.get("amount", 0)),
        "category": data.get("category"),
        "date": data.get("date")
    }
    TRANSACTIONS_DB.append(new_transaction)
    return jsonify({"message": "Transaction added", "data": new_transaction}), 201

@app.route('/api/finance/transactions/<int:transaction_id>', methods=['PUT', 'DELETE'])
def modify_transaction(transaction_id):
    global TRANSACTIONS_DB
    if request.method == 'DELETE':
        TRANSACTIONS_DB = [t for t in TRANSACTIONS_DB if t['id'] != transaction_id]
        return jsonify({"message": "Transaction deleted"}), 200
    if request.method == 'PUT':
        data = request.get_json()
        for t in TRANSACTIONS_DB:
            if t['id'] == transaction_id:
                t['type'] = data.get('type', t['type'])
                t['amount'] = float(data.get('amount', t['amount']))
                t['category'] = data.get('category', t['category'])
                t['date'] = data.get('date', t['date'])
                return jsonify({"message": "Transaction updated", "data": t}), 200
        return jsonify({"error": "Transaction not found"}), 404

@app.route('/api/finance/summary', methods=['GET'])
def get_finance_summary():
    total_income = 0
    total_expenses = 0
    spending_by_category = {}
    alerts = []
    for t in TRANSACTIONS_DB:
        if t["type"] == "income":
            total_income += t["amount"]
        elif t["type"] == "expense":
            total_expenses += t["amount"]
            cat = t["category"]
            spending_by_category[cat] = spending_by_category.get(cat, 0) + t["amount"]
    for category, spent in spending_by_category.items():
        limit = BUDGETS_DB.get(category)
        if limit and spent > limit:
            alerts.append(f"ALERT: You have exceeded your {category} budget by ${spent - limit:.2f}!")
    return jsonify({
        "summary": {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_savings": total_income - total_expenses
        },
        "chart_data": spending_by_category, 
        "budget_alerts": alerts,
        "transactions": TRANSACTIONS_DB
    }), 200

@app.route('/api/finance/export/csv', methods=['GET'])
def export_transactions_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Type', 'Amount', 'Category', 'Date'])
    for t in TRANSACTIONS_DB:
        writer.writerow([t['id'], t['type'], t['amount'], t['category'], t['date']])
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=financial_report.csv'
    return response

@app.route('/finance-dashboard')
def finance_dashboard():
    return render_template('finance.html')

# --- LEGAL CHATBOT ROUTES ---
@app.route('/api/chat', methods=['POST'])
def legal_chat():
    data = request.get_json()
    user_message = data.get("message")
    session_id = data.get("session_id", "demo_user")

    if session_id not in active_chats:
        active_chats[session_id] = model.start_chat(history=[])

    chat_session = active_chats[session_id]

    try:
        response = chat_session.send_message(user_message)
        return jsonify({"reply": response.text, "status": "success"})
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return jsonify({"reply": "I'm so sorry, we are experiencing a technical issue connecting you right now. Please call our office directly at 832-205-5978.", "status": "error"}), 500
    
@app.route('/legal-chat')
def legal_chat_page():
    return render_template('legal.html')

# --- SEO AUDITOR ROUTES ---
@app.route('/seo-auditor')
def seo_auditor_page():
    return render_template('seo.html')

@app.route('/api/audit', methods=['POST'])
def run_audit():
    data = request.get_json()
    target_url = data.get('url')
    
    # 1. Basic validation and formatting
    if not target_url:
        return jsonify({"error": "Please provide a valid URL."}), 400
        
    if not target_url.startswith('http'):
        target_url = 'https://' + target_url

    try:
        # 2. Download the website (We add a User-Agent so websites don't block us as a bot)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status() # Check for HTTP errors like 404
        
        # 3. Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 4. Extract the SEO & Accessibility Data
        title = soup.title.string if soup.title else "No title tag found"
        
        # We use a lambda function to convert the 'name' attribute to lowercase before checking it
        meta_desc_tag = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'description'})
        meta_desc = meta_desc_tag['content'] if meta_desc_tag and meta_desc_tag.has_attr('content') else "No meta description found"
        
        h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
        h2_count = len(soup.find_all('h2'))
        
        images = soup.find_all('img')
        missing_alt_count = sum(1 for img in images if not img.get('alt'))
        
        # 5. Fetch Official Google PageSpeed Insights (PSI) Scores
        pagespeed_key = os.environ.get("PAGESPEED_API_KEY")
        
        # Build the URL. If you have a key, attach it!
        psi_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={target_url}&category=performance&category=seo"
        if pagespeed_key:
            psi_url += f"&key={pagespeed_key}"
            
        try:
            # Increased timeout to 40s because Google's Lighthouse is slow
            psi_response = requests.get(psi_url, timeout=40)
            psi_data = psi_response.json()
            
            # Check if Google sent back an error instead of data
            if 'error' in psi_data:
                print(f"PageSpeed API Blocked us: {psi_data['error'].get('message')}")
                perf_score, seo_score = "N/A", "N/A"
            else:
                lighthouse = psi_data.get('lighthouseResult', {}).get('categories', {})
                
                # Safely extract scores
                perf_score = int(lighthouse.get('performance', {}).get('score', 0) * 100) if lighthouse.get('performance') else "N/A"
                seo_score = int(lighthouse.get('seo', {}).get('score', 0) * 100) if lighthouse.get('seo') else "N/A"
                
        except Exception as e:
            print(f"PageSpeed Request Failed: {e}")
            perf_score, seo_score = "N/A", "N/A"

        # 6. Format the scraped data AND new scores into a readable string for the AI
        ai_input = f"""
        Website Analyzed: {target_url}
        Google Lighthouse SEO Score: {seo_score}/100
        Google Lighthouse Performance Score: {perf_score}/100
        Title: {title}
        Meta Description: {meta_desc}
        H1 Tags: {', '.join(h1_tags) if h1_tags else 'None'}
        H2 Count: {h2_count}
        Images missing Alt Text: {missing_alt_count} out of {len(images)}
        """
        
        # 7. Ask Gemini to analyze the data
        try:
            ai_response = seo_model.generate_content(ai_input)
            report_html = ai_response.text
        except Exception as e:
            print(f"Gemini AI Error: {e}")
            return jsonify({"error": "Failed to generate AI analysis."}), 500
        
        # 8. Send the scores AND the AI HTML report back to the frontend
        return jsonify({
            "message": "Audit complete! Here is your technical analysis.",
            "report": report_html,
            "performance_score": perf_score,
            "seo_score": seo_score,
            "status": "success"
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Could not access website. It may be protected or offline."}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred while parsing: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)