"""Token encryption utilities for secure storage."""

from cryptography.fernet import Fernet
from app.core.config import settings


# Generate a key from the JWT secret (ensure it's 32 bytes for Fernet)
def _get_encryption_key() -> bytes:
    """
    Generate Fernet encryption key from JWT secret.
    
    Fernet requires a 32-byte base64-encoded key.
    We use the JWT secret as a seed for consistency.
    """
    import hashlib
    import base64
    
    # Create a SHA-256 hash of the JWT secret (32 bytes)
    hashed = hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest()
    # Fernet needs base64-encoded key
    return base64.urlsafe_b64encode(hashed)


_fernet = Fernet(_get_encryption_key())


def encrypt_token(token: str) -> str:
    """
    Encrypt an access token for secure storage.
    
    Args:
        token: Plain text access token
        
    Returns:
        Encrypted token as string
        
    Example:
        encrypted = encrypt_token("github_pat_abc123")
        # Returns: "gAAAAAB..."
    """
    if not token:
        raise ValueError("Token cannot be empty")
    
    encrypted_bytes = _fernet.encrypt(token.encode())
    return encrypted_bytes.decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a stored access token.
    
    Args:
        encrypted_token: Encrypted token string
        
    Returns:
        Decrypted plain text token
        
    Raises:
        ValueError: If token is invalid or corrupted
        
    Example:
        token = decrypt_token("gAAAAAB...")
        # Returns: "github_pat_abc123"
    """
    if not encrypted_token:
        raise ValueError("Encrypted token cannot be empty")
    
    try:
        decrypted_bytes = _fernet.decrypt(encrypted_token.encode())
        return decrypted_bytes.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt token: {str(e)}")
