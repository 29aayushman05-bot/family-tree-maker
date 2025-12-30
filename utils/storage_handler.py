import json
import os
from pathlib import Path

CACHE_FILE = ".tree_cache.json"

def save_to_browser(tree_data):
    """Save tree data to local cache file"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(tree_data, f, indent=2)
        print(f"✓ Saved to {CACHE_FILE}")
    except Exception as e:
        print(f"Error saving: {e}")

def load_from_browser():
    """Load tree data from local cache file"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✓ Loaded from {CACHE_FILE}")
                return data
        return None
    except Exception as e:
        print(f"Error loading: {e}")
        return None

def clear_browser_storage():
    """Clear cache file"""
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
            print(f"✓ Cleared {CACHE_FILE}")
    except Exception as e:
        print(f"Error clearing: {e}")
