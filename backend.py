from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from phi.agent import Agent
from phi.model.groq import Groq
from duckduckgo_search import DDGS

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Groq Llama model and DuckDuckGo search tool
def duckduckgo_search(query):
    ddg = DDGS()
    return ddg.search(query)

travel_agent = Agent(
    name="Travel Planner",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[duckduckgo_search],
    instructions=[
        "You are a travel planning assistant using Groq Llama.",
        "Help users plan their trips by researching destinations, finding attractions, suggesting accommodations, and providing transportation options.",
        "Give me relevant live links for each place and hotel you provide by searching on the internet.",
        "Always verify information is current before making recommendations."
    ],
    show_tool_calls=True,
    markdown=True
)

@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    """Generate a comprehensive travel plan based on user inputs."""
    try:
        data = request.json
        destination = data.get("destination")
        duration = data.get("duration")
        start_date = datetime.strptime(data.get("start_date"), "%Y-%m-%d")
        budget = data.get("budget")
        travel_style = data.get("travel_style", [])
        present_location = data.get("present_location")

        if not destination or not duration or not budget:
            return jsonify({"error": "Missing required fields"}), 400

        end_date = start_date + timedelta(days=duration)
        prompt = f"""
        Create a comprehensive travel plan for {destination} for {duration} days starting from {start_date} and ending on {end_date}.

        Travel Preferences:
        - Budget Level: {budget}
        - Travel Styles: {', '.join(travel_style)}

        Please provide a detailed itinerary that includes:

        1. 🌞 Best Time to Visit
        - Seasonal highlights
        - Weather considerations for each day from {start_date} to {end_date} with source links. If the weather is bad on any particular day, suggest alternative dates with good weather.

        2. 🏨 Accommodation Recommendations
        - {budget} range hotels/stays
        - Locations and proximity to attractions

        3. 🗺️ Day-by-Day Itinerary
        - Detailed daily activities
        - Must-visit attractions
        - Local experiences aligned with travel styles

        4. 🍽️ Culinary Experiences
        - Local cuisine highlights
        - Recommended restaurants
        - Food experiences matching travel style

        5. 💡 Practical Travel Tips
        - Local transportation options
        - Cultural etiquette
        - Safety recommendations
        - Estimated daily budget breakdown

        6. 💰 Estimated Total Trip Cost
        - Breakdown of expenses
        - Money-saving tips

        7. 🚂 Transportation from {present_location} to {destination}
        - Trains/buses available with timings and booking links for travel dates between {start_date} and {end_date}.
        """
        response = travel_agent.run(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        return jsonify({"travel_plan": content}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/ask-question", methods=["POST"])
def ask_question():
    """Answer specific questions about the generated travel plan."""
    try:
        data = request.json
        travel_plan = data.get("travel_plan")
        question = data.get("question")
        destination = data.get("destination")

        if not travel_plan or not question or not destination:
            return jsonify({"error": "Missing required fields"}), 400

        context_question = f"""
        I have a travel plan for {destination}. Here's the existing plan:
        {travel_plan}

        Now, please answer this specific question: {question}

        Provide a focused, concise answer that relates to the existing travel plan if possible.
        """
        response = travel_agent.run(context_question)
        content = response.content if hasattr(response, 'content') else str(response)
        return jsonify({"answer": content}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
