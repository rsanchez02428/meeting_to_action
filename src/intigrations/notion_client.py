""" 
notion_client.py - Pushes action items to a Notion database.

CONCEPT: Notion has a REST API. We send HTTP requests to create
new "pages" (rows) in a database. Each action item becomes a task
in the team's Notion board.

The Notion API uses a specific format for different property types
(title, rich_text, date, select). This is documented at:
https://developers.notion.com/reference/property-value-object
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

NOION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"  # API version
}


def create_action_item(item: dict) -> dict:
    """ 
    Create a single action item as a page in a Notion database.

    CONCEPT: In Notion's API, a "database" is like a spreadsheet.
    Eachy row is a "page". Each column is a "property". We create
    new pages by sending a POST request with the property values.
    """

    # Build the properties object matching your Notion database columns
    properties = {
        "Task": {
            "title": [{"text": {"content": item.get("task", [])}}]
        },
        "Owner": {
            "rich_text": [{"text": {"content": item.get("owner", [])}}]
        },
        "Priority": {
            "select": {"name": item.get("priority", [])}
        }, 
        "Status": {
            "select": {"name": "To-Do"}
        },
        "Context": {
            "rich_text": [{"text": {"content": item.get("context", "")}}]
        }
    }

    # Add deadline if specific and it's a recognizable date
    deadline = item.get("deadline", "Not specified")
    if deadline not in ["Not specified", "TBD", ""]:
        # Note: Notion expects ISO date format (YYYY-MM-DD)
        # For now, store as text. A production system would parse relative
        # dates ("next Friday") into actuale dates.
        properties["Deadline"] = {
            "rich_text": [{"text": {"content": deadline}}]
        }
    
    # Create the page
    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers = NOION_HEADERS,
        json = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": properties 
        }
    )

    if response.status_code == 200:
        page = response.json()
        print(f" Created: {item.get('task', 'Untitled')} - {page['url']}")
        return page
    else:
        print(f" Error creating task: {response.status_code} - {response.text[:200]}")
        return None

def push_action_items(data: dict) -> list:
    """Push all action items from the meeting extraction to Notion."""

    action_items = data.get("action_items", [])

    if not action_items: 
        print("No action items to push.")
        return []
    
    print(f"Pushing {len(action_items)} action items to Notion...")

    results = []
    for item in action_items:
        result = create_action_item(item)
        if result: 
            results.append(result)
    
    print(f"Successfullt created {len(results)}/{len(action_items)} tasks.")
    return results

# === TEST IT ====

if __name__ == "__main__":
    import json

    with open(r"outputs\verifications\sample_3\sample_3_extraction_v2_verification_v2.json") as f:
        data = json.load(f)

    success = push_action_items(data)

    if success:
        print("Check your 'Task' database!")
