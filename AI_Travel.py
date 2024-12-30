import streamlit as st
import os
import requests
from dotenv import load_dotenv
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.serpapi_tools import SerpApiTools
from phi.tools.duckduckgo import DuckDuckGo
from datetime import datetime

load_dotenv()

def get_weather(location: str):
    """Fetches the weather forecast for a given location."""
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return "API key not found. Please set it in the .env file.", None

    url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            forecast = data['list'][0]
            temperature = forecast['main']['temp']
            condition = forecast['weather'][0]['description'].lower()
            country = data['city']['country']

            needs_update = (
                temperature > 15 or 
                temperature < 5 or
                'rain' in condition or 
                'storm' in condition or
                'snow' in condition
            )

            return {
                'temperature': temperature,
                'condition': condition,
                'country': country,
                'needs_update': needs_update,
                'success': True
            }
        else:
            return {
                'success': False,
                'error': f"Error fetching weather data. Status code: {response.status_code}"
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

class TravelAgent:
   
    def __init__(self):
        self.agent = Agent(
            name="Comprehensive Travel Assistant",
            model=Groq(id="llama-3.3-70b-versatile"),
            tools=[SerpApiTools(), DuckDuckGo()],
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
                "Provide verified links, maps, images for each reccomdation",
                "Verify all links are functional before including them.",
                "Organize information clearly with appropriate sections based on the query type."
            ],
            show_tool_calls=True,
            markdown=True,
            debug_mode=True
        )

    def generate_travel_plan(self, destination, present_location, start_date, end_date, budget, travel_style):
        prompt = f"""Act as a Personalized Travel Expert
You are a travel expert specializing in creating tailored, detailed travel plans. Design a comprehensive itinerary for a trip to {destination} spanning {duration} days, starting on {start_date} and ending on {end_date}.

Traveler Preferences:
Budget Level: {budget}
Travel Styles: {', '.join(travel_style)}
Your Task:
Provide a structured markdown response that includes the following elements:

🌞 Best Time to Visit:
 -Highlight seasonal considerations for visiting {destination}.
 -Day-by-day weather forecast from {start_date} to {end_date}
 -Alternative date suggestions if weather is unfavorable .Include source links for all weather data.
 -Offer clothing recommendations for each day based on weather forecasts of that particular day be accurate . For example:
    -Warm jackets and boots for cold, snowy days.
    -Light, breathable clothing for warm, sunny days.
    -Raincoats and umbrellas for rainy conditions.

🏨 Accommodation Recommendations:
 -Suggest accommodations within the {budget} range.
 -Include pros and cons, prices, amenities, and booking links.
 -Indicate the distance and travel time to major attractions. 
 -Format your response using markdown with clear headings (##) and bullet points. Use [text](url) format for hyperlinks. Verify all links are functional before including them.

🗺️ Day-by-Day Itinerary:
 -Create a detailed itinerary for each day, broken into specific time slots (e.g., "9:00 AM–12:00 PM: Visit [Attraction]").
 -Incorporate activities, attractions, and cultural experiences that align with the specified travel styles.
 -Include booking links, costs, and recommendations for optimizing time and enjoyment.
 -Include sites only if the sites exist 

🍽️ Culinary Highlights:
 -Recommend local cuisines, restaurants, and food experiences.
 -Provide suggestions based on the travel styles (e.g., street food, fine dining, or unique culinary tours).
 -Include price ranges, opening hours, and reservation links, where available.

💡 Practical Travel Tips:
 -List local and intercity transportation options (e.g., public transit, car rentals, taxis).
 -Provide advice on cultural etiquette, local customs, and safety tips.
 -Include a suggested daily budget breakdown for meals, transport, and activities.

💰 Estimated Total Trip Cost:
 -Provide an itemized expense breakdown by category:
 -Accommodation, transportation, meals, activities, and miscellaneous expenses.
 -Offer budget-saving tips specific to {budget} constraints.

🚂 Transportation Details:
 -Recommend transportation options from {present_location} to {destination}.
 -Include schedules, pricing, duration, and booking links for trains, buses, or flights.

Output Requirements:
 -Use clear, easy-to-read markdown with headings and bullet points for each section.
 -Provide source links, booking references, and maps wherever applicable.
 -Ensure all details are actionable and well-organized to facilitate ease of planning.
 -Verify all links are functional before including them 
 """
        response = self.agent.run(prompt)
        try:
            if hasattr(response, 'content'):
                clean_response = response.content.replace('∣', '|').replace('\n\n\n', '\n\n')
                return clean_response
            else:
                return str(response)
        except Exception as e:
            raise Exception(f"Error generating travel plan: {str(e)}")

    def answer_question(self, question, travel_plan, destination):
        prompt = f"""Using the context of this travel plan for {destination}:

{travel_plan}

Please answer this specific question: {question}

Guidelines for your response:
1. Focus specifically on answering the question asked
2. Reference relevant parts of the travel plan when applicable
3. Provide new information if the travel plan doesn't cover the topic
4. Include verified source links for any new information
5. Keep the response concise but comprehensive
6. Use markdown formatting for clarity

Format your response with appropriate headings and verify all included links."""

        response = self.agent.run(prompt)
        try:
            if hasattr(response, 'content'):
                return response.content.replace('∣', '|').replace('\n\n\n', '\n\n')
            else:
                return str(response)
        except Exception as e:
            raise Exception(f"Error answering question: {str(e)}")

    def update_travel_plan(self, present_location, extra_time, travel_plan):
        prompt = f"""
Update the following day-to-day travel itinerary:{travel_plan}
Current Situation:
The user is presently at {present_location}.
They wish to extend their stay at this location by {extra_time} hours.
Instructions:
Adjust Itinerary: Modify the time and schedule of activities in the Day-to-Day Itinerary starting from {present_location} to accommodate the extended stay.
Do not alter sections such as "Best Time to Visit," "Accommodation Recommendations," "Culinary Highlights," or "Practical Travel Tips."
Ensure that no extraneous sections of the itinerary are changed.
Rearrange or Remove Activities: If necessary, suggest alternatives for activities that need to be omitted or rescheduled.

Financial Impact:
Calculate and summarize the financial impact of these adjustments, including the total cost change (increase or decrease).
Provide a concise explanation of how the costs were recalculated.
Output Format:
Provide the updated Day-to-Day Itinerary in Markdown format.
Include a summary section at the end detailing:
Adjusted total cost and its breakdown.
Brief reasoning behind the cost adjustments.

"""

        response = self.agent.run(prompt)
        try:
            if hasattr(response, 'content'):
                return response.content.replace('∣', '|').replace('\n\n\n', '\n\n')
            else:
                return str(response)
        except Exception as e:
            raise Exception(f"Error updating travel plan: {str(e)}")


# Initialize session state
if 'travel_plan' not in st.session_state:
    st.session_state.travel_plan = None
if 'destination' not in st.session_state:
    st.session_state.destination = None
if 'weather_check' not in st.session_state:
    st.session_state.weather_check = False
if 'qa_expanded' not in st.session_state:
    st.session_state.qa_expanded = False

try:
    # Set API keys
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
    os.environ["SERP_API_KEY"] = os.getenv("SERP_API_KEY")

    # Initialize travel agent
    travel_agent = TravelAgent()

    # Sidebar configuration
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/200/airplane-take-off.png")
        st.title("Trip Settings")
        
        destination = st.text_input("🌍 Where would you like to go?", "")
        present_location = st.text_input("📍 What's your current location?", "")
        
        start_date = st.date_input("📅 Start Date", min_value=datetime.today())
        end_date = st.date_input("📅 End Date", min_value=start_date)
        
        if start_date and end_date:
            duration = (end_date - start_date).days + 1
        else:
            duration = 5
        
        budget = st.select_slider(
            "💰 What's your budget level?",
            options=["Budget", "Moderate", "Luxury"],
            value="Moderate"
        )
        
        all_styles = ["Culture", "Nature", "Adventure", "Relaxation", "Food", "Shopping", "Entertainment", "Scientific Events to Visit", "Tech Events to Visit"]
        selected_styles = st.multiselect(
            "🎯 Travel Style",
            ["All"] + all_styles,
            key="style_selector"
        )
        
        travel_style = all_styles if "All" in selected_styles else selected_styles

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

    if st.button("✨ Generate My Perfect Travel Plan", type="primary"):
        if destination:
            try:
                with st.spinner("🔍 Researching and planning your trip..."):
                    travel_plan = travel_agent.generate_travel_plan(
                        destination,
                        present_location,
                        start_date,
                        end_date,
                        budget,
                        travel_style
                    )
                    st.session_state.travel_plan = travel_plan
                    st.session_state.destination = destination
                    st.markdown(travel_plan)
            except Exception as e:
                st.error(f"Error generating travel plan: {str(e)}")
        else:
            st.warning("Please enter a destination")

    # Display current travel plan if it exists
    if st.session_state.travel_plan:
        with st.expander("📋 Current Travel Plan", expanded=False):
            st.markdown(st.session_state.travel_plan)

    # Q&A Section
    st.divider()
    qa_expander = st.expander("🤔 Ask a specific question about your destination or travel plan", 
                             expanded=st.session_state.qa_expanded)
    
    with qa_expander:
        if st.session_state.travel_plan:
            question = st.text_input("Your question:", placeholder="What would you like to know about your trip?")
            if st.button("Get Answer", key="qa_button"):
                if question:
                    with st.spinner("🔍 Finding answer..."):
                        try:
                            answer = travel_agent.answer_question(
                                question=question,
                                travel_plan=st.session_state.travel_plan,
                                destination=st.session_state.destination
                            )
                            st.markdown(answer)
                        except Exception as e:
                            st.error(f"Error getting answer: {str(e)}")
                else:
                    st.warning("Please enter a question")
        else:
            st.warning("Please generate a travel plan first before asking questions.")

    # Update Plan Section
    st.divider()
    st.header("🔄 Update Your Ongoing Plan")

    if st.session_state.travel_plan:
        current_location = st.text_input("📍 Your current location:", "")
        extra_time = st.number_input("⏳ Additional time (in hours):", min_value=0, step=1)

        if st.button("🔄 Update My Travel Plan"):
            if current_location and extra_time > 0:
                with st.spinner("🔄 Updating your travel plan..."):
                    try:
                        updated_plan = travel_agent.update_travel_plan(
                            present_location=current_location,
                            extra_time=extra_time,
                            travel_plan=st.session_state.travel_plan
                        )
                        st.session_state.travel_plan = updated_plan
                        st.markdown(updated_plan)
                    except Exception as e:
                        st.error(f"Error updating plan: {str(e)}")
            else:
                st.warning("Please provide both current location and additional time.")
    else:
        st.warning("Please generate a travel plan first before updating.")
    
    
    # Update the weather monitor section in the main UI
    st.divider()
    if st.session_state.travel_plan:
        st.subheader("🌤️ Weather Monitor and Plan Adjustment")

        weather_check_col1, weather_check_col2 = st.columns(2)

        with weather_check_col1:
            current_location = st.text_input(
                "📍 Your current location in the itinerary:",
                help="Enter your current location from the trip itinerary"
            )

        with weather_check_col2:
            if st.button("Check Weather & Update Plan"):
                if not current_location:
                    st.warning("Please enter your current location")
                else:
                    weather_data = get_weather(destination)

                    if weather_data.get('success', False):
                        # Create weather info container
                        weather_container = st.container()
                        with weather_container:
                            st.markdown(f"""
                                ### Current Weather in {destination}

                                🌡️ **Temperature:** {weather_data['temperature']}°C  
                                🌥️ **Conditions:** {weather_data['condition'].capitalize()}  
                                🌍 **Country:** {weather_data['country']}
                            """) 

                            if weather_data['needs_update']:
                                st.warning("""
                                    ### ⚠️ Weather Alert
                                    Current conditions may affect your planned activities. 
                                    Here's an adjusted itinerary taking into account the weather:
                                """)
 
                                # Create columns for plan comparison
                                original_col, updated_col = st.columns(2)

                                with original_col:
                                    st.markdown("### Original Plan")
                                    with st.expander("View Original Plan", expanded=False):
                                        st.markdown(st.session_state.travel_plan)

                                with updated_col:
                                    st.markdown("### Weather-Adjusted Plan")
                                    with st.spinner("Creating weather-adjusted itinerary..."):
                                        # Get updated plan with weather considerations
                                        updated_plan = travel_agent.update_travel_plan(
                                            present_location=current_location,
                                            extra_time=2,  # Adding buffer time for weather
                                            travel_plan=st.session_state.travel_plan
                                        )

                                        # Show the changes
                                        st.markdown(updated_plan)

                                # Add action buttons
                                action_col1, action_col2 = st.columns(2)
                                with action_col1:
                                    if st.button("✅ Accept Updated Plan", type="primary"):
                                        st.session_state.travel_plan = updated_plan
                                        st.success("Travel plan updated successfully!")

                                with action_col2:
                                    if st.button("❌ Keep Original Plan"):
                                        st.info("Keeping original travel plan.")

                                # Add weather recommendations
                                st.markdown("""
                                    ### 👔 Weather-Based Recommendations

                                    Based on current conditions, consider:
                                """)

                                if weather_data['temperature'] < 5:
                                    st.markdown("- 🧥 Pack warm layers and winter accessories")
                                    st.markdown("- ⛄ Check indoor alternatives for outdoor activities")
                                elif weather_data['temperature'] > 25:
                                    st.markdown("- 👕 Pack light, breathable clothing")
                                    st.markdown("- 🧴 Bring sun protection")

                                if 'rain' in weather_data['condition'] or 'storm' in weather_data['condition']:
                                    st.markdown("- ☔ Bring rain gear and waterproof accessories")
                                    st.markdown("- 🏛️ Consider indoor backup activities")
                            else:
                                st.success("""
                                    ### ✅ Perfect Weather!
                                    Current conditions are favorable for your planned activities.
                                    Continue with your original itinerary.
                                """)
                    else:
                        st.error(f"Error checking weather: {weather_data.get('error', 'Unknown error')}")
            else:
              st.warning("Please generate a travel plan first before checking weather conditions.")

except Exception as e:
    st.error(f"Application Error: {str(e)}") 