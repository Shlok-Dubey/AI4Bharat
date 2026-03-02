"""
Password hashing service using bcrypt.

This module provides secure password hashing and verification functionality
using bcrypt with a cost factor of 12 as specified in requirements 1.1 and 11.1.
"""

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with cost factor 12.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password as a string
        
    Requirements: 1.1, 11.1
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt with cost factor 12 and hash the password
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string for storage
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against a bcrypt hash.
    
    Args:
        password: Plain text password to verify
        hashed_password: Bcrypt hashed password to check against
        
    Returns:
        True if password matches, False otherwise
        
    Requirements: 1.1, 11.1
    """
    # Convert both to bytes
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    # Verify password
    return bcrypt.checkpw(password_bytes, hashed_bytes)
