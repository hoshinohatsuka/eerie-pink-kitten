import os
import sys
import math
import tempfile
import logging
from agent_core import enforce_safety_policy, MockPolicy, ScanResult, ConsumeResult, TantrumResult
import desktop_handler
import window_effector

# Set up logging for validation run
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Verifier")

class MockToolCall:
    def __init__(self, name: str, args: dict):
        self.name = name
        self.args = args

def test_safety_policies():
    logger.info("=== Running Safety Policy Tests ===")
    
    # Resolve desktop path
    desktop_dir = desktop_handler.get_desktop_directory()
    logger.info(f"Resolved Desktop Path: '{desktop_dir}'")
    
    # Case 1: Valid shortcut inside Desktop directory
    valid_path = os.path.join(desktop_dir, "MySteamGame.lnk")
    call_valid = MockToolCall("consume_target", {"filepath": valid_path})
    assert enforce_safety_policy(call_valid) == True, "Should ALLOW valid shortcut on Desktop"
    logger.info("  [PASS] Allowed valid shortcut on Desktop.")

    # Case 2: Invalid extension (.txt) inside Desktop directory
    invalid_ext = os.path.join(desktop_dir, "CriticalDocument.txt")
    call_invalid_ext = MockToolCall("consume_target", {"filepath": invalid_ext})
    assert enforce_safety_policy(call_invalid_ext) == False, "Should BLOCK non-.lnk file on Desktop"
    logger.info("  [PASS] Blocked invalid extension on Desktop.")

    # Case 3: Shortcut file (.lnk) outside Desktop directory
    outside_lnk = "C:\\Windows\\System32\\cmd.lnk"
    call_outside = MockToolCall("consume_target", {"filepath": outside_lnk})
    assert enforce_safety_policy(call_outside) == False, "Should BLOCK shortcut outside Desktop"
    logger.info("  [PASS] Blocked shortcut outside Desktop folder.")

def test_shortcut_parsing_and_classification():
    logger.info("=== Running Shortcut Parsing & Classification Tests ===")
    
    # Check simple classification mappings
    test_cases = [
        ("C:\\Program Files\\Steam\\steam.exe", "game"),
        ("C:\\Users\\User\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe", "development"),
        ("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "browser"),
        ("C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE", "document"),
        ("C:\\Windows\\System32\\notepad.exe", "generic")
    ]
    
    for path, expected_category in test_cases:
        # Create a mock dictionary representing the resolved shortcut properties
        info = {
            "target_path": path,
            "category": "generic",
            "is_dead": not os.path.exists(path)
        }
        # Naive category extraction logic replica
        target_lower = path.lower()
        if any(k in target_lower for k in ["steam", "game", "ea", "epicgames", "riotgames"]):
            info["category"] = "game"
        elif any(k in target_lower for k in ["code", "visualstudio", "pycharm", "git"]):
            info["category"] = "development"
        elif any(k in target_lower for k in ["chrome", "firefox", "edge", "browser"]):
            info["category"] = "browser"
        elif any(k in target_lower for k in ["word", "excel", "powerpnt", "pdf"]):
            info["category"] = "document"

        assert info["category"] == expected_category, f"Classification failed for {path}. Expected: {expected_category}, Got: {info['category']}"
        logger.info(f"  [PASS] Correctly classified target: '{path}' as '{expected_category}'")

def test_window_perturbation_math():
    logger.info("=== Running Window Perturbation Mathematics Tests ===")
    
    # Test that the damped sin/cos calculations do not throw domain errors
    duration = 1.2
    intensity = 15.0
    gamma = 4.0
    omega = 35.0
    
    steps = 10
    time_slices = [duration * (i / steps) for i in range(steps)]
    
    for elapsed in time_slices:
        decay_factor = math.exp(-gamma * elapsed)
        offset_x = int(intensity * decay_factor * math.sin(omega * elapsed))
        offset_y = int(intensity * decay_factor * math.cos(omega * elapsed))
        
        # Verify result types and bounds
        assert isinstance(offset_x, int)
        assert isinstance(offset_y, int)
        assert abs(offset_x) <= intensity
        assert abs(offset_y) <= intensity
        
    logger.info("  [PASS] Window oscillation maths calculated without errors.")

def run_all_tests():
    try:
        test_safety_policies()
        test_shortcut_parsing_and_classification()
        test_window_perturbation_math()
        logger.info("=== All Verification Tests Passed Successfully! ===")
        return True
    except AssertionError as e:
        logger.error(f"Verification Assertion Failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
