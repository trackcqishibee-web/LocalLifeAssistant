#!/usr/bin/env python3
"""
Local Life Assistant CLI
Interactive command-line interface for the local life assistant
"""

import asyncio
import httpx
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.markdown import Markdown
from typing import List, Dict, Any
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.models import ChatMessage, ChatRequest

class AssistantCLI:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.console = Console()
        self.conversation_history: List[ChatMessage] = []
        self.current_llm_provider = "openai"
        self.available_providers = ["openai", "anthropic", "ollama"]
        
    def print_welcome(self):
        """Print welcome message"""
        welcome_text = """
# 🏙️ Local Life Assistant

Welcome to your AI-powered local life assistant! I can help you find:
- 🎉 Events and activities
- 🍽️ Restaurants and dining
- 🎵 Music and entertainment
- 🏃‍♀️ Sports and fitness
- 🎨 Arts and culture
- And much more!

Type your questions naturally, like:
- "I want to go to a jazz concert this weekend"
- "Find me a good Italian restaurant in Manhattan"
- "What free events are happening today?"
- "Show me networking events for professionals"

Type `/help` for commands or `/exit` to quit.
        """
        
        self.console.print(Panel(Markdown(welcome_text), title="Welcome", border_style="blue"))
    
    def print_help(self):
        """Print help information"""
        help_text = """
## Available Commands

- `/help` - Show this help message
- `/clear` - Clear conversation history
- `/llm <provider>` - Switch LLM provider (openai, anthropic, ollama)
- `/stats` - Show database statistics
- `/exit` - Exit the application

## Example Queries

- "Find me a jazz concert this weekend"
- "What restaurants are good for a date night?"
- "Show me free events in Brooklyn"
- "I want to try some new cuisine"
- "What networking events are happening?"
        """
        
        self.console.print(Panel(Markdown(help_text), title="Help", border_style="green"))
    
    def print_stats(self, stats: Dict[str, Any]):
        """Print database statistics"""
        table = Table(title="Database Statistics")
        table.add_column("Collection", style="cyan")
        table.add_column("Count", style="magenta")
        
        table.add_row("Events", str(stats.get("events_count", 0)))
        table.add_row("Restaurants", str(stats.get("restaurants_count", 0)))
        
        self.console.print(table)
    
    def format_recommendation(self, rec: Dict[str, Any]) -> str:
        """Format a single recommendation for display"""
        data = rec.get("data", {})
        rec_type = rec.get("type", "unknown")
        
        if rec_type == "event":
            return f"""
🎉 **{data.get('title', 'Unknown Event')}**
📅 {data.get('start_datetime', 'TBD')}
📍 {data.get('venue_name', 'TBD')}, {data.get('venue_city', 'TBD')}
💰 {'Free' if data.get('is_free') else data.get('ticket_min_price', 'TBD')}
🏷️ {', '.join(data.get('categories', []))}
📝 {data.get('description', 'No description')[:100]}...
🔗 {data.get('event_url', 'No URL')}
            """
        else:  # restaurant
            return f"""
🍽️ **{data.get('name', 'Unknown Restaurant')}**
🍴 {data.get('cuisine_type', 'Unknown')} • {data.get('price_range', 'TBD')}
⭐ {data.get('rating', 'N/A')}/5
📍 {data.get('venue_name', 'TBD')}, {data.get('venue_city', 'TBD')}
🏷️ {', '.join(data.get('categories', []))}
📝 {data.get('description', 'No description')[:100]}...
🌐 {data.get('website', 'No website')}
            """
    
    async def send_chat_request(self, message: str) -> Dict[str, Any]:
        """Send chat request to API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/api/chat",
                    json={
                        "message": message,
                        "conversation_history": [msg.dict() for msg in self.conversation_history],
                        "llm_provider": self.current_llm_provider
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError:
            self.console.print("[red]Error: Could not connect to the API server. Make sure the backend is running on http://localhost:8000[/red]")
            return None
        except httpx.HTTPStatusError as e:
            self.console.print(f"[red]HTTP Error: {e.response.status_code}[/red]")
            return None
        except Exception as e:
            self.console.print(f"[red]Error: {str(e)}[/red]")
            return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base_url}/stats", timeout=10.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            self.console.print(f"[red]Error getting stats: {str(e)}[/red]")
            return {}
    
    def handle_command(self, command: str) -> bool:
        """Handle CLI commands. Returns True if should continue, False if should exit"""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == "/exit":
            return False
        elif cmd == "/help":
            self.print_help()
        elif cmd == "/clear":
            self.conversation_history.clear()
            self.console.print("[green]Conversation history cleared![/green]")
        elif cmd == "/llm":
            if len(parts) > 1:
                provider = parts[1].lower()
                if provider in self.available_providers:
                    self.current_llm_provider = provider
                    self.console.print(f"[green]Switched to {provider} LLM provider[/green]")
                else:
                    self.console.print(f"[red]Invalid provider. Available: {', '.join(self.available_providers)}[/red]")
            else:
                self.console.print(f"[yellow]Current provider: {self.current_llm_provider}[/yellow]")
                self.console.print(f"Available providers: {', '.join(self.available_providers)}")
        elif cmd == "/stats":
            asyncio.create_task(self.show_stats())
        else:
            self.console.print(f"[red]Unknown command: {cmd}. Type /help for available commands.[/red]")
        
        return True
    
    async def show_stats(self):
        """Show database statistics"""
        stats = await self.get_stats()
        if stats:
            self.print_stats(stats)
    
    async def process_message(self, message: str):
        """Process a user message"""
        if not message.strip():
            return
        
        # Add user message to history
        user_msg = ChatMessage(role="user", content=message)
        self.conversation_history.append(user_msg)
        
        # Show typing indicator
        with self.console.status("[bold green]Thinking...", spinner="dots"):
            response = await self.send_chat_request(message)
        
        if response:
            # Display assistant response
            assistant_response = response.get("message", "No response")
            self.console.print(Panel(assistant_response, title="Assistant", border_style="blue"))
            
            # Add assistant message to history
            assistant_msg = ChatMessage(role="assistant", content=assistant_response)
            self.conversation_history.append(assistant_msg)
            
            # Display recommendations
            recommendations = response.get("recommendations", [])
            if recommendations:
                self.console.print("\n[bold cyan]Recommendations:[/bold cyan]")
                
                for i, rec in enumerate(recommendations, 1):
                    rec_text = self.format_recommendation(rec)
                    self.console.print(Panel(rec_text, title=f"Recommendation {i}", border_style="yellow"))
            
            # Show LLM provider used
            provider_used = response.get("llm_provider_used", "unknown")
            self.console.print(f"\n[dim]Powered by {provider_used}[/dim]")
        else:
            self.console.print("[red]Failed to get response from the assistant.[/red]")
    
    async def run(self):
        """Main CLI loop"""
        self.print_welcome()
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]")
                
                # Handle commands
                if user_input.startswith("/"):
                    should_continue = self.handle_command(user_input)
                    if not should_continue:
                        break
                    continue
                
                # Process regular message
                await self.process_message(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Goodbye![/yellow]")
                break
            except EOFError:
                self.console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Unexpected error: {str(e)}[/red]")

async def main():
    """Main entry point"""
    cli = AssistantCLI()
    await cli.run()

if __name__ == "__main__":
    asyncio.run(main())
