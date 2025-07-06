#!/usr/bin/env python3
"""
Simple MCP Server for GitHub Repository Creation
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GitHub configuration - load from environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    logger.error("GITHUB_TOKEN not found in environment variables. Please set it in your .env file or environment.")
    sys.exit(1)
GITHUB_API_URL = "https://api.github.com/user/repos"

class MCPServer:
    def __init__(self):
        self.server_name = "github-repo-creator"
        self.server_version = "1.0.0"
        
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP messages"""
        method = message.get("method")
        msg_id = message.get("id")
        
        if method == "initialize":
            return self.handle_initialize(message, msg_id)
        elif method == "tools/list":
            return self.handle_list_tools(msg_id)
        elif method == "tools/call":
            return await self.handle_call_tool(message, msg_id)
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    def handle_initialize(self, message: Dict[str, Any], msg_id: int) -> Dict[str, Any]:
        """Handle initialization request"""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": self.server_name,
                    "version": self.server_version
                }
            }
        }
    
    def handle_list_tools(self, msg_id: int) -> Dict[str, Any]:
        """Handle tools/list request"""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "create_github_repository",
                        "description": "Create a new GitHub repository",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the repository to create"
                                },
                                "private": {
                                    "type": "boolean",
                                    "description": "Whether the repository should be private",
                                    "default": False
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Description of the repository"
                                },
                                "auto_init": {
                                    "type": "boolean",
                                    "description": "Initialize repository with README",
                                    "default": True
                                }
                            },
                            "required": ["name"]
                        }
                    },
                    {
                        "name": "delete_github_repository",
                        "description": "Delete a GitHub repository",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the repository to delete"
                                }
                            },
                            "required": ["name"]
                        }
                    },
                    {
                        "name": "list_calendar_events",
                        "description": "List upcoming Google Calendar events",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "maxResults": {
                                    "type": "integer",
                                    "description": "Maximum number of events to return",
                                    "default": 10
                                }
                            }
                        }
                    },
                    {
                        "name": "create_calendar_events",
                        "description": "Create a Google Calendar event",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "summary": {"type": "string", "description": "Event title"},
                                "start": {"type": "object", "description": "Start time object (dateTime or date)"},
                                "end": {"type": "object", "description": "End time object (dateTime or date)"}
                            },
                            "required": ["summary", "start", "end"]
                        }
                    },
                    {
                        "name": "update_calendar_events",
                        "description": "Update a Google Calendar event",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "eventId": {"type": "string", "description": "ID of the event to update"},
                                "summary": {"type": "string", "description": "Event title"},
                                "start": {"type": "object", "description": "Start time object (dateTime or date)"},
                                "end": {"type": "object", "description": "End time object (dateTime or date)"}
                            },
                            "required": ["eventId"]
                        }
                    },
                    {
                        "name": "delete_calendar_events",
                        "description": "Delete a Google Calendar event",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "eventId": {"type": "string", "description": "ID of the event to delete"}
                            },
                            "required": ["eventId"]
                        }
                    },
                    {
                        "name": "list_emails",
                        "description": "List Gmail messages using Google Calendar authentication",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "maxResults": {
                                    "type": "integer",
                                    "description": "Maximum number of emails to return",
                                    "default": 10
                                },
                                "query": {
                                    "type": "string",
                                    "description": "Gmail search query (optional)"
                                }
                            }
                        }
                    },
                    {
                        "name": "send_email",
                        "description": "Send an email using Gmail API",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "to": {"type": "string", "description": "Recipient email address"},
                                "subject": {"type": "string", "description": "Email subject"},
                                "body": {"type": "string", "description": "Email body content"}
                            },
                            "required": ["to", "subject", "body"]
                        }
                    },
                    {
                        "name": "read_email",
                        "description": "Read a specific email by ID",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "emailId": {"type": "string", "description": "ID of the email to read"}
                            },
                            "required": ["emailId"]
                        }
                    },
                    {
                        "name": "delete_email",
                        "description": "Delete a Gmail message",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "emailId": {"type": "string", "description": "ID of the email to delete"}
                            },
                            "required": ["emailId"]
                        }
                    }
                ]
            }
        }
    
    async def handle_call_tool(self, message: Dict[str, Any], msg_id: int) -> Dict[str, Any]:
        """Handle tools/call request"""
        params = message.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "create_github_repository":
            result = await self.create_github_repository(arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        if tool_name == "delete_github_repository":
            result = await self.delete_github_repository(arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif tool_name == "list_calendar_events":
            result = await self.list_calendar_events(arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif tool_name == "create_calendar_events":
            result = await self.create_calendar_events(arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif tool_name == "update_calendar_events":
            result = await self.update_calendar_events(arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif tool_name == "delete_calendar_events":
            result = await self.delete_calendar_events(arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif tool_name == "list_emails":
            result = await self.list_emails(arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif tool_name == "send_email":
            result = await self.send_email(arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif tool_name == "read_email":
            result = await self.read_email(arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        elif tool_name == "delete_email":
            result = await self.delete_email(arguments)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }
    
    async def create_github_repository(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub repository"""
        try:
            repo_name = arguments.get("name")
            if not repo_name:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Error: Repository name is required"
                        }
                    ],
                    "isError": True
                }
            
            # Prepare GitHub API request
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            }
            
            json_data = {
                "name": repo_name,
                "private": arguments.get("private", False),
                "auto_init": arguments.get("auto_init", True)
            }
            
            if "description" in arguments:
                json_data["description"] = arguments["description"]
            
            # Call GitHub API
            async with httpx.AsyncClient() as client:
                response = await client.post(GITHUB_API_URL, json=json_data, headers=headers)
            
            if response.status_code == 201:
                repo_data = response.json()
                repo_url = repo_data.get("html_url", "Unknown")
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"✅ Successfully created GitHub repository '{repo_name}'!\n\nRepository URL: {repo_url}\nClone URL: {repo_data.get('clone_url', 'Unknown')}"
                        }
                    ]
                }
            else:
                error_data = response.json()
                error_message = error_data.get("message", "Unknown error")
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"❌ Failed to create repository: {error_message} (Status: {response.status_code})"
                        }
                    ],
                    "isError": True
                }
                
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Error creating repository: {str(e)}"
                    }
                ],
                "isError": True
            }

    async def delete_github_repository(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a GitHub repository"""
        try:
            repo_name = arguments.get("name")
            if not repo_name:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Error: Repository name is required"
                        }
                    ],
                    "isError": True
                }
            
            # Prepare GitHub API request
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            }
            
            # Get the username from the token
            async with httpx.AsyncClient() as client:
                # First, get user info to get the username
                user_response = await client.get("https://api.github.com/user", headers=headers)
                if user_response.status_code != 200:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"❌ Failed to get user info: {user_response.status_code}"
                            }
                        ],
                        "isError": True
                    }
                
                user_data = user_response.json()
                username = user_data.get("login")
                
                # Now delete the repository using the full path
                delete_url = f"https://api.github.com/repos/{username}/{repo_name}"
                response = await client.delete(delete_url, headers=headers)
            
            if response.status_code == 204:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"✅ Successfully deleted GitHub repository '{repo_name}'"
                        }
                    ]
                }
            else:
                error_data = response.json()
                error_message = error_data.get("message", "Unknown error")
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"❌ Failed to delete repository: {error_message} (Status: {response.status_code})"
                        }
                    ],
                    "isError": True
                }
                
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Error deleting repository: {str(e)}"
                    }
                ],
                "isError": True
            }

    async def list_calendar_events(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List upcoming Google Calendar events with IDs"""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        max_results = arguments.get("maxResults", 10)
        try:
            creds = Credentials.from_authorized_user_file('/Users/amanueltefera/Desktop/untitled folder 3/token.json')
            service = build('calendar', 'v3', credentials=creds)
            events_result = service.events().list(calendarId='primary', maxResults=max_results).execute()
            events = events_result.get('items', [])
            
            if not events:
                return {"content": [{"type": "text", "text": "No calendar events found."}]}
            
            output = []
            for event in events:
                event_id = event.get('id', 'No ID')
                summary = event.get('summary', 'No Title')
                start = event.get('start', {})
                
                # Format start time
                if 'dateTime' in start:
                    start_time = start['dateTime']
                elif 'date' in start:
                    start_time = start['date']
                else:
                    start_time = 'No start time'
                
                output.append(f"📅 {summary}\nStart: {start_time}\nID: {event_id}\n{'─' * 50}")
            
            return {"content": [{"type": "text", "text": "\n".join(output)}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}
    
    async def delete_calendar_events(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a Google Calendar event"""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        
        event_id = arguments.get("eventId")
        if not event_id:
            return {"content": [{"type": "text", "text": "Error: Event ID is required"}], "isError": True}
        
        try:
            creds = Credentials.from_authorized_user_file('/Users/amanueltefera/Desktop/untitled folder 3/token.json')
            service = build('calendar', 'v3', credentials=creds)
            service.events().delete(calendarId='primary', eventId=event_id).execute()   
            return {"content": [{"type": "text", "text": f"✅ Successfully deleted event: {event_id}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"❌ Error deleting event: {str(e)}"}], "isError": True}

    async def create_calendar_events(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Google Calendar event"""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        
        try:
            creds = Credentials.from_authorized_user_file('/Users/amanueltefera/Desktop/untitled folder 3/token.json')
            service = build('calendar', 'v3', credentials=creds)
            event = service.events().insert(calendarId='primary', body=arguments).execute() 
            
            event_id = event.get('id', 'No ID')
            summary = event.get('summary', 'No Title')
            
            return {"content": [{"type": "text", "text": f"✅ Successfully created event: {summary}\nEvent ID: {event_id}"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"❌ Error creating event: {str(e)}"}], "isError": True}
        
    async def update_calendar_events(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Google Calendar event"""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        
        event_id = arguments.get("eventId")
        if not event_id:
            return {"content": [{"type": "text", "text": "Error: Event ID is required"}], "isError": True}  
        
        try:
            creds = Credentials.from_authorized_user_file('/Users/amanueltefera/Desktop/untitled folder 3/token.json')
            service = build('calendar', 'v3', credentials=creds)
            event = service.events().update(calendarId='primary', eventId=event_id, body=arguments).execute()
            return {"content": [{"type": "text", "text": f"✅ Successfully updated event: {event.get('summary', 'No Title')}"}]}    
        except Exception as e:
            return {"content": [{"type": "text", "text": f"❌ Error updating event: {str(e)}"}], "isError": True}

    async def list_emails(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List Gmail messages using Google Calendar authentication"""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        import base64
        import email

        max_results = arguments.get("maxResults", 10)
        query = arguments.get("query", "")
        
        try:
            creds = Credentials.from_authorized_user_file('/Users/amanueltefera/Desktop/untitled folder 3/token.json')
            service = build('gmail', 'v1', credentials=creds)
            
            # List messages
            if query:
                messages_result = service.users().messages().list(
                    userId='me', 
                    maxResults=max_results,
                    q=query
                ).execute()
            else:
                messages_result = service.users().messages().list(
                    userId='me', 
                    maxResults=max_results
                ).execute()
            
            messages = messages_result.get('messages', [])
            
            if not messages:
                return {"content": [{"type": "text", "text": "No emails found."}]}
            
            output = []
            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                
                # Extract headers
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                email_id = message['id']
                
                output.append(f"📧 {subject}\nFrom: {sender}\nDate: {date}\nID: {email_id}\n{'─' * 50}")
            
            return {"content": [{"type": "text", "text": "\n".join(output)}]}
            
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}

    async def send_email(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Send an email using Gmail API"""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        import base64
        from email.mime.text import MIMEText

        to = arguments.get("to")
        subject = arguments.get("subject")
        body = arguments.get("body")
        
        if not all([to, subject, body]):
            return {"content": [{"type": "text", "text": "Error: to, subject, and body are required"}], "isError": True}
        
        try:
            creds = Credentials.from_authorized_user_file('/Users/amanueltefera/Desktop/untitled folder 3/token.json')
            service = build('gmail', 'v1', credentials=creds)
            
            # Create message
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send the message
            sent_message = service.users().messages().send(
                userId='me', 
                body={'raw': raw_message}
            ).execute()
            
            message_id = sent_message.get('id', 'No ID')
            
            return {"content": [{"type": "text", "text": f"✅ Email sent successfully!\nMessage ID: {message_id}"}]}
            
        except Exception as e:
            return {"content": [{"type": "text", "text": f"❌ Error sending email: {str(e)}"}], "isError": True}

    async def read_email(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Read a specific email by ID"""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        import base64
        import email

        email_id = arguments.get("emailId")
        if not email_id:
            return {"content": [{"type": "text", "text": "Error: Email ID is required"}], "isError": True}
        
        try:
            creds = Credentials.from_authorized_user_file('/Users/amanueltefera/Desktop/untitled folder 3/token.json')
            service = build('gmail', 'v1', credentials=creds)
            
            # Get the message
            message = service.users().messages().get(userId='me', id=email_id).execute()
            
            # Extract headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            # Extract body
            body = ""
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            else:
                if message['payload']['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
            
            if not body:
                body = "No text content found"
            
            output = f"📧 {subject}\nFrom: {sender}\nDate: {date}\nID: {email_id}\n\n{body}"
            
            return {"content": [{"type": "text", "text": output}]}
            
        except Exception as e:
            return {"content": [{"type": "text", "text": f"❌ Error reading email: {str(e)}"}], "isError": True}

    async def delete_email(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a Gmail message"""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        
        email_id = arguments.get("emailId")
        if not email_id:
            return {"content": [{"type": "text", "text": "Error: Email ID is required"}], "isError": True}
        
        try:
            creds = Credentials.from_authorized_user_file('/Users/amanueltefera/Desktop/untitled folder 3/token.json')
            service = build('gmail', 'v1', credentials=creds)
            
            # Delete the message
            service.users().messages().delete(userId='me', id=email_id).execute()
            
            return {"content": [{"type": "text", "text": f"✅ Successfully deleted email: {email_id}"}]}
            
        except Exception as e:
            return {"content": [{"type": "text", "text": f"❌ Error deleting email: {str(e)}"}], "isError": True}
        

async def main():
    """Main function to run the MCP server"""
    server = MCPServer()
    
    print(f"🚀 Starting {server.server_name} MCP server...", file=sys.stderr)
    print("Ready to receive MCP messages on stdin/stdout", file=sys.stderr)
    
    # Read from stdin, write to stdout
    while True:
        try:
            # Read a line from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            # Parse the JSON message
            message = json.loads(line.strip())
            
            # Handle the message
            response = await server.handle_message(message)
            
            # Send the response
            print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }), flush=True)
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }), flush=True)

if __name__ == "__main__":
    asyncio.run(main()) 