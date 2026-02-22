"""LangChain agent setup and execution."""

import logging
from typing import List, Dict, Any, Optional, AsyncIterator
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.config import settings
from src.tools import get_available_tools

logger = logging.getLogger(__name__)


class ChatAgent:
    """Manages the LangChain agent for conversational AI with tool calling."""
    
    def __init__(
        self,
        tools: Optional[List[BaseTool]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """Initialize the chat agent.
        
        Args:
            tools: List of tools for the agent. Defaults to configured tools.
            temperature: LLM temperature. Defaults to config setting.
            max_tokens: Maximum tokens. Defaults to config setting.
        """
        self.tools = tools or get_available_tools()
        self.temperature = temperature or settings.openai_temperature
        self.max_tokens = max_tokens or settings.openai_max_tokens
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=settings.openai_api_key
        )
        
        # Create agent prompt
        self.prompt = self._create_prompt()
        
        # Create agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=settings.agent_verbose,
            max_iterations=settings.agent_max_iterations,
            max_execution_time=settings.agent_max_execution_time,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        logger.info(f"Agent initialized with {len(self.tools)} tools")
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the agent prompt template.
        
        Returns:
            ChatPromptTemplate instance
        """
        system_message = """You are a helpful AI assistant with access to various tools.
You can help users with calculations, web searches, weather information, and general questions.
When a user asks a question that requires tool usage, use the appropriate tool(s) to get the information.
Always provide clear, helpful responses based on the tool results.
If a tool fails, explain the error to the user and suggest alternatives."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return prompt
    
    def format_chat_history(self, messages: List[Dict[str, Any]]) -> List:
        """Format chat history for LangChain.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            List of LangChain message objects
        """
        formatted = []
        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            
            if role == "user":
                formatted.append(HumanMessage(content=content))
            elif role == "assistant":
                formatted.append(AIMessage(content=content))
        
        return formatted
    
    def run(
        self,
        user_input: str,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Execute the agent with user input.
        
        Args:
            user_input: User's message
            chat_history: Previous conversation messages
            
        Returns:
            Dictionary with 'output', 'tools_used', and 'intermediate_steps'
        """
        try:
            # Format chat history
            history = self.format_chat_history(chat_history or [])
            
            # Prepare input
            agent_input = {
                "input": user_input,
                "chat_history": history
            }
            
            # Execute agent
            result = self.agent_executor.invoke(agent_input)
            
            # Extract tools used
            tools_used = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) > 0:
                        tool_name = step[0].tool if hasattr(step[0], 'tool') else "unknown"
                        tools_used.append(tool_name)
            
            return {
                "output": result.get("output", ""),
                "tools_used": tools_used,
                "intermediate_steps": result.get("intermediate_steps", [])
            }
            
        except Exception as e:
            logger.error(f"Agent execution error: {str(e)}", exc_info=True)
            return {
                "output": f"I encountered an error: {str(e)}. Please try again.",
                "tools_used": [],
                "intermediate_steps": []
            }
    
    async def astream(
        self,
        user_input: str,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[str]:
        """Stream agent response.
        
        Args:
            user_input: User's message
            chat_history: Previous conversation messages
            
        Yields:
            Chunks of the response as strings
        """
        try:
            # Format chat history
            history = self.format_chat_history(chat_history or [])
            
            # Prepare input
            agent_input = {
                "input": user_input,
                "chat_history": history
            }
            
            # Stream agent execution
            async for chunk in self.agent_executor.astream(agent_input):
                if "output" in chunk:
                    yield chunk["output"]
                elif "agent" in chunk and "messages" in chunk["agent"]:
                    for message in chunk["agent"]["messages"]:
                        if hasattr(message, 'content'):
                            yield message.content
                            
        except Exception as e:
            logger.error(f"Agent streaming error: {str(e)}", exc_info=True)
            yield f"Error: {str(e)}"


# Global agent instance (will be initialized in main.py)
agent: Optional[ChatAgent] = None


def get_agent(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> ChatAgent:
    """Get or create the global agent instance.
    
    Args:
        temperature: Optional temperature override
        max_tokens: Optional max_tokens override
        
    Returns:
        ChatAgent instance
    """
    global agent
    if agent is None:
        agent = ChatAgent(temperature=temperature, max_tokens=max_tokens)
    return agent
