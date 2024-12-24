import streamlit as st
import os
from dotenv import load_dotenv
from phi.agent import Agent
from phi.model.groq import Groq  # Assuming this is how you import Groq Llama
from serpapi import GoogleSearch  #Import SerpAPI library

load_dotenv()
def serp_api_search(query):
    """Searches using SerpAPI and returns the results."""
    search = GoogleSearch({"q": query, "api_key": os.getenv("SERP_API_KEY")})
    results = search.get_dict()
    return results

# Initialize page config
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS for improved UI
st.markdown("""
    <style>
    :root {
        --primary-color: #2E86C1;
        --accent-color: #FF6B6B;
        --background-light: #F8F9FA;
        --text-color: #2C3E50;
        --hover-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    .main {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: var(--accent-color) !important;
        color: white !important;
        font-weight: bold;
        font-size: 1rem;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--hover-shadow);
        background-color: #FF4A4A !important;
    }

    .sidebar .element-container {
        background-color: var(--background-light);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .stExpander {
        background-color: #262730;
        border-radius: 10px;
        padding: 1rem;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .travel-summary {
        background-color: #262730;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    .travel-summary h4 {
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }

    .spinner-text {
        font-size: 1.2rem;
        font-weight: bold;
        color: var(--primary-color);
    }

    </style>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/airplane-take-off.png")
    st.title("Trip Settings")
    
    # User inputs for API keys
    # groq_api_key = st.text_input("🔑 Enter your Groq API Key", type="password")
    #serpapi_key = st.text_input("🔑 Enter your SerpAPI Key", type="password") #Removed SerpAPI Key input
    
    destination = st.text_input("🌍 Where would you like to go?", "")
    duration = st.number_input("📅 How many days?", min_value=1, max_value=30, value=5)
    
    budget = st.select_slider(
        "💰 What's your budget level?",
        options=["Budget", "Moderate", "Luxury"],
        value="Moderate"
    )
    
    if 'travel_style' not in st.session_state:
        st.session_state.travel_style = []
    
    # Define all available travel styles
    all_styles = ["Culture", "Nature", "Adventure", "Relaxation", "Food", "Shopping"]
    
    # Create multiselect with "All" option
    selected_styles = st.multiselect(
        "🎯 Travel Style",
        ["All"] + all_styles,
        key="style_selector"
    )
    
    # Handle "All" selection logic
    if "All" in selected_styles:
        # If "All" is selected, include all styles
        travel_style = all_styles
    else:
        # If "All" is not selected, use only the specifically selected styles
        travel_style = selected_styles

# Initialize session state variables
if 'travel_plan' not in st.session_state:
    st.session_state.travel_plan = None
if 'qa_expanded' not in st.session_state:
    st.session_state.qa_expanded = False

# Add loading state container
loading_container = st.empty()

class SpecializedAgent:
    def __init__(self, name, instructions):
        self.agent = Agent(
            name=name,
            model=Groq(id="llama-3.3-70b-versatile"),
            tools=[serp_api_search],
            instructions=instructions,
            show_tool_calls=True,
            markdown=True
        )

    def run(self, prompt):
        return self.agent.run(prompt)
def create_specialized_agents():
    """Create and return dictionary of specialized travel agents"""
    return {
        'time_agent': SpecializedAgent(
            "Best Time Advisor",
            ["You are a specialist in seasonal travel timing and weather patterns.",
             "Focus on providing detailed information about best times to visit destinations.",
             "Include seasonal events, weather considerations, and peak/off-peak timing."]
        ),
        'accommodation_agent': SpecializedAgent(
            "Accommodation Expert",
            ["You are an expert in finding and recommending accommodations.",
             "Focus on matching lodging options to budget levels and preferences.",
             "Always include actual links and proximity to attractions."]
        ),
        'day_by_day_agent': SpecializedAgent(
            "Day-by-Day Itinerary Agent",
            ["You are responsible for creating a detailed daily itinerary.",
             "Focus on including must-visit attractions and local experiences aligned with travel styles.",
             "Ensure a balance of activities and relaxation time."]
        ),
        'culinary_agent': SpecializedAgent(
            "Culinary Experiences Agent",
            ["You are an expert in highlighting local cuisine and recommending restaurants.",
             "Focus on suggesting food experiences that match the travel style.",
             "Include a mix of traditional and modern culinary experiences."]
        ),
        'practical_tips_agent': SpecializedAgent(
            "Practical Travel Tips Agent",
            ["You offer advice on local transportation options and cultural etiquette.",
             "Focus on providing safety recommendations and an estimated daily budget breakdown.",
             "Ensure travelers are prepared for their trip."]
        ),
        'estimated_cost_agent': SpecializedAgent(
            "Estimated Total Trip Cost Agent",
            ["You are responsible for calculating and providing a breakdown of expenses.",
             "Focus on offering money-saving tips and budgeting advice.",
             "Ensure travelers have a clear understanding of their trip's financial requirements."]
        ),
    }

def coordinate_travel_plan(agents, destination, duration, budget, travel_style):
    """Coordinate between agents to create comprehensive travel plan"""
    
    # Get best time information
    time_prompt = f"Analyze the best time to visit {destination}, considering weather patterns and seasonal events."
    time_info = agents['time_agent'].run(time_prompt)
    
    # Get accommodation recommendations
    accom_prompt = f"Find {budget} level accommodations in {destination} for {duration} days."
    accom_info = agents['accommodation_agent'].run(accom_prompt)
    
    # Get day-by-day itinerary
    day_by_day_prompt = f"Create a detailed daily itinerary for {duration} days in {destination}, focusing on {', '.join(travel_style)}."
    day_by_day_info = agents['day_by_day_agent'].run(day_by_day_prompt)
    
    # Get culinary experiences
    culinary_prompt = f"Recommend local cuisine and restaurants in {destination} that match the travel style: {', '.join(travel_style)}."
    culinary_info = agents['culinary_agent'].run(culinary_prompt)
    
    # Get practical travel tips
    practical_tips_prompt = f"Provide practical travel tips for {destination}, including transportation, cultural etiquette, and safety recommendations."
    practical_tips_info = agents['practical_tips_agent'].run(practical_tips_prompt)
    
    # Get estimated total trip cost
    estimated_cost_prompt = f"Estimate the total cost of a trip to {destination} for {duration} days, considering {budget} level accommodations and activities."
    estimated_cost_info = agents['estimated_cost_agent'].run(estimated_cost_prompt)
    
    # Combine all responses
    complete_plan = f"""
    # Complete Travel Plan for {destination}

    {time_info}
    
    {accom_info}
    
    {day_by_day_info}
    
    {culinary_info}
    
    {practical_tips_info}
    
    {estimated_cost_info}
    
    # ... Other sections ...
    """
    
    return complete_plan

def coordinate_agent_response(agents, context_question):
    """Coordinate between agents to answer a specific question about the travel plan"""
    # Assuming the question is related to the travel plan, use the 'practical_tips_agent' for a response
    response = agents['practical_tips_agent'].run(context_question)
    return response

try:
    # Set API keys in environment variables
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
    os.environ["SERP_API_KEY"] = os.getenv("SERP_API_KEY")

    specialized_agents = create_specialized_agents()

    # Main UI
    st.title("🌎 AI Travel Planner")
    
    st.markdown(f"""
        <div class="travel-summary">
            <h4>Welcome to your personal AI Travel Assistant! 🌟</h4>
            <p>Let me help you create your perfect travel itinerary based on your preferences.</p>
            <p><strong>Destination:</strong> {destination}</p>
            <p><strong>Duration:</strong> {duration} days</p>
            <p><strong>Budget:</strong> {budget}</p>
            <p><strong>Travel Styles:</strong> {', '.join(travel_style)}</p>
        </div>
    """, unsafe_allow_html=True)

    # Generate button
    if st.button("✨ Generate My Perfect Travel Plan", type="primary"):
        if destination:
            try:
                with st.spinner("🔍 Researching and planning your trip..."):
                    travel_plan = coordinate_travel_plan(
                        specialized_agents,
                        destination,
                        duration,
                        budget,
                        travel_style
                    )
                    st.session_state.travel_plan = travel_plan
                    st.markdown(travel_plan)
            except Exception as e:
                st.error(f"Error generating travel plan: {str(e)}")
        else:
            st.warning("Please enter a destination")

    # Q&A Section
    st.divider()
    
    # Use st.expander with a key to maintain state
    qa_expander = st.expander("🤔 Ask a specific question about your destination or travel plan", expanded=st.session_state.qa_expanded)
    
    with qa_expander:
        # Store the expanded state
        st.session_state.qa_expanded = True
        
        question = st.text_input("Your question:", placeholder="What would you like to know about your trip?")
        if st.button("Get Answer", key="qa_button"):
            if question and st.session_state.travel_plan:
                with st.spinner("🔍 Finding answer..."):
                    try:
                        # Combine the original travel plan with the new question for context
                        context_question = f"""
                        I have a travel plan for {destination}. Here's the existing plan:
                        {st.session_state.travel_plan}

                        Now, please answer this specific question: {question}
                        
                        Provide a focused, concise answer that relates to the existing travel plan if possible.
                        """
                        # Utilize the specialized_agents framework to get a response
                        response = coordinate_agent_response(specialized_agents, context_question)
                        st.markdown(response)
                    except Exception as e:
                        st.error(f"Error getting answer: {str(e)}")
            elif not st.session_state.travel_plan:
                st.warning("Please generate a travel plan first before asking questions.")
            else:
                st.warning("Please enter a question")

except Exception as e:
    st.error(f"Application Error: {str(e)}")
