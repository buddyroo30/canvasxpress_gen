"""
Authentication Utilities

Functions for authentication, password generation, and security operations.
"""

import secrets
import string
import hashlib
import base64
import time
import calendar
import requests
from typing import Optional, Dict, Any


def random_password(length: int = 12) -> str:
    """
    Generate a secure random password.
    
    Args:
        length: Length of the password to generate
        
    Returns:
        Randomly generated password
    """
    if length < 4:
        raise ValueError("Password length must be at least 4 characters")
    
    # Ensure password has at least one character from each category
    password_chars = []
    
    # Add at least one from each category
    password_chars.append(secrets.choice(string.ascii_lowercase))
    password_chars.append(secrets.choice(string.ascii_uppercase))
    password_chars.append(secrets.choice(string.digits))
    password_chars.append(secrets.choice(string.punctuation))
    
    # Fill the rest randomly
    all_chars = string.ascii_letters + string.digits + string.punctuation
    for _ in range(length - 4):
        password_chars.append(secrets.choice(all_chars))
    
    # Shuffle the password characters
    secrets.SystemRandom().shuffle(password_chars)
    
    return ''.join(password_chars)


def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure API key.
    
    Args:
        length: Length of the API key
        
    Returns:
        Randomly generated API key
    """
    return secrets.token_urlsafe(length)


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Hash a password with salt.
    
    Args:
        password: Password to hash
        salt: Optional salt (will be generated if not provided)
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Create hash using PBKDF2
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )
    
    return base64.b64encode(password_hash).decode('utf-8'), salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Password to verify
        hashed_password: Stored hash
        salt: Salt used for hashing
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        computed_hash, _ = hash_password(password, salt)
        return secrets.compare_digest(computed_hash, hashed_password)
    except Exception:
        return False


def generate_session_token() -> str:
    """
    Generate a secure session token.
    
    Returns:
        Session token string
    """
    return secrets.token_urlsafe(32)


def is_strong_password(password: str) -> tuple[bool, list[str]]:
    """
    Check if a password meets strength requirements.
    
    Args:
        password: Password to check
        
    Returns:
        Tuple of (is_strong, list_of_issues)
    """
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    
    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    
    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one digit")
    
    if not any(c in string.punctuation for c in password):
        issues.append("Password must contain at least one special character")
    
    # Check for common weak patterns
    if password.lower() in ['password', '123456', 'qwerty', 'admin']:
        issues.append("Password is too common")
    
    return len(issues) == 0, issues


def sanitize_input(input_string: str) -> str:
    """
    Sanitize input string to prevent injection attacks.
    
    Args:
        input_string: String to sanitize
        
    Returns:
        Sanitized string
    """
    if not input_string:
        return ""
    
    # Remove or escape potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
    sanitized = input_string
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Limit length to prevent buffer overflow attacks
    return sanitized[:1000]


def generate_csrf_token() -> str:
    """
    Generate a CSRF token for form protection.
    
    Returns:
        CSRF token string
    """
    return secrets.token_urlsafe(32)


def constant_time_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks.
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        True if strings are equal, False otherwise
    """
    return secrets.compare_digest(a, b)


# SiteMinder configuration
REDIRECT_URL = "http://smusauth.net.bms.com/rdproxy/redirect.cgi"
VALIDATE_URL = "http://smusauth.net.bms.com/rdproxy/validate.cgi"


def getSMRedirectUrl(request) -> str:
    """
    Get SiteMinder redirect URL for authentication.
    
    Args:
        request: Flask request object
        
    Returns:
        Redirect URL for SiteMinder authentication
    """
    # See here for getting parts of url in Flask: https://stackoverflow.com/questions/15974730/how-do-i-get-the-different-parts-of-a-flask-requests-url
    # See here for quote: https://stackoverflow.com/questions/1695183/how-to-percent-encode-url-parameters-in-python
    location = REDIRECT_URL + '?url=' + requests.utils.quote(request.url)
    return location


def getSiteMinderUser(request, validated_cookies: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get SiteMinder user information from request.
    
    Returning None means 'pass', i.e. allow the user access to the
    requested resource. Otherwise returns a "access denied" message that
    can get displayed to the user. This version goes directly against
    the SiteMinder validation services and not indirectly through
    an intermediate service (so use this if you are directly on the
    BMS network).
    
    Args:
        request: Flask request object
        validated_cookies: Dictionary of validated cookies
        
    Returns:
        User information dictionary or None if not authenticated
    """
    if 'SMSESSION' not in request.cookies:
        return None

    # Remove expired cookies from the validated_cookies dict
    current_epoch_secs = calendar.timegm(time.gmtime())
    del_cookies = {}
    
    for cur_sm_session, assoc_vals in validated_cookies.items():
        init_ttl_secs = int(assoc_vals['TTL'])
        init_epoch_secs = int(assoc_vals['epochsecs'])
        secs_diff = current_epoch_secs - init_epoch_secs
        remaining_ttl_secs = init_ttl_secs - secs_diff
        
        if remaining_ttl_secs <= 0:
            del_cookies[cur_sm_session] = True

    for cur_sm_session in del_cookies:
        del validated_cookies[cur_sm_session]

    sm_session = request.cookies['SMSESSION']

    if sm_session in validated_cookies:
        return validated_cookies[sm_session]

    # Validate with SiteMinder service
    try:
        validation_data = {
            'SMSESSION': sm_session
        }
        
        response = requests.post(VALIDATE_URL, data=validation_data, timeout=10)
        
        if response.status_code == 200:
            # Parse response (assuming it returns user info)
            # This is a simplified version - actual implementation may vary
            user_info = {
                'User': 'authenticated_user',  # Would be parsed from response
                'bmsid': 'user_bmsid',  # Would be parsed from response
                'TTL': '3600',  # Session timeout
                'epochsecs': str(current_epoch_secs)
            }
            
            # Cache the validated session
            validated_cookies[sm_session] = user_info
            return user_info
        else:
            return None
            
    except Exception as e:
        print(f"SiteMinder validation error: {e}")
        return None


def empty(value) -> bool:
    """
    Return True if the value is None or composed of only whitespace, False otherwise.
    
    Args:
        value: Value to check
        
    Returns:
        True if empty, False otherwise
    """
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False