import os
import sys
import logging
from typing import List, Dict, Any, Callable
from pydantic import BaseModel, Field

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AgentCore")

# Attempt to import Google Antigravity SDK, fall back to mock if not present
try:
    from google.antigravity import Agent as ActualAgent
    from google.antigravity import LocalAgentConfig as ActualLocalAgentConfig
    from google.antigravity import policy as actual_policy
    HAS_SDK = True
    logger.info("Successfully imported Google Antigravity SDK.")
except ImportError:
    HAS_SDK = False
    logger.warning("Google Antigravity SDK not found. Loading fallback Mock agent harness.")

# Define Pydantic V2 schemas for structured outputs
class ScanResult(BaseModel):
    items: List[str] = Field(description="List of absolute paths of shortcuts on the desktop")

class ConsumeResult(BaseModel):
    success: bool = Field(description="Whether the target file was successfully removed")
    reason: str = Field(description="Details on why the consumption succeeded or failed")

class TantrumResult(BaseModel):
    applied: bool = Field(description="Whether the window shaking was successfully applied")
    intensity: str = Field(description="Intensity level of the window shaking (MINIMAL or HIGH)")

# Mock classes for standalone fallback execution
class MockPolicy:
    def __init__(self):
        self.denied = False
        self.reason = ""

    def deny(self, reason: str):
        self.denied = True
        self.reason = reason
        logger.warning(f"[POLICY DENIED] {reason}")

policy = MockPolicy()

class MockLocalAgentConfig:
    def __init__(self, system_instructions: str = ""):
        self.system_instructions = system_instructions
        self.decide_hooks: List[Callable] = []
        self.tools: List[Callable] = []

    def register_decide_hook(self, hook: Callable):
        self.decide_hooks.append(hook)

    def register_tool(self, tool: Callable):
        self.tools.append(tool)

class MockAgentChatResponse:
    def __init__(self, text_content: str):
        self._text = text_content

    async def text(self) -> str:
        return self._text

class MockAgent:
    def __init__(self, config: MockLocalAgentConfig):
        self.config = config
        self._tools_map = {t.__name__: t for t in config.tools}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def chat(self, prompt: str) -> MockAgentChatResponse:
        logger.info(f"Mock Agent received prompt: '{prompt}'")
        
        # Simulate agentic reasoning based on prompt contents
        if "scan" in prompt.lower():
            # Simulate calling scan_environment tool
            tool_call = type('ToolCall', (), {'name': 'scan_environment', 'args': {}})()
            # Enforce decide hook policy
            allowed = True
            for hook in self.config.decide_hooks:
                allowed = allowed and hook(tool_call)
            
            if allowed and 'scan_environment' in self._tools_map:
                res = await self._tools_map['scan_environment']()
                return MockAgentChatResponse(
                    f"I scanned the desktop and found {len(res.items)} shortcuts: {', '.join(res.items)}."
                )
            else:
                return MockAgentChatResponse("I tried to scan the environment but was blocked or tool not registered.")
                
        elif "consume" in prompt.lower() or "eat" in prompt.lower():
            # Extract potential path (very naive parser for testing)
            filepath = ""
            for word in prompt.split():
                if word.endswith(".lnk") or ":" in word:
                    filepath = word.strip("'\"")
                    break
            
            if not filepath:
                # Fallback to some default
                filepath = "C:\\Users\\MockUser\\Desktop\\InvalidFile.txt"

            tool_call = type('ToolCall', (), {'name': 'consume_target', 'args': {'filepath': filepath}})()
            
            # Enforce decide hook policy
            policy.denied = False
            policy.reason = ""
            allowed = True
            for hook in self.config.decide_hooks:
                allowed = allowed and hook(tool_call)
                
            if policy.denied:
                return MockAgentChatResponse(f"I cannot eat that file! Reason: {policy.reason}")
                
            if allowed and 'consume_target' in self._tools_map:
                res = await self._tools_map['consume_target'](filepath)
                if res.success:
                    return MockAgentChatResponse(f"Mmm! Delicious. I successfully consumed: {filepath}. {res.reason}")
                else:
                    return MockAgentChatResponse(f"I tried to eat {filepath} but failed. Reason: {res.reason}")
            else:
                return MockAgentChatResponse("Eating action was blocked or could not be executed.")
                
        elif "shake" in prompt.lower() or "tantrum" in prompt.lower() or "hungry" in prompt.lower():
            tool_call = type('ToolCall', (), {'name': 'tantrum_actuation', 'args': {'intensity': 'HIGH'}})()
            allowed = True
            for hook in self.config.decide_hooks:
                allowed = allowed and hook(tool_call)
                
            if allowed and 'tantrum_actuation' in self._tools_map:
                res = await self._tools_map['tantrum_actuation']('HIGH')
                return MockAgentChatResponse(
                    "I am extremely hungry and I couldn't find any shortcuts! I am shaking your window! Feed me now! (Tantrum executed)"
                )
            else:
                return MockAgentChatResponse("My tantrum action was blocked.")

        return MockAgentChatResponse("Hello! I am your desktop companion. I parse shortcuts and need to eat .lnk files to stay happy!")

# Export SDK or Mock equivalents
Agent = ActualAgent if HAS_SDK else MockAgent
LocalAgentConfig = ActualLocalAgentConfig if HAS_SDK else MockLocalAgentConfig

# Helper function to enforce safety policy via Decide Hook
def enforce_safety_policy(tool_call) -> bool:
    """
    Decide Hook logic:
    1. consume_target MUST target files within the Desktop directory.
    2. The file extension MUST strictly be '.lnk'.
    3. Block all other operations on files to prevent system modifications.
    """
    import winshell
    
    if tool_call.name == "consume_target":
        filepath = tool_call.args.get("filepath")
        if not filepath:
            if HAS_SDK:
                from google.antigravity import policy as sdk_policy
                sdk_policy.deny("Missing filepath parameter")
            else:
                policy.deny("Missing filepath parameter")
            return False
            
        try:
            desktop_dir = os.path.normpath(winshell.desktop())
        except Exception as e:
            # Fallback path if winshell fails in non-Windows/testing environments
            desktop_dir = os.path.normpath(os.path.expanduser("~/Desktop"))
            
        target_path = os.path.normpath(filepath)
        
        # Verify directory boundary
        if not target_path.lower().startswith(desktop_dir.lower()):
            msg = f"Security Violation: Target file '{target_path}' lies outside the Desktop boundary '{desktop_dir}'!"
            if HAS_SDK:
                from google.antigravity import policy as sdk_policy
                sdk_policy.deny(msg)
            else:
                policy.deny(msg)
            return False
            
        # Verify shortcut extension
        if not target_path.lower().endswith(".lnk"):
            msg = f"Security Violation: Target file '{target_path}' is not a shortcut (.lnk) file!"
            if HAS_SDK:
                from google.antigravity import policy as sdk_policy
                sdk_policy.deny(msg)
            else:
                policy.deny(msg)
            return False
            
        logger.info(f"[POLICY CHECK] Approved consume_target for: {filepath}")
    return True
