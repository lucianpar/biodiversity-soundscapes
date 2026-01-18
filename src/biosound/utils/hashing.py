"""
Deterministic hashing utilities for stable species-to-music mappings.

All functions produce identical outputs for identical inputs across runs.
NO random functions are used - only cryptographic hashes.
"""

import hashlib
from typing import Union


def _hash_bytes(key: str) -> bytes:
    """Get SHA-256 hash bytes for a string key."""
    return hashlib.sha256(key.encode("utf-8")).digest()


def stable_int(key: str, mod: int) -> int:
    """
    Generate a stable integer in [0, mod) from a string key.
    
    Uses SHA-256 hash to ensure deterministic mapping.
    
    Args:
        key: String to hash (e.g., species_id, "species_id:pan")
        mod: Modulus for output range
        
    Returns:
        Integer in [0, mod)
        
    Example:
        >>> stable_int("american_robin", 128)
        73  # Always returns same value for same input
    """
    if mod <= 0:
        raise ValueError(f"mod must be positive, got {mod}")
    
    hash_bytes = _hash_bytes(key)
    # Use first 8 bytes as integer
    hash_int = int.from_bytes(hash_bytes[:8], byteorder="big")
    return hash_int % mod


def stable_float01(key: str) -> float:
    """
    Generate a stable float in [0.0, 1.0) from a string key.
    
    Uses SHA-256 hash to ensure deterministic mapping.
    
    Args:
        key: String to hash
        
    Returns:
        Float in [0.0, 1.0)
        
    Example:
        >>> stable_float01("stellers_jay:velocity")
        0.4521...  # Always returns same value for same input
    """
    hash_bytes = _hash_bytes(key)
    # Use first 8 bytes, divide by max value
    hash_int = int.from_bytes(hash_bytes[:8], byteorder="big")
    max_val = 2**64
    return hash_int / max_val


def stable_shuffle_key(year: int, species_id: str) -> int:
    """
    Generate a stable sort key for shuffling species within a year.
    
    Args:
        year: Year for context
        species_id: Species identifier
        
    Returns:
        Integer sort key
    """
    return stable_int(f"{year}:{species_id}", 10**18)


def content_hash(data: Union[str, bytes]) -> str:
    """
    Generate a content hash for data integrity verification.
    
    Args:
        data: String or bytes to hash
        
    Returns:
        Hex string of SHA-256 hash (first 16 chars)
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:16]
