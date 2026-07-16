import os
import time
import math
import logging
import threading
from typing import Tuple
from agent_core import TantrumResult

logger = logging.getLogger("WindowEffector")

# Try to import Win32 packages, handle non-Windows systems gracefully
try:
    import win32gui
    import win32api
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    logger.warning("pywin32 packages not found. Window perturbation will run in simulated mode.")

# Blacklist of window titles that should never be perturbed to prevent DWM crashes or breaking system overlay
WINDOW_TITLE_BLACKLIST = [
    "task switching",
    "program manager",
    "开始",
    "start",
    "task manager",
    "任务管理器",
    "desktop companion",
    "live2dpet"
]

def get_foreground_window_safely() -> int:
    """
    Retrieves the memory handle (HWND) of the current foreground active window,
    applying cleaning heuristics to filter out system and background components.
    """
    if not HAS_WIN32:
        logger.info("[MOCK] GetForegroundWindow retrieved mock handle: 9999")
        return 9999
        
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd or hwnd == 0:
        return 0
        
    # Check 1: Window visibility
    if not win32gui.IsWindowVisible(hwnd):
        return 0
        
    # Check 2: Window title length and content
    title = win32gui.GetWindowText(hwnd).strip()
    if not title:
        return 0
        
    # Check 3: Check title against blacklist
    title_lower = title.lower()
    for blacklisted in WINDOW_TITLE_BLACKLIST:
        if blacklisted in title_lower:
            logger.info(f"Window '{title}' (HWND: {hwnd}) is blacklisted. Shaking skipped.")
            return 0
            
    # Check 4: Filter out Shell classes like Desktop worker or taskbars
    class_name = win32gui.GetClassName(hwnd).lower()
    if any(cls in class_name for cls in ["workerw", "progman", "shell_traywnd", "dv2controlhost"]):
        logger.info(f"Window class '{class_name}' is a system shell. Shaking skipped.")
        return 0
        
    logger.info(f"Target window identified: '{title}' (HWND: {hwnd}, Class: {class_name})")
    return hwnd

def perform_damped_shake(hwnd: int, duration: float = 1.0, intensity: float = 15.0):
    """
    Applies continuous position displacement to target window HWND based on a damped sine wave:
    x_offset(t) = A * e^(-gamma * t) * sin(omega * t)
    y_offset(t) = B * e^(-gamma * t) * cos(omega * t)
    
    Includes multi-display monitor boundary clamping to prevent window clipping.
    """
    if not HAS_WIN32 or hwnd == 9999:
        logger.info(f"[MOCK] Shaking mock window. Duration: {duration}s, Intensity: {intensity}")
        time.sleep(duration)
        logger.info("[MOCK] Shaking completed. Mock window returned to static state.")
        return
        
    try:
        # Get static initial geometry
        rect = win32gui.GetWindowRect(hwnd)
        x, y, r, b = rect
        w, h = r - x, b - y
        
        # Resolve display monitor work area boundaries to clamp motion
        monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        monitor_info = win32api.GetMonitorInfo(monitor)
        work_area = monitor_info['Work']
        mw_left, mw_top, mw_right, mw_bottom = work_area
        
        start_time = time.time()
        gamma = 4.0   # Damping coefficient (decay rate)
        omega = 35.0  # Angular frequency of oscillation (frequency)
        
        logger.info(f"Beginning damped window shake on HWND {hwnd}. Initial position: ({x}, {y})")
        
        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break
                
            # Damped sin/cos computation
            decay_factor = math.exp(-gamma * elapsed)
            offset_x = int(intensity * decay_factor * math.sin(omega * elapsed))
            offset_y = int(intensity * decay_factor * math.cos(omega * elapsed))
            
            # Compute new coordinates with boundary clamping
            new_x = max(mw_left, min(x + offset_x, mw_right - w))
            new_y = max(mw_top, min(y + offset_y, mw_bottom - h))
            
            # Send movement to Windows OS queue
            win32gui.MoveWindow(hwnd, new_x, new_y, w, h, True)
            time.sleep(0.015) # ~60FPS update cycle
            
        # Restore window to original absolute coordinates
        win32gui.MoveWindow(hwnd, x, y, w, h, True)
        logger.info(f"Finished window shake. Restored HWND {hwnd} to ({x}, {y})")
        
    except Exception as e:
        logger.error(f"Error occurred during physical window shake: {e}")

def run_shake_in_background(hwnd: int, duration: float = 1.2, intensity: float = 20.0):
    """
    Executes the shaking sequence inside an asynchronous background daemon thread
    to prevent locking the Qt UI rendering thread.
    """
    t = threading.Thread(
        target=perform_damped_shake,
        args=(hwnd, duration, intensity),
        daemon=True
    )
    t.start()

async def tantrum_actuation(intensity: str = "HIGH") -> TantrumResult:
    """
    Triggers the active window shaking. Returns whether the perturbation was applied.
    """
    hwnd = get_foreground_window_safely()
    if hwnd == 0:
        logger.warning("No valid foreground window found to shake.")
        return TantrumResult(applied=False, intensity=intensity)
        
    # Set intensity values
    int_val = 25.0 if intensity == "HIGH" else 10.0
    run_shake_in_background(hwnd, duration=1.2, intensity=int_val)
    
    return TantrumResult(applied=True, intensity=intensity)
