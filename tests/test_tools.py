"""Unit tests for tools module."""

import pytest
from src.tools import CalculatorTool, WebSearchTool, WeatherTool, get_available_tools


def test_calculator_tool():
    """Test calculator tool."""
    tool = CalculatorTool()
    
    # Test simple addition
    result = tool._run("2 + 2")
    assert result == "4"
    
    # Test multiplication
    result = tool._run("5 * 3")
    assert result == "15"
    
    # Test division
    result = tool._run("10 / 2")
    assert result == "5.0"


def test_web_search_tool():
    """Test web search tool."""
    tool = WebSearchTool()
    
    # Test search (may fail if network is unavailable)
    try:
        result = tool._run("Python programming")
        assert isinstance(result, str)
        assert len(result) > 0
    except Exception:
        # Network may be unavailable in test environment
        pytest.skip("Network unavailable for web search test")


def test_weather_tool():
    """Test weather tool."""
    tool = WeatherTool()
    
    # Test weather lookup
    result = tool._run("New York")
    assert isinstance(result, str)
    assert "New York" in result
    assert "Temperature" in result


def test_get_available_tools():
    """Test getting available tools."""
    tools = get_available_tools()
    assert len(tools) > 0
    
    # Check tool names
    tool_names = [tool.name for tool in tools]
    assert "calculator" in tool_names or "web_search" in tool_names or "weather" in tool_names
