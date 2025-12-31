import re
import random
import string

def slugify(text: str) -> str:
    """
    Convert a string to a slug.
    1. Handle None/Empty
    2. Convert to lowercase
    3. Replace non-alphanumeric characters with hyphens
    4. Remove multiple hyphens
    5. Strip leading/trailing hyphens
    """
    if not text:
        return "dream"
        
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'-+', '-', text)
    res = text.strip('-')
    return res if res else "dream"

def generate_unique_slug(base_slug: str) -> str:
    """
    Generate a unique slug by appending a random suffix.
    This is a helper; uniqueness checks should still be done against the DB.
    """
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{base_slug}-{suffix}"
