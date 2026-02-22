"""Custom tools for the AI agent."""

import json
import logging
import re
from typing import Any, Dict, Optional
import requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.config import settings

logger = logging.getLogger(__name__)


class CalculatorInput(BaseModel):
    """Input schema for calculator tool."""
    expression: str = Field(..., description="Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')")


class CalculatorTool(BaseTool):
    """Tool for performing mathematical calculations."""
    
    name: str = "calculator"
    description: str = (
        "Useful for performing mathematical calculations. "
        "Input should be a valid mathematical expression. "
        "Examples: '2 + 2', '10 * 5', 'sqrt(16)', '2 ** 3'"
    )
    args_schema: type[BaseModel] = CalculatorInput
    
    def _run(self, expression: str) -> str:
        """Execute the calculation.
        
        Args:
            expression: Mathematical expression to evaluate
            
        Returns:
            Result of the calculation as a string
        """
        try:
            # Sanitize input - only allow safe mathematical operations
            # Remove any potentially dangerous functions
            sanitized = re.sub(r'[^0-9+\-*/().\s]', '', expression)
            
            # Use eval with limited builtins for safety
            allowed_names = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
            }
            
            result = eval(sanitized, allowed_names)
            logger.info(f"Calculator: {expression} = {result}")
            return str(result)
        except Exception as e:
            error_msg = f"Error calculating '{expression}': {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def _arun(self, expression: str) -> str:
        """Async version of the tool."""
        return self._run(expression)


class WebSearchInput(BaseModel):
    """Input schema for web search tool."""
    query: str = Field(..., description="Search query string")


class WebSearchTool(BaseTool):
    """Tool for searching the web (mock implementation using DuckDuckGo API)."""
    
    name: str = "web_search"
    description: str = (
        "Useful for searching the web for current information. "
        "Input should be a search query string. "
        "Returns relevant search results and snippets."
    )
    args_schema: type[BaseModel] = WebSearchInput
    
    def _run(self, query: str) -> str:
        """Execute the web search.
        
        Args:
            query: Search query string
            
        Returns:
            Search results as a formatted string
        """
        try:
            # Using DuckDuckGo Instant Answer API (no API key required)
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Extract abstract if available
            if data.get("AbstractText"):
                results.append(f"Summary: {data['AbstractText']}")
            
            # Extract related topics
            if data.get("RelatedTopics"):
                topics = data["RelatedTopics"][:3]  # Limit to 3 results
                for topic in topics:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append(f"- {topic['Text']}")
            
            # Extract answer if available
            if data.get("Answer"):
                results.insert(0, f"Answer: {data['Answer']}")
            
            if not results:
                return f"No results found for query: {query}"
            
            result_text = "\n".join(results)
            logger.info(f"Web search completed for: {query}")
            return result_text
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error searching web for '{query}': {str(e)}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error in web search: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def _arun(self, query: str) -> str:
        """Async version of the tool."""
        return self._run(query)


class WeatherInput(BaseModel):
    """Input schema for weather tool."""
    location: str = Field(..., description="Location name or city (e.g., 'New York', 'London')")


class WeatherTool(BaseTool):
    """Tool for getting weather information (mock implementation)."""
    
    name: str = "weather"
    description: str = (
        "Useful for getting current weather information for a location. "
        "Input should be a location name or city. "
        "Returns weather conditions including temperature, humidity, and description."
    )
    args_schema: type[BaseModel] = WeatherInput
    
    def _run(self, location: str) -> str:
        """Get weather information for a location.
        
        Args:
            location: Location name or city
            
        Returns:
            Weather information as a formatted string
        """
        try:
            # Mock weather data - in production, integrate with a real weather API
            # like OpenWeatherMap, WeatherAPI, etc.
            mock_weather = {
                "location": location,
                "temperature": "22°C",
                "condition": "Partly cloudy",
                "humidity": "65%",
                "wind_speed": "15 km/h"
            }
            
            # In a real implementation, you would call an actual weather API:
            # url = f"https://api.weatherapi.com/v1/current.json"
            # params = {"key": settings.weather_api_key, "q": location}
            # response = requests.get(url, params=params)
            # data = response.json()
            
            result = (
                f"Weather for {mock_weather['location']}:\n"
                f"Temperature: {mock_weather['temperature']}\n"
                f"Condition: {mock_weather['condition']}\n"
                f"Humidity: {mock_weather['humidity']}\n"
                f"Wind Speed: {mock_weather['wind_speed']}"
            )
            
            logger.info(f"Weather retrieved for: {location}")
            return result
            
        except Exception as e:
            error_msg = f"Error getting weather for '{location}': {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def _arun(self, location: str) -> str:
        """Async version of the tool."""
        return self._run(location)


def get_available_tools() -> list[BaseTool]:
    """Get list of available tools based on configuration.
    
    Returns:
        List of tool instances
    """
    tools = []
    
    if settings.enable_calculator:
        tools.append(CalculatorTool())
    
    if settings.enable_web_search:
        tools.append(WebSearchTool())
    
    if settings.enable_weather:
        tools.append(WeatherTool())
    
    return tools


def get_tool_info() -> list[Dict[str, Any]]:
    """Get information about available tools.
    
    Returns:
        List of tool information dictionaries
    """
    tools = get_available_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.args_schema.schema() if hasattr(tool, 'args_schema') else {}
        }
        for tool in tools
    ]
