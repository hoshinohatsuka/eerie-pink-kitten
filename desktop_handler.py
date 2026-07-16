import os
import logging
from typing import List, Dict, Any
import winshell
from send2trash import send2trash
from agent_core import ScanResult, ConsumeResult

logger = logging.getLogger("DesktopHandler")

# Attempt pywin32 dispatch for robust shortcut parsing, fallback to basic parsing if unavailable
try:
    import win32com.client
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False
    logger.warning("pywin32 (win32com) not available. Shortcut resolution will rely on text fallbacks.")

try:
    import pylnk3
    HAS_PYLNK3 = True
except ImportError:
    HAS_PYLNK3 = False
    logger.warning("pylnk3 not available. Using COM/WScript as primary.")

def get_desktop_directory() -> str:
    """
    Resolves the user's active desktop directory. Handles redirected folders (like OneDrive).
    """
    try:
        return os.path.normpath(winshell.desktop())
    except Exception as e:
        logger.error(f"Failed to resolve desktop using winshell: {e}")
        # Fallback to default user profile directory
        return os.path.normpath(os.path.expanduser("~/Desktop"))

def resolve_shortcut(lnk_path: str) -> Dict[str, Any]:
    """
    Parses a Windows .lnk shortcut to extract its Target Path, existence, and category.
    """
    target_path = ""
    description = ""
    working_directory = ""
    
    # Method A: Use Windows COM interface (highly reliable on Windows)
    if HAS_WIN32COM:
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(lnk_path)
            target_path = shortcut.TargetPath
            description = shortcut.Description
            working_directory = shortcut.WorkingDirectory
        except Exception as e:
            logger.error(f"COM parsing failed for {lnk_path}: {e}")
            
    # Method B: Use pylnk3 if COM failed or was unavailable
    if not target_path and HAS_PYLNK3:
        try:
            lnk = pylnk3.parse(lnk_path)
            target_path = lnk.path
            description = lnk.description
        except Exception as e:
            logger.error(f"pylnk3 parsing failed for {lnk_path}: {e}")

    # Fallback/Heuristic: Check if we got anything
    if not target_path:
        # Unable to parse target path, mark as unknown
        target_path = "UnknownTarget"

    # Classify the shortcut type for mascot flavor preferences
    category = "generic"
    target_lower = target_path.lower()
    
    if any(k in target_lower for k in ["steam", "game", "ea", "epicgames", "riotgames", "glauncher"]):
        category = "game"
    elif any(k in target_lower for k in ["code", "visualstudio", "pycharm", "git", "idea", "sublime"]):
        category = "development"
    elif any(k in target_lower for k in ["chrome", "firefox", "edge", "browser", "opera"]):
        category = "browser"
    elif any(k in target_lower for k in ["word", "excel", "powerpnt", "pdf", "acrobat", "office"]):
        category = "document"

    # Check for dead link
    is_dead = False
    if target_path and target_path != "UnknownTarget":
        is_dead = not os.path.exists(target_path)

    return {
        "target_path": target_path,
        "description": description,
        "working_directory": working_directory,
        "category": category,
        "is_dead": is_dead
    }

async def scan_environment() -> ScanResult:
    """
    Scans the desktop for all .lnk shortcut files.
    """
    desktop_dir = get_desktop_directory()
    logger.info(f"Scanning desktop directory: {desktop_dir}")
    
    shortcuts = []
    if os.path.exists(desktop_dir):
        for file in os.listdir(desktop_dir):
            if file.lower().endswith(".lnk"):
                full_path = os.path.join(desktop_dir, file)
                shortcuts.append(os.path.normpath(full_path))
                
    return ScanResult(items=shortcuts)

async def consume_target(filepath: str) -> ConsumeResult:
    """
    Moves a shortcut file safely to the Recycle Bin via Send2Trash.
    """
    filepath = os.path.normpath(filepath)
    if not os.path.exists(filepath):
        return ConsumeResult(success=False, reason=f"File does not exist: '{filepath}'")
        
    try:
        # Extract target information before deleting for the flavor text
        info = resolve_shortcut(filepath)
        filename = os.path.basename(filepath)
        
        # Safe deletion via Send2Trash (moves file to Recycle Bin)
        send2trash(filepath)
        
        # Build fun taste profile response
        category = info["category"]
        is_dead = info["is_dead"]
        
        if is_dead:
            flavor = "This was a dead link! Clean, light, and easy to digest. 10/10 digital waste removal!"
        elif category == "game":
            flavor = "Whoa! Tons of graphics and physics calculations. Tastes energetic and spicy!"
        elif category == "development":
            flavor = "Tastes like code rust, git merge conflicts, and stack overflows. Heavy but satisfying!"
        elif category == "browser":
            flavor = "Full of internet cookies and raw html data. Creamy and sweet!"
        elif category == "document":
            flavor = "Dry paperwork flavor. Needs a little digital seasoning!"
        else:
            flavor = "Standard shortcut taste. Tastes like a plain byte."

        reason = f"Successfully consumed '{filename}' and moved to Recycle Bin. Taste Profile: {flavor}"
        logger.info(reason)
        return ConsumeResult(success=True, reason=reason)
        
    except PermissionError:
        err_msg = f"Failed to consume '{filepath}'. File is locked or currently in use by another process."
        logger.error(err_msg)
        return ConsumeResult(success=False, reason=err_msg)
    except Exception as e:
        err_msg = f"Unexpected error during consumption: {e}"
        logger.error(err_msg)
        return ConsumeResult(success=False, reason=err_msg)
