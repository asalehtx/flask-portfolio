# --- MOCK DB: SUBSCRIPTIONS & CONTENT ---

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

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# Mock database to store user settings
USER_SETTINGS_DB = {
    "user_1": {
        "theme": "dark",
        "language": "en",
        "notifications": True
    }
}

from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Sample data representing your projects
PROJECTS = [
    {
        "id": 1,
        "title": "User Configuration Manager",
        "description": "A complete CRUD REST API that allows applications to store, retrieve, modify, and delete user preferences (theme, language, etc).",
        "tech_stack": ["Python", "Flask", "REST API"],
        "github_url": "https://github.com/asalehtx/flask-portfolio",
        "live_demo": "/api/users/user_1/settings" 
    },
    {
        "id": 2,
        "title": "Content Feed & Subscription API",
        "description": "A RESTful service that implements a basic Pub/Sub model. Users can subscribe to topics of interest, retrieve a personalized feed of articles, and receive topic recommendations.",
        "tech_stack": ["Python", "Flask", "Data Filtering"],
        "github_url": "https://github.com/asalehtx/flask-portfolio",
        "live_demo": "/api/users/user_1/feed" 
    }
]

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

# --- LIVE API DEMO ENDPOINT ---
@app.route('/api/v1/weather-demo')
def weather_demo():
    """A live demonstration endpoint to show off your API skills."""
    return jsonify({
        "status": "success",
        "data": {
            "location": "Chicago, IL",
            "temperature_c": 22,
            "condition": "Partly Cloudy"
        },
        "message": "This is a live demo endpoint hosted directly on my portfolio!"
    })

# --- USER CONFIGURATION MANAGER API ---

@app.route('/api/users/<user_id>/settings', methods=['GET'])
def get_settings(user_id):
    """READ: View a user's current settings."""
    settings = USER_SETTINGS_DB.get(user_id)
    if not settings:
        return jsonify({"error": "User settings not found"}), 404
    
    return jsonify({
        "message": "Settings retrieved successfully",
        "data": settings
    }), 200

@app.route('/api/users/<user_id>/settings', methods=['POST'])
def create_settings(user_id):
    """CREATE: Add settings for a new user."""
    if user_id in USER_SETTINGS_DB:
        return jsonify({"error": "Settings already exist for this user"}), 400
    
    data = request.get_json()
    
    # Set defaults if the user didn't provide specific fields
    USER_SETTINGS_DB[user_id] = {
        "theme": data.get("theme", "light"),
        "language": data.get("language", "en"),
        "notifications": data.get("notifications", True)
    }
    
    return jsonify({
        "message": f"Settings created for {user_id}",
        "data": USER_SETTINGS_DB[user_id]
    }), 201

@app.route('/api/users/<user_id>/settings', methods=['PUT'])
def update_settings(user_id):
    """UPDATE: Modify existing settings."""
    if user_id not in USER_SETTINGS_DB:
        return jsonify({"error": "User settings not found"}), 404
    
    data = request.get_json()
    
    # Update only the provided fields
    if "theme" in data:
        USER_SETTINGS_DB[user_id]["theme"] = data["theme"]
    if "language" in data:
        USER_SETTINGS_DB[user_id]["language"] = data["language"]
    if "notifications" in data:
        USER_SETTINGS_DB[user_id]["notifications"] = data["notifications"]
        
    return jsonify({
        "message": f"Settings updated for {user_id}",
        "data": USER_SETTINGS_DB[user_id]
    }), 200

@app.route('/api/users/<user_id>/settings', methods=['DELETE'])
def delete_settings(user_id):
    """DELETE: Remove a user's settings."""
    if user_id in USER_SETTINGS_DB:
        del USER_SETTINGS_DB[user_id]
        return jsonify({"message": f"Settings deleted for {user_id}"}), 200
        
    return jsonify({"error": "User settings not found"}), 404

# --- CONTENT SUBSCRIPTION API ---

@app.route('/api/users/<user_id>/subscriptions', methods=['POST'])
def add_subscription(user_id):
    """Subscribe a user to a new topic."""
    data = request.get_json()
    topic = data.get("topic")

    if topic not in AVAILABLE_TOPICS:
        return jsonify({"error": f"Topic '{topic}' does not exist."}), 400

    # Initialize user's subscription list if they are new
    if user_id not in USER_SUBSCRIPTIONS:
        USER_SUBSCRIPTIONS[user_id] = []

    # Add the topic if they aren't already subscribed
    if topic not in USER_SUBSCRIPTIONS[user_id]:
        USER_SUBSCRIPTIONS[user_id].append(topic)
        return jsonify({"message": f"Successfully subscribed to {topic}", "subscriptions": USER_SUBSCRIPTIONS[user_id]}), 201
    
    return jsonify({"message": f"Already subscribed to {topic}"}), 200

@app.route('/api/users/<user_id>/feed', methods=['GET'])
def get_personalized_feed(user_id):
    """Retrieve articles matching the user's subscribed topics."""
    user_topics = USER_SUBSCRIPTIONS.get(user_id, [])
    
    if not user_topics:
        return jsonify({"message": "You are not subscribed to any topics yet.", "data": []}), 200

    # Filter articles where the article's topic is in the user's subscribed topics
    personalized_articles = [article for article in ARTICLES_DB if article["topic"] in user_topics]
    
    return jsonify({
        "message": "Your personalized feed",
        "subscribed_topics": user_topics,
        "data": personalized_articles
    }), 200

@app.route('/api/users/<user_id>/recommendations', methods=['GET'])
def get_recommendations(user_id):
    """Recommend topics the user is NOT currently subscribed to."""
    user_topics = USER_SUBSCRIPTIONS.get(user_id, [])
    
    # Find topics in the AVAILABLE_TOPICS list that the user doesn't have
    recommended_topics = [topic for topic in AVAILABLE_TOPICS if topic not in user_topics]
    
    return jsonify({
        "message": "Topics you might like",
        "data": recommended_topics
    }), 200

if __name__ == '__main__':
    app.run(debug=True)