from .__init__ import BaseAgent
from .executor import AgentExecutor
from .graph.agent_graph import AgentGraph
from .graph.memory_graph import MemoryGraph
from .state import AgentState, MemoryState
from ..models import BaseModel
from ..browser import Browser
from typing import AsyncGenerator, Optional, Dict, Any
from colorama import Fore, Style
from uuid import uuid4
import asyncio
import json
import os

class Agent(BaseAgent):
    """
    High-level orchestrator for the agent.
    Takes in attributes of the browser, model, max_iterations, scraper_response_json_format

    Attributes:
        browser (Browser): The browser instance to use for the agent
        model (BaseModel): The model instance to use for the agent
        max_iterations (int): The maximum number of iterations to run the agent for
        scraper_response_json_format (Optional[Dict[str, Any]]): The JSON format to use for the scraper response
    """

    def __init__(
            self, 
            browser: Browser, 
            model: BaseModel, 
            max_iterations: int = 100, 
            scraper_response_json_format: Optional[Dict[str, Any]] = None,
        ) -> None:
        self._executor = AgentExecutor(
            model = model,
            browser = browser,
            scraper_response_json_format = scraper_response_json_format,
            session = str(uuid4())
        )
        self.max_iterations = max_iterations
        self.browser = browser

    async def arun(
            self, 
            query: str, 
            verbose: bool = False, 
            wait_between_actions: int = 0,
            memorize: bool = False,
            screenshot_each_step: bool = True
        ) -> AsyncGenerator[str | dict | list, None]:
        """
        The arun as Async Run method is the driver method to run the agent to do the task.
        This will run the agent graph and return the final output.

        Args:
            query (str): The input query to run the agent for
            verbose (bool): Whether to print verbose output
            wait_between_actions (int): Wait between actions in seconds (default: 0)
            memorize (bool): Whether to memorize the steps being taken

        Returns:
            AsyncGenerator[str | dict | list, None]: The final output of the agent
        """

        agent_graph_instance = AgentGraph(self._executor, AgentState)
        graph = agent_graph_instance.create_graph()

        # Initialize browser and executor
        # await self.browser.init_browser()
        self._executor._finish_initialization(self.browser.page)

        # Build initial state which will be passed to the agent
        initial_state = AgentState(
            input = query,
            output = "",
            previous_actions = [],
            page_state = None,
            response = None,
            scraped_data = [],
            verbose = verbose,
            wait_between_actions = wait_between_actions,
            memorize = memorize,
            screenshot_each_step = screenshot_each_step,
            screenshot_base64 = None
        )

        prev_iteration = -1
        
        # Stream graph states
        try:
            async for chunk in graph.astream(
                initial_state, { 'recursion_limit': self.max_iterations }, 
                stream_mode = 'updates'
            ):  
                # yield iteration count at every chunk
                if prev_iteration != self._executor._iterations:
                    yield json.dumps({"type": "iteration", "data": self._executor._iterations}, ensure_ascii=False)
                    prev_iteration = self._executor._iterations

                url = self.browser.page.url
                if url:
                    yield json.dumps({"type": "url", "data": url}, ensure_ascii=False)
                
                for node_name, node_output in chunk.items():
                    if not node_output: 
                        continue

                    if node_name == "model_node":
                        response_data = node_output.get("response") or {}
                        thought = response_data.get("thought")
                        tool_call = response_data.get("tool_name")
                        tool_args = response_data.get("tool_args")
                        if thought:
                            yield json.dumps({"type": "thought", "data": thought}, ensure_ascii=False)
                        if tool_call:
                            yield json.dumps({"type": "tool_call", "data": {"name": tool_call, "args": tool_args}}, ensure_ascii=False)

                    elif node_name == "tool_node":
                        previous_actions = node_output.get("previous_actions") or []
                        last_tool_response = previous_actions[-1].get("tool_response")
                        screenshot = node_output.get("screenshot_base64")
                        if last_tool_response:
                            yield json.dumps({"type": "tool_response", "data": last_tool_response}, ensure_ascii=False)
                        if screenshot:
                            yield json.dumps({"type": "screenshot", "data": screenshot}, ensure_ascii=False)

                    elif node_name == "output_node":
                        text_output = node_output.get("text_output", "")
                        json_output = node_output.get("json_output", "")
                        result_output = node_output.get("result_output", "")
                        error_output = node_output.get("error_output", "")

                        if text_output:
                            yield json.dumps({"type": "text_output", "data": text_output}, ensure_ascii=False)
                        if json_output:
                            yield json.dumps({"type": "json_output", "data": json_output}, ensure_ascii=False)
                        if result_output:
                            yield json.dumps({"type": "result_output", "data": result_output}, ensure_ascii=False)
                        if error_output:
                            yield json.dumps({"type": "error_output", "data": error_output}, ensure_ascii=False)
                        return
        except asyncio.CancelledError:
            yield json.dumps({"type": "cancelled", "data": "Request cancelled by the server"}, ensure_ascii=False)

        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f'Error: {str(e)}\n' + Style.RESET_ALL)
            yield json.dumps({"type": "error", "data": str(e)}, ensure_ascii=False)
        finally:
            await self.browser.close_browser()
            self._executor._model = None
            self._executor = None
            self.browser = None
            print(Fore.GREEN + Style.BRIGHT + "Browser closed successfully (agent)" + Style.RESET_ALL)

    def get_memory(self) -> str:
        MEMORY_PATH = os.path.join(os.path.dirname(__file__), '../memory/memory.json')
        try:
            with open(MEMORY_PATH, 'r') as f:
                memory = json.load(f)
            
            sessions = ''
            for m in memory:
                sessions += 'Session: ' + m['session'] + '\n'
                sessions += 'Input: ' + m['input'] + '\n'
                sessions += 'Created At: ' + m['created_at'] + '\n'
                sessions += '-----------------------------------------\n'
                    
            return sessions
        except FileNotFoundError:
            return 'No memory found'

    async def replay_session(
            self, 
            session: str, 
            verbose: bool = False, 
            wait_between_actions: int = 1,
            screenshot_each_step: bool = False
        ) -> list | dict | str:
        """
        Replay a saved session from memory. 
        This will replace exact steps from the saved memory json, does not resolve tool response errors
        as there is no LLM to resolve the errors.
        Note: Any manual changes done to the saved memory json will directly reflect in the replayed session.

        Args:
            session (str): The session to replay
            verbose (bool): Whether to print verbose output
            wait_between_actions (int): Wait between actions in seconds (default: 1)

        Returns:
            list or dict or str: The final output of the agent
        """

        initial_memory_state = MemoryState(
            input = '',
            steps = [],
            step_results = [],
            verbose = verbose,
            current_step_index = 0,
            scraped_data = [],
            output = '',
            wait_between_actions = wait_between_actions,
            screenshot_each_step = screenshot_each_step
        )

        try:
            with open(os.path.join(os.path.dirname(__file__), '../memory/memory.json'), 'r') as f:
                memory = json.load(f)
        except FileNotFoundError:
            memory = []

        found_session = False
        for m in memory:
            if m['session'] == session:
                initial_memory_state = MemoryState(
                    input = m['input'],
                    steps = m['steps'],
                    step_results = [],
                    verbose = verbose,
                    current_step_index = 0,
                    scraped_data = [],
                    output = '',
                    wait_between_actions = wait_between_actions,
                    screenshot_each_step = screenshot_each_step
                )
                found_session = True
                break

        if not found_session:
            return 'Session not found'

        memory_graph_instance = MemoryGraph(self._executor, initial_memory_state)
        graph = memory_graph_instance.create_graph()

        await self.browser.init_browser()
        self._executor._finish_initialization(self.browser.page)

        print(Fore.CYAN + Style.BRIGHT + 'Memory session: ' + session + '\n' + Style.RESET_ALL)
        print(Fore.BLUE + Style.BRIGHT + f'User input: {initial_memory_state.get('input')}\n' + Style.RESET_ALL)

        result = await graph.ainvoke(initial_memory_state, { 'recursion_limit': self.max_iterations })

        await self.browser.close_browser()

        if result['output']:
            return result['output']
        return result