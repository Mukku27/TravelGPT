from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import date
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.serpapi_tools import SerpApiTools
from phi.tools.duckduckgo import DuckDuckGo
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Travel Agent API")

class TravelPreferences(BaseModel):
    destination: str
    present_location: str
    start_date: date
    end_date: date
    budget: str
    travel_styles: List[str]

class QuestionRequest(BaseModel):
    question: str
    destination: str
    travel_plan: str

class ModifyRequest(BaseModel):
    travel_plan: str
    modifications: str

class TravelAgent:
    def __init__(self):
        self.agent = Agent(
            name="Comprehensive Travel Assistant",
            model=Groq(id="llama-3.3-70b-versatile"),
            tools=[DuckDuckGo(),SerpApiTools()],
            instructions=[
                "You are a comprehensive travel planning assistant with expertise in all aspects of travel.",
                "For every recommendation and data point, you MUST provide working source links.",
                "Your knowledge spans across:",
                "- Seasonal travel timing and weather patterns",
                "- Transportation options and booking",
                "- Accommodation recommendations",
                "- Day-by-day itinerary planning",
                "- Local cuisine and restaurant recommendations",
                "- Practical travel tips and cultural advice",
                "- Budget estimation and cost breakdown",
                "Format all responses in markdown with clear headings (##) and bullet points.",
                "Use [text](url) format for all hyperlinks.",
                "Verify all links are functional before including them.",
                "Organize information clearly with appropriate sections based on the query type."
            ]
        )

    def generate_travel_plan(self, preferences: TravelPreferences) -> str:
        prompt = f"""Act as a Personalized Travel Expert
You are a travel expert specializing in creating tailored, detailed travel plans. Design a comprehensive itinerary for a trip to {preferences.destination} spanning {preferences.end_date - preferences.start_date}.days days, starting on {preferences.start_date} and ending on {preferences.end_date}.

Traveler Preferences:
Budget Level: {preferences.budget}
Travel Styles: {', '.join(preferences.travel_styles)}
Your Task:
Provide a structured markdown response that includes the following elements:

🌞 Best Time to Visit:
 - Highlight seasonal considerations for visiting {preferences.destination}.
 - Day-by-day weather forecast from {preferences.start_date} to {preferences.end_date}
 - Alternative date suggestions if weather is unfavorable 
 - Include source links for all weather data.
 - Offer clothing recommendations for each day based on weather forecasts. For example:
    - Warm jackets and boots for cold, snowy days.
    - Light, breathable clothing for warm, sunny days.
    - Raincoats and umbrellas for rainy conditions.

🏨 Accommodation Recommendations:
 - Suggest accommodations within the {preferences.budget} range.
 - Include pros and cons, prices, amenities, and booking links.
 - Indicate the distance and travel time to major attractions.  Include map links where possible.
 - Format your response using markdown with clear headings (##) and bullet points. Use [text](url) format for hyperlinks. Verify all links are functional before including them.

🗺️ Day-by-Day Itinerary:
 - Create a detailed itinerary for each day, broken into specific time slots (e.g., "9:00 AM–12:00 PM: Visit [Attraction]").
 - Incorporate activities, attractions, and cultural experiences that align with the specified travel styles.
 - Include booking links, costs, and recommendations for optimizing time and enjoyment.

🍽️ Culinary Highlights:
 - Recommend local cuisines, restaurants, and food experiences.
 - Provide suggestions based on the travel styles (e.g., street food, fine dining, or unique culinary tours).
 - Include price ranges, opening hours, and reservation links, where available.

💡 Practical Travel Tips:
 - List local and intercity transportation options (e.g., public transit, car rentals, taxis).
 - Provide advice on cultural etiquette, local customs, and safety tips.
 - Include a suggested daily budget breakdown for meals, transport, and activities.

💰 Estimated Total Trip Cost:
 - Provide an itemized expense breakdown by category according to {preferences.budget}
 - Accommodation, transportation, meals, activities, and miscellaneous expenses.
 - Offer budget-saving tips specific to {preferences.budget} constraints.

🚂 Transportation Details:
 - Recommend transportation options from {preferences.present_location} to {preferences.destination}.
 - Include schedules, pricing, duration, and booking links for trains, buses, or flights.

Output Requirements:
 - Use clear, easy-to-read markdown with headings and bullet points for each section.
 - Provide source links, booking references, and maps wherever applicable.
 - Ensure all details are actionable and well-organized to facilitate ease of planning.
"""
        response = self.agent.run(prompt)
        return response.content if hasattr(response, 'content') else str(response)

    def answer_question(self, request: QuestionRequest, preferences: TravelPreferences) -> str:
        prompt = f"""Using the context of this travel plan for {preferences.destination}:

{request.travel_plan}

Please answer this specific question: {request.question}

Guidelines for your response:
1. Focus specifically on answering the question asked
2. Reference relevant parts of the travel plan when applicable
3. Provide new information if the travel plan doesn't cover the topic
4. Include verified source links for any new information
5. Keep the response concise but comprehensive
6. Use markdown formatting for clarity

Format your response with appropriate headings and verify all included links."""
        response = self.agent.run(prompt)
        return response.content if hasattr(response, 'content') else str(response)

    def modify_plan(self, request: ModifyRequest) -> str:
        prompt = f"""Modify the following travel plan based on the specified changes:

Original Travel Plan:
{request.travel_plan}

Modifications:
{request.modifications}

Guidelines:
1. Integrate changes seamlessly into the existing plan.
2. Maintain the original structure and formatting.
3. Provide source links for any new information added.
4. Ensure all details are accurate and up-to-date.

Return the updated travel plan in markdown format."""
        response = self.agent.run(prompt)
        return response.content if hasattr(response, 'content') else str(response)


travel_agent = TravelAgent()

@app.post("/generate-plan")
async def generate_plan(preferences: TravelPreferences):
    try:
        travel_plan = travel_agent.generate_travel_plan(preferences)
        return {"travel_plan": travel_plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/answer-question")
async def answer_question(request: QuestionRequest):
    try:
        answer = travel_agent.answer_question(request)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/modify-plan")
async def modify_plan(request: ModifyRequest):
    try:
        modified_plan = travel_agent.modify_plan(request)
        return {"modified_plan": modified_plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
