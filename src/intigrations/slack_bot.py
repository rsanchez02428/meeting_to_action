""" 
slack_bot.py - Delivers meeting summaries and action items to Slack.

CONCEPT: The value of this system isn't just the extraction - it's 
the delivery. Meeting notes sitting in a JSON file help nobody.
Pushing them to where the team already works (Slack) is what makes 
this system actually useful.
"""

import os
from slack_sdk import WebClient 
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

def format_meeting_summary(data: dict) -> str:
    """
    Format extracted meeting data into Slack Block Kit messages.
    
    CONCEPT: Slack Block Kit is a JSON-based framework for building 
    rich messages. Instead of plain text, you can create formatted
    messages with headers, sections, bullet points, and dividers.

    Reference: https://api.slack.com/block-kit

    We return a list of "blocks" - Slack's building blocks for messages.
    """
    blocks = []

    # Header
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": "Meeting Summary"}
    })

    # Summary
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Summary:* {data.get('meeting_summary', 'No summary available')}"
        }
    })

    blocks.append({"type": "divider"})

    # Decisions
    decisions = data.get("decisions", [])
    if decisions:
        decision_text = "*Decisions Made:*\n"
        for d in decisions:
            decision_text += f"- {d['decision']}\n"
        blocks.append({
            "type": "section", 
            "text": {"type": "mrkdwn", "text": decision_text}
        })

    # Action Items
    action_items = data.get("action_items", [])
    if action_items:
        blocks.append({"type": "divider"})
        action_text = "*Acttion Items:*\n"
        for item in action_items:
            priority = item.get("priority", []),
            action_text += ( 
                f"*{item['task']}*\n"
                f"     {item.get('owner', [])} "
                f"| {item.get("deadline", [])}\n"
            )
        blocks.append({
            "type": "section", 
            "text": {"type": "mrkdwn", "text": action_text}
        })

    # Open Questions
    questions = data.get("open_questions", [])
    if questions:
        blocks.append({"type": "divider"})
        q_text = "Open Questions:*\n"
        for q in questions:
            q_text += f" - {q['question']}\n"
        blocks.append({
            "type": "section", 
            "text": {"type": "mrkdwn", "text": q_text}
        })
    
    return blocks


def send_to_slack(channel: str, data: dict) -> bool:
    """
    Send formatted meeting summary to a Slack channel.
    
    Parameters:
    -----------
    channel : str
        Channel name (e.g., "#meeting-notes") or channel ID 
    data : dict
        The verified extraction data

    Returns:
    --------
    bool : True if sent successfully

    LEARNING NOTE: Always handle API errors gracefully. Slack might 
    be down, the channel might not exist, or the bot might not have 
    permission. Your code should never crash from an integration failure.
    """
    blocks = format_meeting_summary(data)

    try:
        response = slack_client.chat_postMessage(
            channel=channel, 
            text="Meeting summary posted", # Fallback for notifications
            blocks=blocks
        )
        print(f"Message sent to {channel}: {response['ts']}")
        return True
    
    except SlackApiError as e:
        error_msg = e.response["error"]

        # Commone errors and their fixes
        if error_msg == "channel_not_found":
            print(f"Error: Channel '{channel}' not found. Check the channel name.")
        elif error_msg == "not_in_channel":
            print(f"Error: Bot not in '{channel}'. Invite it with /invite @Meeting Action Bot")
        elif error_msg == "invalid_auth":
            print("ErrorL INvalid Slack token. Check your SLACK_BOT_TOKEN in .env")
        else:
            print(f"Slack API Error: {error_msg}")
        
        return False


# === TEST IT ===
if __name__ == "__main__":
    import json

    with open("outputs/verifications/outputs/verifications/sample_1/sample_1_extraction_v2_verification_v2.json") as f:
        data = json.load(f)

    # Change this to test channel
    success = send_to_slack("#new-channel", data)

    if success:
        print("Check your Slack channel!")
        
