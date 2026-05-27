"""
Unit Tests for Authentication System
Tests JWT token generation, validation, password hashing, and auth middleware.
"""

import pytest
import jwt
import bcrypt
import time
from unittest.mock import Mock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../backend'))

from middleware.auth import (
    generate_token, decode_token, hash_password, verify_password,
    require_auth, optional_auth
)
from config import Config


class TestTokenGeneration:
    """Test JWT token generation and validation."""
    
    def test_generate_token_basic(self):
        """Test basic token generation."""
        user_id = "user123"
        email = "test@example.com"
        
        token = generate_token(user_id, email)
        
        # Token should be a string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Should be decodable
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert "iat" in payload
        assert "exp" in payload
        
    def test_generate_token_expiration(self):
        """Test token expiration time."""
        token = generate_token("user123", "test@example.com")
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        
        # Expiration should be JWT_EXPIRATION_HOURS from now
        expected_exp = payload["iat"] + (Config.JWT_EXPIRATION_HOURS * 3600)
        assert payload["exp"] == expected_exp
        
    def test_generate_token_different_users(self):
        """Test token generation for different users."""
        token1 = generate_token("user1", "user1@example.com")
        token2 = generate_token("user2", "user2@example.com")
        
        # Tokens should be different
        assert token1 != token2
        
        # But both should be valid
        payload1 = jwt.decode(token1, Config.JWT_SECRET, algorithms=["HS256"])
        payload2 = jwt.decode(token2, Config.JWT_SECRET, algorithms=["HS256"])
        
        assert payload1["user_id"] == "user1"
        assert payload2["user_id"] == "user2"
        
    def test_generate_token_special_characters(self):
        """Test token generation with special characters in email."""
        special_emails = [
            "test+tag@example.com",
            "user.name@sub.domain.com",
            "test_user@example-domain.co.uk"
        ]
        
        for email in special_emails:
            token = generate_token("user123", email)
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
            assert payload["email"] == email


class TestTokenDecoding:
    """Test JWT token decoding and validation."""
    
    def test_decode_valid_token(self):
        """Test decoding valid token."""
        user_id = "user123"
        email = "test@example.com"
        
        token = generate_token(user_id, email)
        result = decode_token(token)
        
        assert "error" not in result
        assert result["user_id"] == user_id
        assert result["email"] == email
        
    def test_decode_expired_token(self):
        """Test decoding expired token."""
        # Create token with past expiration
        payload = {
            "user_id": "user123",
            "email": "test@example.com",
            "iat": int(time.time()) - 7200,  # 2 hours ago
            "exp": int(time.time()) - 3600,  # 1 hour ago (expired)
        }
        
        expired_token = jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")
        result = decode_token(expired_token)
        
        assert "error" in result
        assert result["error"] == "Token expired"
        
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        invalid_tokens = [
            "invalid.token.here",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
            "",
            "not-a-jwt-token"
        ]
        
        for invalid_token in invalid_tokens:
            result = decode_token(invalid_token)
            assert "error" in result
            assert result["error"] == "Invalid token"
            
    def test_decode_wrong_secret(self):
        """Test decoding token with wrong secret."""
        # Create token with different secret
        payload = {
            "user_id": "user123",
            "email": "test@example.com",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        
        wrong_secret_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        result = decode_token(wrong_secret_token)
        
        assert "error" in result
        assert result["error"] == "Invalid token"
        
    def test_decode_malformed_payload(self):
        """Test decoding token with malformed payload."""
        # Create token with missing required fields
        payload = {
            "user_id": "user123",
            # Missing email, iat, exp
        }
        
        malformed_token = jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")
        
        # Should still decode but may fail validation in middleware
        result = decode_token(malformed_token)
        assert result["user_id"] == "user123"
        assert "email" not in result


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password_basic(self):
        """Test basic password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Hash should be different from original
        assert hashed != password
        
        # Hash should be a string
        assert isinstance(hashed, str)
        
        # Hash should have bcrypt format
        assert hashed.startswith("$2b$")
        
    def test_hash_password_different_results(self):
        """Test that same password produces different hashes (salt)."""
        password = "same_password"
        
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
        
    def test_hash_password_special_characters(self):
        """Test password hashing with special characters."""
        special_passwords = [
            "p@ssw0rd!",
            "пароль123",  # Cyrillic
            "密码123",     # Chinese
            "🔒secure🔑",  # Emojis
            "a" * 100,     # Long password
            ""             # Empty password
        ]
        
        for password in special_passwords:
            hashed = hash_password(password)
            assert verify_password(password, hashed)
            
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "correct_password"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
        
    def test_verify_password_edge_cases(self):
        """Test password verification edge cases."""
        password = "test_password"
        hashed = hash_password(password)
        
        # Case sensitivity
        assert verify_password("TEST_PASSWORD", hashed) is False
        assert verify_password("Test_Password", hashed) is False
        
        # Extra characters
        assert verify_password(password + " ", hashed) is False
        assert verify_password(" " + password, hashed) is False
        
        # Empty password vs hash
        empty_hash = hash_password("")
        assert verify_password("", empty_hash) is True
        assert verify_password("not_empty", empty_hash) is False


class TestAuthMiddleware:
    """Test authentication middleware decorators."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.valid_token = generate_token("user123", "test@example.com")
        self.expired_token = jwt.encode({
            "user_id": "user123",
            "email": "test@example.com",
            "iat": int(time.time()) - 7200,
            "exp": int(time.time()) - 3600,
        }, Config.JWT_SECRET, algorithm="HS256")
        
    def test_require_auth_valid_token(self):
        """Test require_auth decorator with valid token."""
        @require_auth
        def protected_route():
            return {"success": True, "message": "Access granted"}
            
        # Mock Flask request with valid Authorization header
        with patch('middleware.auth.request') as mock_request, \
             patch('middleware.auth.g') as mock_g:
            
            mock_request.headers.get.return_value = f"Bearer {self.valid_token}"
            
            result = protected_route()
            
            # Should call the protected function
            assert result["success"] is True
            assert result["message"] == "Access granted"
            
            # Should set g.user_id and g.user_email
            assert mock_g.user_id == "user123"
            assert mock_g.user_email == "test@example.com"
            
    def test_require_auth_missing_header(self):
        """Test require_auth decorator with missing Authorization header."""
        @require_auth
        def protected_route():
            return {"success": True}
            
        with patch('middleware.auth.request') as mock_request, \
             patch('middleware.auth.jsonify') as mock_jsonify:
            
            mock_request.headers.get.return_value = ""
            mock_jsonify.return_value = ("Unauthorized", 401)
            
            result = protected_route()
            
            # Should return 401 error
            assert result == ("Unauthorized", 401)
            
    def test_require_auth_invalid_format(self):
        """Test require_auth decorator with invalid header format."""
        @require_auth
        def protected_route():
            return {"success": True}
            
        invalid_headers = [
            "InvalidFormat",
            "Basic dXNlcjpwYXNz",  # Basic auth instead of Bearer
            "Bearer",  # Missing token
            "Bearer ",  # Empty token
        ]
        
        for header in invalid_headers:
            with patch('middleware.auth.request') as mock_request, \
                 patch('middleware.auth.jsonify') as mock_jsonify:
                
                mock_request.headers.get.return_value = header
                mock_jsonify.return_value = ("Unauthorized", 401)
                
                result = protected_route()
                assert result == ("Unauthorized", 401)
                
    def test_require_auth_expired_token(self):
        """Test require_auth decorator with expired token."""
        @require_auth
        def protected_route():
            return {"success": True}
            
        with patch('middleware.auth.request') as mock_request, \
             patch('middleware.auth.jsonify') as mock_jsonify:
            
            mock_request.headers.get.return_value = f"Bearer {self.expired_token}"
            mock_jsonify.return_value = ("Token expired", 401)
            
            result = protected_route()
            assert result == ("Token expired", 401)
            
    def test_require_auth_invalid_token(self):
        """Test require_auth decorator with invalid token."""
        @require_auth
        def protected_route():
            return {"success": True}
            
        with patch('middleware.auth.request') as mock_request, \
             patch('middleware.auth.jsonify') as mock_jsonify:
            
            mock_request.headers.get.return_value = "Bearer invalid.token.here"
            mock_jsonify.return_value = ("Invalid token", 401)
            
            result = protected_route()
            assert result == ("Invalid token", 401)
            
    def test_optional_auth_valid_token(self):
        """Test optional_auth decorator with valid token."""
        @optional_auth
        def public_route():
            return {"success": True, "authenticated": hasattr(Mock(), 'user_id')}
            
        with patch('middleware.auth.request') as mock_request, \
             patch('middleware.auth.g') as mock_g:
            
            mock_request.headers.get.return_value = f"Bearer {self.valid_token}"
            
            result = public_route()
            
            # Should execute function
            assert result["success"] is True
            
            # Should set user info in g
            assert mock_g.user_id == "user123"
            assert mock_g.user_email == "test@example.com"
            
    def test_optional_auth_no_token(self):
        """Test optional_auth decorator with no token."""
        @optional_auth
        def public_route():
            return {"success": True}
            
        with patch('middleware.auth.request') as mock_request, \
             patch('middleware.auth.g') as mock_g:
            
            mock_request.headers.get.return_value = ""
            
            result = public_route()
            
            # Should still execute function
            assert result["success"] is True
            
            # Should not set user info
            assert not hasattr(mock_g, 'user_id')
            assert not hasattr(mock_g, 'user_email')
            
    def test_optional_auth_invalid_token(self):
        """Test optional_auth decorator with invalid token."""
        @optional_auth
        def public_route():
            return {"success": True}
            
        with patch('middleware.auth.request') as mock_request, \
             patch('middleware.auth.g') as mock_g:
            
            mock_request.headers.get.return_value = "Bearer invalid.token"
            
            result = public_route()
            
            # Should still execute function (optional auth)
            assert result["success"] is True
            
            # Should not set user info due to invalid token
            assert not hasattr(mock_g, 'user_id')


class TestAuthSecurity:
    """Test authentication security aspects."""
    
    def test_token_timing_attack_resistance(self):
        """Test resistance to timing attacks on token validation."""
        import time
        
        valid_token = generate_token("user123", "test@example.com")
        invalid_token = "invalid.token.here"
        
        # Measure time for valid token
        start = time.time()
        decode_token(valid_token)
        valid_time = time.time() - start
        
        # Measure time for invalid token
        start = time.time()
        decode_token(invalid_token)
        invalid_time = time.time() - start
        
        # Times should be similar (within order of magnitude)
        # This is a basic check - real timing attack resistance requires more sophisticated testing
        assert abs(valid_time - invalid_time) < 0.1
        
    def test_password_hash_timing_attack_resistance(self):
        """Test resistance to timing attacks on password verification."""
        import time
        
        password = "test_password"
        hashed = hash_password(password)
        wrong_password = "wrong_password"
        
        # Measure time for correct password
        start = time.time()
        verify_password(password, hashed)
        correct_time = time.time() - start
        
        # Measure time for wrong password
        start = time.time()
        verify_password(wrong_password, hashed)
        wrong_time = time.time() - start
        
        # bcrypt should have consistent timing regardless of correctness
        # Allow for some variance due to system load
        time_ratio = max(correct_time, wrong_time) / min(correct_time, wrong_time)
        assert time_ratio < 2.0  # Should be within 2x
        
    def test_token_secret_isolation(self):
        """Test that tokens can't be forged without secret."""
        # Try to create token with guessed secrets
        common_secrets = [
            "secret", "password", "key", "jwt", "token",
            "12345", "admin", "test", "", "null"
        ]
        
        for fake_secret in common_secrets:
            if fake_secret == Config.JWT_SECRET:
                continue  # Skip if it happens to match
                
            fake_token = jwt.encode({
                "user_id": "hacker",
                "email": "hacker@evil.com",
                "iat": int(time.time()),
                "exp": int(time.time()) + 3600,
            }, fake_secret, algorithm="HS256")
            
            result = decode_token(fake_token)
            assert "error" in result
            assert result["error"] == "Invalid token"
            
    def test_password_hash_uniqueness(self):
        """Test that password hashes are unique (proper salting)."""
        password = "same_password"
        hashes = set()
        
        # Generate 100 hashes of the same password
        for _ in range(100):
            hash_val = hash_password(password)
            hashes.add(hash_val)
            
        # All hashes should be unique
        assert len(hashes) == 100
        
    def test_token_payload_integrity(self):
        """Test that token payload can't be modified."""
        original_token = generate_token("user123", "test@example.com")
        
        # Decode to get parts
        header, payload, signature = original_token.split('.')
        
        # Try to modify payload (change user_id)
        import base64
        import json
        
        decoded_payload = json.loads(base64.urlsafe_b64decode(payload + '=='))
        decoded_payload["user_id"] = "hacker"
        
        modified_payload = base64.urlsafe_b64encode(
            json.dumps(decoded_payload).encode()
        ).decode().rstrip('=')
        
        # Create token with modified payload but original signature
        modified_token = f"{header}.{modified_payload}.{signature}"
        
        # Should be rejected
        result = decode_token(modified_token)
        assert "error" in result
        assert result["error"] == "Invalid token"


class TestAuthConfiguration:
    """Test authentication configuration and edge cases."""
    
    def test_jwt_expiration_configuration(self):
        """Test JWT expiration configuration."""
        # Test with different expiration times
        original_expiration = Config.JWT_EXPIRATION_HOURS
        
        try:
            # Test short expiration
            Config.JWT_EXPIRATION_HOURS = 1
            token = generate_token("user123", "test@example.com")
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
            
            expected_exp = payload["iat"] + 3600  # 1 hour
            assert payload["exp"] == expected_exp
            
            # Test long expiration
            Config.JWT_EXPIRATION_HOURS = 168  # 1 week
            token = generate_token("user123", "test@example.com")
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
            
            expected_exp = payload["iat"] + (168 * 3600)  # 1 week
            assert payload["exp"] == expected_exp
            
        finally:
            # Restore original configuration
            Config.JWT_EXPIRATION_HOURS = original_expiration
            
    def test_empty_user_data(self):
        """Test token generation with empty user data."""
        # Empty strings should still work
        token = generate_token("", "")
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        
        assert payload["user_id"] == ""
        assert payload["email"] == ""
        
    def test_unicode_user_data(self):
        """Test token generation with Unicode user data."""
        unicode_data = [
            ("用户123", "用户@example.com"),  # Chinese
            ("пользователь", "тест@example.com"),  # Cyrillic
            ("🚀user", "test🔥@example.com"),  # Emojis
        ]
        
        for user_id, email in unicode_data:
            token = generate_token(user_id, email)
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
            
            assert payload["user_id"] == user_id
            assert payload["email"] == email


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])