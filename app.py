from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Sample data representing your projects
PROJECTS = [
    {
        "id": 1,
        "title": "Weather Data APIx",
        "description": "A RESTful API built with Flask and PostgreSQL that aggregates historical weather data.",
        "tech_stack": ["Python", "Flask", "PostgreSQL", "Docker"],
        "github_url": "https://github.com/asalehtx/weather-api",
        "live_demo": "/api/v1/weather-demo" 
    },
    {
        "id": 2,
        "title": "Auth Microservice",
        "description": "JWT-based authentication server built for microservice architectures.",
        "tech_stack": ["Node.js", "Express", "MongoDB", "Redis"],
        "github_url": "https://github.com/asalehtx/auth-service",
        "live_demo": None
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

if __name__ == '__main__':
    app.run(debug=True)