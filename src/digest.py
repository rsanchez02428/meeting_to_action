""" 
digest.py - Weekly meeting digest generator.

CONCEPT: Summarizing across MULTIPLE inputs. Instead of analyzing one meeting,
you're synthesizing patterns across many meetings in a week.

This is valuable because it surfaces:
- Overdue action items (assigned Monday, still not done Friday)
- Recurring topics (the same issue discussed 3 weeks in a row)
- Workload imbalance (one person assigned 15 items, another assigned 2)
"""

import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_weekly_digest(meeting_results: list[dict]) -> str:
    """ 
    Generate a weekly digest from multiple meeting extractions.

    Parameters:
    -----------
    meeting_results : list[dict]
        List of verified extraction results from the week's meetings
    """

    meetings_json = json.dump(meeting_results, indent=2)

    prompt = prompt = f"""You are an executive assistant preparing a weekly meeting digest 
for a leadership team. You have the extracted data from all meetings 
held this week.

MEETING DATA:
{meetings_json}

Generate a concise weekly digest with these sections:

1. WEEK AT A GLANCE (2-3 sentences summarizing the week's key themes)

2. KEY DECISIONS (bullet list of all decisions made across all meetings)

3. ACTION ITEMS TRACKER
   - NEW this week: list all new action items with owners
   - OVERDUE: any items from previous weeks still not done (if trackable)
   - Workload distribution: count of items per person

4. OPEN QUESTIONS (consolidated — remove duplicates across meetings)

5. PATTERNS & FLAGS
   - Topics discussed in multiple meetings (possible stalled issues)
   - People overloaded with action items
   - Decisions that might conflict with each other
   - Anything that seems like it's falling through the cracks

6. RECOMMENDED FOCUS FOR NEXT WEEK (2-3 priorities based on the data)

Format this as a clean, readable Slack message using markdown. 
Keep it under 500 words. Be direct and actionable."""
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text