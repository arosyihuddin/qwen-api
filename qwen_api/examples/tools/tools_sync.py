"""
Synchronous Tool Usage Example

This script demonstrates how to use tools with the Qwen API synchronously.
It includes multiple tools and shows how the model can choose and use them.
"""

from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage


def main():
    """
    Main function that demonstrates synchronous tool usage.

    1. Creates a Qwen client instance
    2. Defines multiple tools (calculator, weather, search)
    3. Sends requests that should trigger tool usage
    4. Shows the tool calls and their results
    """
    # Initialize the Qwen client
    client = Qwen()

    # Define available tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate",
                        }
                    },
                    "required": ["input"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather information for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The city name to get weather for",
                        },
                        "country": {
                            "type": "string",
                            "description": "The country code (optional)",
                        },
                    },
                    "required": ["city"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query"}
                    },
                    "required": ["query"],
                },
            },
        },
    ]

    # Test cases that should trigger different tools
    test_cases = [
        "Berapa hasil dari 25 * 8 + 17?",
        "Bagaimana cuaca di Jakarta hari ini?",
        "Cari informasi tentang teknologi AI terbaru",
    ]

    try:
        for i, question in enumerate(test_cases, 1):
            print(f"\n=== Test Case {i} ===")
            print(f"Question: {question}")

            messages = [
                ChatMessage(
                    role="user",
                    content=question,
                    web_search=False,
                    thinking=False,
                )
            ]

            # Send the request with tools
            response = client.chat.create(
                messages=messages,
                model="qwen-max-latest",
                tools=tools,
                temperature=0.7,
                max_tokens=1024,
            )

            # Check if tools were called
            if response.choices.message.tool_calls:
                print(
                    f"✅ Tool calls detected: {len(response.choices.message.tool_calls)}"
                )
                for j, tool_call in enumerate(response.choices.message.tool_calls):
                    print(f"  Tool {j+1}: {tool_call.function.name}")
                    print(f"  Arguments: {tool_call.function.arguments}")
            else:
                print("❌ No tool calls detected")
                print(f"Response content: {response.choices.message.content}")

    except QwenAPIError as e:
        print(f"\nError: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")


if __name__ == "__main__":
    main()
