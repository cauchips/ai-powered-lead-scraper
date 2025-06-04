import json

def load_cache(filename):
    """
    Load a JSON cache from disk; return {} if not found.
    """
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        return {}

def save_cache(filename, data):
    """
    Save a dict to a JSON file.
    """
    try:
        with open(filename, "w") as f:
            json.dump(data, f)
    except:
        pass
