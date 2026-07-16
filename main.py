import sys
import os
import asyncio
import logging
from PySide6 import QtCore, QtWidgets, QtGui

from agent_core import Agent, LocalAgentConfig, enforce_safety_policy
from desktop_handler import scan_environment, consume_target, get_desktop_directory
from window_effector import tantrum_actuation
from ui_components import TransparentMascotWindow

# Configure logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s")
logger = logging.getLogger("MainApplication")

class AgentWorker(QtCore.QThread):
    """
    QThread worker to run the asyncio Antigravity SDK agent loop in the background,
    preventing any blocking of the PySide6 animation event loop.
    """
    chat_finished = QtCore.Signal(str)
    
    def __init__(self, config: LocalAgentConfig):
        super().__init__()
        self.config = config
        self.prompt = ""
        self.loop = None

    def run_chat(self, prompt: str):
        if self.isRunning():
            logger.warning("Agent is currently busy processing another decision loop.")
            return
        self.prompt = prompt
        self.start()

    def run(self):
        # Create a new event loop for this thread to execute async SDK tasks
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        async def execute_agent():
            logger.info(f"Worker starting execution for prompt: '{self.prompt}'")
            async with Agent(self.config) as agent:
                response = await agent.chat(self.prompt)
                text = await response.text()
                return text
                
        try:
            result_text = self.loop.run_until_complete(execute_agent())
            self.chat_finished.emit(result_text)
        except Exception as e:
            logger.error(f"Error in Agent background thread: {e}")
            self.chat_finished.emit(f"System Error: {e}")
        finally:
            self.loop.close()


class DesktopCompanionApp(QtWidgets.QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        
        # 1. Initialize transparent GUI Window
        self.window = TransparentMascotWindow()
        self.window.show()
        
        # 2. Setup Google Antigravity SDK Configuration
        self.agent_config = LocalAgentConfig(
            system_instructions=(
                "You are an active desktop pet. Your food is Windows shortcut (.lnk) files on the user's desktop.\n"
                "You must check the desktop environment using scan_environment.\n"
                "If food exists, eat one of them using consume_target.\n"
                "If no shortcut files exist and you are hungry, you MUST trigger a tantrum_actuation and beg for shortcuts."
            )
        )
        # Register custom Python callables as tools
        self.agent_config.register_tool(scan_environment)
        self.agent_config.register_tool(consume_target)
        self.agent_config.register_tool(tantrum_actuation)
        # Attach the declarative safety decide hook
        self.agent_config.register_decide_hook(enforce_safety_policy)
        
        # 3. Initialize Agent background worker thread
        self.worker = AgentWorker(self.agent_config)
        self.worker.chat_finished.connect(self._on_agent_response)
        
        # 4. State variables: hunger status tracking
        self.hunger_level = 0  # 0 to 100
        
        # 5. Timer for active hunger tracking cycle (every 10 seconds)
        self.hunger_timer = QtCore.QTimer()
        self.hunger_timer.timeout.connect(self._on_hunger_tick)
        self.hunger_timer.start(10000) # Tick every 10 seconds
        
        # Bind double-click event to trigger immediate feeding/interaction
        # We use an event filter to catch double clicks safely
        self.window.mascot.installEventFilter(self)
        
        # Say initial hello
        self.window.speak("Hello! Double-click me to scan your desktop for tasty shortcuts!")

    def _on_hunger_tick(self):
        # Accumulate hunger
        self.hunger_level = min(100, self.hunger_level + 15)
        logger.info(f"Hunger level updated: {self.hunger_level}/100")
        
        if self.hunger_level >= 75:
            logger.info("Hunger is high. Initiating autonomous eating/tantrum decision sequence.")
            self._trigger_agent_decision("Check if there are any shortcuts on the desktop. If there are, eat one. If none exist, execute a window shake tantrum immediately!")
        elif self.hunger_level >= 45:
            # Gentle warning bubble dialogue
            self.window.speak(f"Getting hungry... Current hunger: {self.hunger_level}%. Feed me some .lnk files soon!")

    def eventFilter(self, obj, event):
        if obj == self.window.mascot and event.type() == QtCore.QEvent.Type.MouseButtonDblClick:
            self._on_mascot_double_click(event)
            return True
        return super().eventFilter(obj, event)

    def _on_mascot_double_click(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            logger.info("User double-clicked mascot. Triggering manual feed/scan request.")
            self.window.speak("Scanning your desktop for delicious shortcuts...")
            # Query the agent to scan and eat
            self._trigger_agent_decision("Scan the desktop environment now and try to consume a shortcut file. Tell me what you found!")
            event.accept()

    def _trigger_agent_decision(self, prompt: str):
        self.worker.run_chat(prompt)

    def _on_agent_response(self, text: str):
        # Display the response text inside the floating bubble
        self.window.speak(text)
        
        # If the agent successfully consumed a file, reduce hunger level
        if "successfully consumed" in text.lower() or "yum" in text.lower() or "delicious" in text.lower() or "mmm" in text.lower():
            self.hunger_level = max(0, self.hunger_level - 50)
            logger.info(f"Mascot fed successfully. Hunger reduced to: {self.hunger_level}/100")


if __name__ == "__main__":
    # Ensure winshell and pywin32 are setup properly on local Windows
    logger.info("Initializing Live2Dpet Desktop Companion program...")
    logger.info(f"Target Desktop folder: {get_desktop_directory()}")
    
    app = DesktopCompanionApp(sys.argv)
    sys.exit(app.exec())
