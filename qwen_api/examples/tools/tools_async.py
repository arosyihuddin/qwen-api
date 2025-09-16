"""
Asynchronous Tool Usage Example

This script demonstrates how to use tools with the Qwen API asynchronously.
It includes multiple tools and shows concurrent tool usage.
"""

import asyncio
from qwen_api import Qwen
from qwen_api.core.exceptions import QwenAPIError
from qwen_api.core.types.chat import ChatMessage


async def test_single_tool(client, question, tools, test_name):
    """Helper function to test a single tool usage"""
    print(f"\n=== {test_name} ===")
    print(f"Question: {question}")

    messages = [
        ChatMessage(
            role="user",
            content=question,
            web_search=False,
            thinking=False,
        )
    ]

    try:
        # Send the request with tools
        response = await client.chat.acreate(
            messages=messages,
            model="qwen-max-latest",
            tools=tools,
            temperature=0.7,
            max_tokens=1024,
            stream=False,
        )

        # Check if tools were called
        if response.choices.message.tool_calls:
            print(f"✅ Tool calls detected: {len(response.choices.message.tool_calls)}")
            for j, tool_call in enumerate(response.choices.message.tool_calls):
                print(f"  Tool {j+1}: {tool_call.function.name}")
                print(f"  Arguments: {tool_call.function.arguments}")
        else:
            print("❌ No tool calls detected")
            print(f"Response content: {response.choices.message.content}")

        return response

    except Exception as e:
        print(f"❌ Error in {test_name}: {str(e)}")
        return None


async def main():
    """
    Main async function that demonstrates asynchronous tool usage.

    1. Creates a Qwen client instance
    2. Defines multiple tools
    3. Tests tools concurrently and sequentially
    4. Shows different tool usage patterns
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

    # Test cases
    test_cases = [
        ("Berapa hasil dari 15 * 12?", "Math Calculation"),
        ("Bagaimana cuaca di Surabaya?", "Weather Query"),
        ("Cari berita terbaru tentang teknologi", "Web Search"),
    ]

    try:
        print("Starting asynchronous tool usage tests...")

        # Sequential execution
        print("\n" + "=" * 50)
        print("SEQUENTIAL EXECUTION")
        print("=" * 50)

        for question, test_name in test_cases:
            await test_single_tool(client, question, tools, test_name)

        # Concurrent execution
        print("\n" + "=" * 50)
        print("CONCURRENT EXECUTION")
        print("=" * 50)

        # Create all tasks
        tasks = [
            test_single_tool(client, question, tools, f"Concurrent {test_name}")
            for question, test_name in test_cases
        ]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Summary
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)

        successful_tools = 0
        total_tool_calls = 0

        for i, result in enumerate(results):
            if (
                result
                and hasattr(result, "choices")
                and result.choices.message.tool_calls
            ):
                successful_tools += 1
                total_tool_calls += len(result.choices.message.tool_calls)

        print(f"✅ Successful tool usage: {successful_tools}/{len(test_cases)}")
        print(f"✅ Total tool calls made: {total_tool_calls}")

    except QwenAPIError as e:
        print(f"\nQwen API Error: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
