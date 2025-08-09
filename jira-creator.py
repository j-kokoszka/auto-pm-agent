import requests
import json
import os

# Define file names
CONFIG_FILE = 'config.json'
TASKS_FILE = 'tasks.json'

# --- Load configuration from config.json ---
if not os.path.exists(CONFIG_FILE):
    print(f"Error: The configuration file '{CONFIG_FILE}' was not found.")
    exit()

try:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    jira_url = config.get("jira_url")
    api_token = config.get("api_token")
    user_email = config.get("user_email")
    project_key = config.get("project_key")

    if not all([jira_url, api_token, user_email, project_key]):
        print(f"Error: Missing one or more required fields in '{CONFIG_FILE}'.")
        exit()

except (json.JSONDecodeError, IOError) as e:
    print(f"Error reading or parsing '{CONFIG_FILE}': {e}")
    exit()

# --- Load tasks from tasks.json ---
if not os.path.exists(TASKS_FILE):
    print(f"Error: The tasks file '{TASKS_FILE}' was not found.")
    exit()

try:
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
except (json.JSONDecodeError, IOError) as e:
    print(f"Error reading or parsing '{TASKS_FILE}': {e}")
    exit()

# --- Main logic for creating Jira issues ---
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}
auth = requests.auth.HTTPBasicAuth(user_email, api_token)
api_endpoint = f"{jira_url}/rest/api/3/issue"
created_issues_map = {}

for task in tasks:
    summary = task.get("summary")
    description_text = task.get("description")
    issue_type = task.get("issue_type", "Task")
    parent_summary = task.get("parent_summary")

    if not summary:
        print("Skipping issue due to missing 'summary'.")
        continue

    description_payload = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "text": description_text if description_text else "",
                        "type": "text"
                    }
                ]
            }
        ]
    }
    
    fields = {
        "project": {
            "key": project_key
        },
        "summary": summary,
        "description": description_payload,
        "issuetype": {
            "name": issue_type
        }
    }
    
    if parent_summary:
        parent_key = created_issues_map.get(parent_summary)
        if parent_key:
            fields['parent'] = {
                "key": parent_key
            }
        else:
            print(f"Error: Parent '{parent_summary}' for issue '{summary}' not yet created or does not exist. Skipping link.")
    
    payload = json.dumps({"fields": fields})

    try:
        response = requests.post(
            api_endpoint,
            data=payload,
            headers=headers,
            auth=auth
        )

        if response.status_code == 201:
            issue_key = response.json()['key']
            print(f"Issue '{summary}' (Type: {issue_type}) created successfully! Key: {issue_key}")
            created_issues_map[summary] = issue_key
        else:
            print(f"Error creating issue '{summary}'. Status code: {response.status_code}")
            print(f"Server response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending the request for '{summary}': {e}")
