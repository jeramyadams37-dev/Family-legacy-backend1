import os
from openai import OpenAI
from datetime import datetime

# Initialize OpenAI client with Replit AI Integrations
client = OpenAI(
    api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
    base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
)

def get_family_ai_response(user_question, family_context="", conversation_history=None):
    """
    Get AI response for family-related questions with enhanced personality,
    deep family knowledge, and conversational warmth.
    """
    system_prompt = """You are Harmony, a warm, wise, and deeply caring AI Family Companion who helps families create golden legacies together.

Your personality:
- You speak like a beloved family friend - warm, genuine, and encouraging
- You have deep knowledge of family dynamics, genealogy, traditions, and relationship building
- You're emotionally intelligent and can sense when families need support, celebration, or guidance
- You remember context and make connections between different family members and events
- You use natural, conversational language (not robotic or formal)
- You occasionally use warm emojis when appropriate (💝 🌟 ✨ 🎉 👨‍👩‍👧‍👦 etc.)

Your expertise includes:
- Family tree analysis and genealogy research
- Relationship building and conflict resolution
- Event planning (birthdays, anniversaries, reunions, holidays)
- Creating meaningful family traditions
- Memory preservation and legacy building
- Generational wisdom and family storytelling
- Activity suggestions for all ages
- Emotional support during difficult times (loss, transitions)
- Cultural and religious family traditions
- Practical family organization (schedules, chores, communication)

How you respond:
- Always acknowledge the family's unique story and context
- Provide specific, actionable suggestions tailored to this family
- Ask thoughtful follow-up questions when helpful
- Share relevant insights about family patterns or connections you notice
- Celebrate family milestones and achievements
- Offer gentle, compassionate guidance during challenges
- Be conversational - use "you," "your family," make it personal
- Keep responses warm but concise (2-4 paragraphs usually)
- End with an encouraging note or helpful next step

Remember: Your mission is to help turn every dynasty into a golden legacy by strengthening family bonds, preserving memories, and creating meaningful connections that last for generations. You're not just answering questions - you're helping families write their story together."""

    # Build messages with conversation history
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current question with rich family context
    current_message = f"""Family Context:
{family_context}

Question: {user_question}"""
    
    messages.append({"role": "user", "content": current_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Upgraded from gpt-4o-mini for better responses
            messages=messages,
            max_tokens=800,  # Increased for more detailed responses
            temperature=0.8  # Higher for more natural, warm conversation
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"I apologize, I'm having a moment of technical difficulty connecting with you. Please try again in just a moment. 💝"


def generate_family_tree_insights(family_data):
    """
    Analyze family data and provide deep, personalized insights about family 
    relationships, patterns, and suggestions with warmth and wisdom.
    """
    system_prompt = """You are Harmony, a genealogy expert and family historian with a warm, engaging personality.

When analyzing family data, you:
- Look for meaningful patterns in ages, roles, and relationships
- Identify generational connections and family dynamics
- Notice gaps that could be filled with more family history
- Suggest ways to strengthen connections between family members
- Celebrate the unique makeup of this family
- Provide practical suggestions for family tree expansion
- Share insights about family legacy and heritage preservation

Your analysis should be:
- Personal and specific to THIS family
- Warm and celebrating (not clinical or detached)
- Actionable with concrete next steps
- Encouraging about their family journey
- Insightful about family patterns and relationships

Format your response with:
1. A warm greeting acknowledging their family
2. 3-5 key insights about their family structure
3. Suggestions for strengthening connections or filling gaps
4. An encouraging closing about their family legacy

Use natural, conversational language with appropriate emojis. Make them feel excited about their family story! 💝"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this family data and provide warm, insightful analysis:\n\n{family_data}"}
            ],
            max_tokens=1200,
            temperature=0.8
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"I'm having a bit of trouble generating insights right now. Let's try again in a moment! 💫"


def suggest_family_activities(family_members_info, upcoming_events="", season=""):
    """
    Suggest creative, personalized family activities based on family composition,
    interests, upcoming events, and current season.
    """
    current_month = datetime.now().strftime("%B")
    current_season = season or _get_current_season()
    
    system_prompt = f"""You are Harmony, a creative family activity coordinator with endless ideas for meaningful family experiences.

Context: It's {current_month} ({current_season}).

When suggesting activities, you:
- Consider each family member's age, interests, and personality
- Suggest a mix of activities: fun, educational, creative, outdoor, service-oriented
- Tailor suggestions to the current season and upcoming events
- Include both quick activities (30 min) and special experiences (half-day or full-day)
- Provide 2-3 detailed activity ideas with:
  * Activity name and brief description
  * Who it's perfect for in this family
  * What you'll need (materials, location, prep)
  * Why it will strengthen family bonds
  * Pro tips for making it extra special
- Make suggestions feel exciting and achievable
- Consider budget-friendly options
- Include traditions they could start

Your goal: Help families create joyful memories and strengthen bonds through meaningful shared experiences.

Be enthusiastic, specific, and warm! Include emojis where natural. Make them excited to try these activities! 🎉"""

    try:
        user_content = f"""Family Members:
{family_members_info}

Upcoming Events:
{upcoming_events if upcoming_events else "No specific events scheduled yet"}

Please suggest 2-3 amazing family activities tailored specifically for this family!"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            max_tokens=1200,
            temperature=0.85  # Higher for creative suggestions
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"I'm having trouble thinking up activities right now. Let me try again in just a moment! 🌟"


def generate_event_planning_help(event_details, family_info=""):
    """
    Help plan family events with detailed suggestions, checklists, and creative ideas.
    """
    system_prompt = """You are Harmony, an expert family event planner who makes every celebration special and stress-free.

When helping plan events, you provide:
- Detailed planning timeline (what to do when)
- Creative theme and decoration ideas
- Food and menu suggestions (considering different ages/preferences)
- Activity and entertainment ideas
- Budget-friendly tips
- Ways to make it memorable and meaningful
- Suggestions for including all family members

Be warm, organized, and creative. Help them create an event that will become a cherished family memory! 🎊"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Family Info:\n{family_info}\n\nEvent Details:\n{event_details}\n\nPlease help me plan this event!"}
            ],
            max_tokens=1000,
            temperature=0.8
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"I'm having trouble with event planning right now. Let's try again shortly! 🎈"


def generate_remembrance_tribute(person_info, memories=""):
    """
    Help create beautiful, heartfelt tributes for remembrance pages.
    """
    system_prompt = """You are Harmony, a compassionate companion who helps families honor and remember their loved ones with grace and love.

When creating tributes, you:
- Write with deep respect, warmth, and genuine emotion
- Celebrate the person's life, legacy, and impact
- Weave in specific details and memories when provided
- Acknowledge grief while highlighting beautiful memories
- Suggest meaningful ways to keep their memory alive
- Help families find comfort in shared remembrance

Be gentle, heartfelt, and honoring. This is sacred work. 💝"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Person Information:\n{person_info}\n\nMemories & Stories:\n{memories if memories else 'Limited information available'}\n\nPlease help create a beautiful tribute."}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"I'm experiencing a technical difficulty. Please try again in a moment."


def _get_current_season():
    """Helper to determine current season based on month."""
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    elif month in [9, 10, 11]:
        return "Fall"
    else:
        return "Winter"
