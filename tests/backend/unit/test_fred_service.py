"""
Unit Tests for FRED Service
Tests Federal Reserve Economic Data API integration, caching, and data processing.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import httpx
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../backend'))

from services.fred_service import FREDService, TREASURY_SERIES, ECONOMIC_SERIES, _cache_get, _cache_set, _cache


class TestFREDService:
    """Test FRED API service functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.service = FREDService()
        # Clear cache before each test
        _cache.clear()
        
    def teardown_method(self):
        """Cleanup after each test."""
        _cache.clear()
        
    # ================================================================
    # INITIALIZATION TESTS
    # ================================================================
    
    def test_service_initialization(self):
        """Test FRED service initialization."""
        service = FREDService()
        
        assert hasattr(service, 'api_key')
        assert hasattr(service, 'client')
        assert isinstance(service.client, httpx.Client)
        
    def test_service_initialization_no_api_key(self):
        """Test service initialization without API key."""
        with patch('services.fred_service.Config.FRED_API_KEY', None):
            service = FREDService()
            assert service.api_key is None
            
    # ================================================================
    # CACHE FUNCTIONALITY TESTS
    # ================================================================
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        key = "test_key"
        data = {"test": "data"}
        
        # Set cache
        _cache_set(key, data)
        
        # Get from cache
        cached_data = _cache_get(key)
        
        assert cached_data == data
        
    def test_cache_expiration(self):
        """Test cache expiration functionality."""
        key = "test_key"
        data = {"test": "data"}
        
        # Set cache with very short TTL
        _cache_set(key, data)
        
        # Should be available immediately
        assert _cache_get(key, ttl=1) == data
        
        # Mock time passage
        with patch('time.time', return_value=time.time() + 2):
            # Should be expired
            assert _cache_get(key, ttl=1) is None
            
    def test_cache_miss(self):
        """Test cache miss behavior."""
        # Non-existent key should return None
        assert _cache_get("non_existent_key") is None
        
    def test_cache_overwrite(self):
        """Test cache overwrite behavior."""
        key = "test_key"
        data1 = {"version": 1}
        data2 = {"version": 2}
        
        _cache_set(key, data1)
        assert _cache_get(key)["version"] == 1
        
        _cache_set(key, data2)
        assert _cache_get(key)["version"] == 2
        
    # ================================================================
    # API REQUEST TESTS
    # ================================================================
    
    def test_fetch_success(self):
        """Test successful API fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {"observations": [{"date": "2024-01-01", "value": "4.25"}]}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(self.service.client, 'get', return_value=mock_response):
            result = self.service._fetch("series/observations", {"series_id": "DGS10"})
            
            assert "observations" in result
            assert result["observations"][0]["value"] == "4.25"
            
    def test_fetch_no_api_key(self):
        """Test fetch without API key."""
        service = FREDService()
        service.api_key = None
        
        result = service._fetch("series/observations")
        
        assert "error" in result
        assert result["error"] == "FRED API key not configured"
        
    def test_fetch_http_error(self):
        """Test fetch with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=Mock()
        )
        
        with patch.object(self.service.client, 'get', return_value=mock_response):
            result = self.service._fetch("invalid/endpoint")
            
            assert "error" in result
            
    def test_fetch_network_error(self):
        """Test fetch with network error."""
        with patch.object(self.service.client, 'get', side_effect=httpx.ConnectError("Connection failed")):
            result = self.service._fetch("series/observations")
            
            assert "error" in result
            assert "Connection failed" in result["error"]
            
    def test_fetch_timeout_error(self):
        """Test fetch with timeout error."""
        with patch.object(self.service.client, 'get', side_effect=httpx.TimeoutException("Request timeout")):
            result = self.service._fetch("series/observations")
            
            assert "error" in result
            assert "Request timeout" in result["error"]
            
    # ================================================================
    # SERIES DATA TESTS
    # ================================================================
    
    def test_get_series_success(self):
        """Test successful series data retrieval."""
        mock_observations = [
            {"date": "2024-01-01", "value": "4.25"},
            {"date": "2024-01-02", "value": "4.26"},
            {"date": "2024-01-03", "value": "4.24"}
        ]
        
        mock_response = {"observations": mock_observations}
        
        with patch.object(self.service, '_fetch', return_value=mock_response):
            result = self.service.get_series("DGS10")
            
            assert len(result) == 3
            assert result[0]["date"] == "2024-01-01"
            assert result[0]["value"] == "4.25"
            
    def test_get_series_with_limit(self):
        """Test series data retrieval with limit."""
        mock_response = {"observations": [{"date": "2024-01-01", "value": "4.25"}]}
        
        with patch.object(self.service, '_fetch', return_value=mock_response) as mock_fetch:
            self.service.get_series("DGS10", limit=100)
            
            # Check that limit parameter was passed
            call_args = mock_fetch.call_args
            assert call_args[1]["limit"] == 100
            
    def test_get_series_cache_hit(self):
        """Test series data cache hit."""
        series_id = "DGS10"
        limit = 365
        cache_key = f"fred_series_{series_id}_{limit}"
        
        # Pre-populate cache
        cached_data = [{"date": "2024-01-01", "value": "4.25"}]
        _cache_set(cache_key, cached_data)
        
        # Should return cached data without API call
        with patch.object(self.service, '_fetch') as mock_fetch:
            result = self.service.get_series(series_id, limit)
            
            assert result == cached_data
            mock_fetch.assert_not_called()
            
    def test_get_series_cache_miss(self):
        """Test series data cache miss."""
        mock_observations = [{"date": "2024-01-01", "value": "4.25"}]
        mock_response = {"observations": mock_observations}
        
        with patch.object(self.service, '_fetch', return_value=mock_response):
            result = self.service.get_series("DGS10")
            
            # Should make API call and cache result
            assert result == mock_observations
            
            # Verify data was cached
            cache_key = "fred_series_DGS10_365"
            assert _cache_get(cache_key) == mock_observations
            
    def test_get_series_error_handling(self):
        """Test series data error handling."""
        error_response = {"error": "Series not found"}
        
        with patch.object(self.service, '_fetch', return_value=error_response):
            result = self.service.get_series("INVALID_SERIES")
            
            assert result == []  # Should return empty list on error
            
    # ================================================================
    # TREASURY YIELD TESTS
    # ================================================================
    
    def test_get_treasury_yields_success(self):
        """Test successful treasury yields retrieval."""
        # Mock responses for different maturities
        mock_responses = {}
        for maturity, series_id in TREASURY_SERIES.items():
            mock_responses[series_id] = [{"date": "2024-01-01", "value": "4.25"}]
            
        def mock_get_series(series_id, limit=None):
            return mock_responses.get(series_id, [])
            
        with patch.object(self.service, 'get_series', side_effect=mock_get_series):
            result = self.service.get_treasury_yields()
            
            assert len(result) == len(TREASURY_SERIES)
            
            # Check structure
            for item in result:
                assert "maturity" in item
                assert "yield" in item
                assert "date" in item
                
    def test_get_treasury_yields_missing_data(self):
        """Test treasury yields with missing data."""
        def mock_get_series(series_id, limit=None):
            # Return empty for some series
            if series_id == "DGS1MO":
                return []
            return [{"date": "2024-01-01", "value": "4.25"}]
            
        with patch.object(self.service, 'get_series', side_effect=mock_get_series):
            result = self.service.get_treasury_yields()
            
            # Should still return results for available series
            assert len(result) == len(TREASURY_SERIES) - 1  # Minus the missing one
            
    def test_get_treasury_yields_invalid_values(self):
        """Test treasury yields with invalid values."""
        def mock_get_series(series_id, limit=None):
            return [
                {"date": "2024-01-01", "value": "4.25"},
                {"date": "2024-01-02", "value": "."},  # Invalid value
                {"date": "2024-01-03", "value": ""},   # Empty value
                {"date": "2024-01-04", "value": "4.26"}
            ]
            
        with patch.object(self.service, 'get_series', side_effect=mock_get_series):
            result = self.service.get_treasury_yields()
            
            # Should filter out invalid values
            for item in result:
                assert isinstance(item["yield"], (int, float))
                assert item["yield"] > 0
                
    # ================================================================
    # ECONOMIC INDICATORS TESTS
    # ================================================================
    
    def test_get_economic_indicators_success(self):
        """Test successful economic indicators retrieval."""
        mock_responses = {}
        for series_id in ECONOMIC_SERIES.keys():
            mock_responses[series_id] = [{"date": "2024-01-01", "value": "5.25"}]
            
        def mock_get_series(series_id, limit=None):
            return mock_responses.get(series_id, [])
            
        with patch.object(self.service, 'get_series', side_effect=mock_get_series):
            result = self.service.get_economic_indicators()
            
            assert len(result) == len(ECONOMIC_SERIES)
            
            # Check structure
            for item in result:
                assert "series_id" in item
                assert "name" in item
                assert "category" in item
                assert "value" in item
                assert "date" in item
                
    def test_get_economic_indicators_by_category(self):
        """Test economic indicators filtered by category."""
        def mock_get_series(series_id, limit=None):
            return [{"date": "2024-01-01", "value": "5.25"}]
            
        with patch.object(self.service, 'get_series', side_effect=mock_get_series):
            # Test rates category
            rates = self.service.get_economic_indicators(category="rates")
            
            for item in rates:
                series_info = ECONOMIC_SERIES[item["series_id"]]
                assert series_info["category"] == "rates"
                
    # ================================================================
    # YIELD CURVE TESTS
    # ================================================================
    
    def test_get_yield_curve_success(self):
        """Test successful yield curve retrieval."""
        def mock_get_series(series_id, limit=None):
            return [{"date": "2024-01-01", "value": "4.25"}]
            
        with patch.object(self.service, 'get_series', side_effect=mock_get_series):
            result = self.service.get_yield_curve()
            
            assert len(result) > 0
            
            # Check structure and ordering
            prev_maturity_years = 0
            for point in result:
                assert "maturity" in point
                assert "yield" in point
                assert "maturity_years" in point
                
                # Should be ordered by maturity
                assert point["maturity_years"] >= prev_maturity_years
                prev_maturity_years = point["maturity_years"]
                
    def test_get_yield_curve_historical(self):
        """Test historical yield curve retrieval."""
        def mock_get_series(series_id, limit=None):
            return [
                {"date": "2024-01-03", "value": "4.25"},
                {"date": "2024-01-02", "value": "4.24"},
                {"date": "2024-01-01", "value": "4.23"}
            ]
            
        with patch.object(self.service, 'get_series', side_effect=mock_get_series):
            result = self.service.get_yield_curve(days_back=3)
            
            # Should return multiple dates
            dates = set(point["date"] for point in result)
            assert len(dates) <= 3  # Up to 3 days of data
            
    # ================================================================
    # INVERSION DETECTION TESTS
    # ================================================================
    
    def test_detect_yield_curve_inversion_normal(self):
        """Test inversion detection with normal curve."""
        # Normal upward sloping curve
        curve_data = [
            {"maturity": "2Y", "yield": 4.0, "maturity_years": 2},
            {"maturity": "10Y", "yield": 4.5, "maturity_years": 10}
        ]
        
        with patch.object(self.service, 'get_yield_curve', return_value=curve_data):
            result = self.service.detect_yield_curve_inversion()
            
            assert result["2s10s"]["inverted"] is False
            assert result["2s10s"]["spread"] == 0.5  # 10Y - 2Y
            
    def test_detect_yield_curve_inversion_inverted(self):
        """Test inversion detection with inverted curve."""
        # Inverted curve
        curve_data = [
            {"maturity": "2Y", "yield": 4.5, "maturity_years": 2},
            {"maturity": "10Y", "yield": 4.0, "maturity_years": 10}
        ]
        
        with patch.object(self.service, 'get_yield_curve', return_value=curve_data):
            result = self.service.detect_yield_curve_inversion()
            
            assert result["2s10s"]["inverted"] is True
            assert result["2s10s"]["spread"] == -0.5  # 10Y - 2Y
            
    def test_detect_yield_curve_inversion_missing_data(self):
        """Test inversion detection with missing data."""
        # Missing 10Y data
        curve_data = [
            {"maturity": "2Y", "yield": 4.0, "maturity_years": 2}
        ]
        
        with patch.object(self.service, 'get_yield_curve', return_value=curve_data):
            result = self.service.detect_yield_curve_inversion()
            
            assert result["2s10s"]["inverted"] is None
            assert result["2s10s"]["spread"] is None
            
    # ================================================================
    # PERFORMANCE TESTS
    # ================================================================
    
    def test_cache_performance(self):
        """Test cache performance for repeated requests."""
        import time
        
        # Pre-populate cache
        cache_key = "fred_series_DGS10_365"
        cached_data = [{"date": "2024-01-01", "value": "4.25"}]
        _cache_set(cache_key, cached_data)
        
        # Measure cache hit performance
        start_time = time.time()
        for _ in range(1000):
            _cache_get(cache_key)
        cache_time = time.time() - start_time
        
        # Should be very fast (under 10ms for 1000 operations)
        assert cache_time < 0.01
        
    def test_concurrent_cache_access(self):
        """Test concurrent cache access safety."""
        import threading
        
        results = []
        
        def cache_worker():
            for i in range(100):
                key = f"test_key_{i}"
                data = {"value": i}
                _cache_set(key, data)
                retrieved = _cache_get(key)
                results.append(retrieved["value"] == i)
                
        # Run multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=cache_worker)
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
            
        # All operations should succeed
        assert all(results)
        
    # ================================================================
    # ERROR HANDLING TESTS
    # ================================================================
    
    def test_malformed_api_response(self):
        """Test handling of malformed API responses."""
        malformed_responses = [
            {},  # Empty response
            {"error": "Invalid series ID"},  # Error response
            {"observations": None},  # Null observations
            {"observations": "not_a_list"},  # Invalid observations type
        ]
        
        for response in malformed_responses:
            with patch.object(self.service, '_fetch', return_value=response):
                result = self.service.get_series("DGS10")
                assert isinstance(result, list)  # Should always return list
                
    def test_invalid_series_id(self):
        """Test handling of invalid series IDs."""
        error_response = {"error_message": "Bad Request. The series does not exist."}
        
        with patch.object(self.service, '_fetch', return_value=error_response):
            result = self.service.get_series("INVALID_SERIES")
            assert result == []
            
    def test_rate_limit_handling(self):
        """Test handling of API rate limits."""
        rate_limit_response = {"error_message": "Too Many Requests"}
        
        with patch.object(self.service, '_fetch', return_value=rate_limit_response):
            result = self.service.get_series("DGS10")
            assert result == []
            
    # ================================================================
    # DATA VALIDATION TESTS
    # ================================================================
    
    def test_data_type_validation(self):
        """Test validation of data types in responses."""
        mixed_data = [
            {"date": "2024-01-01", "value": "4.25"},  # Valid
            {"date": "2024-01-02", "value": 4.26},    # Number instead of string
            {"date": "2024-01-03", "value": "."},     # Missing value indicator
            {"date": "2024-01-04", "value": ""},      # Empty string
            {"date": "2024-01-05", "value": None},    # Null value
        ]
        
        mock_response = {"observations": mixed_data}
        
        with patch.object(self.service, '_fetch', return_value=mock_response):
            result = self.service.get_series("DGS10")
            
            # Should handle all data types gracefully
            assert len(result) == 5
            
    def test_date_format_validation(self):
        """Test validation of date formats."""
        date_formats = [
            {"date": "2024-01-01", "value": "4.25"},  # Standard format
            {"date": "2024-1-1", "value": "4.25"},    # No leading zeros
            {"date": "01/01/2024", "value": "4.25"},  # Different format
            {"date": "", "value": "4.25"},            # Empty date
            {"date": None, "value": "4.25"},          # Null date
        ]
        
        mock_response = {"observations": date_formats}
        
        with patch.object(self.service, '_fetch', return_value=mock_response):
            result = self.service.get_series("DGS10")
            
            # Should handle various date formats
            assert len(result) == 5


class TestFREDConstants:
    """Test FRED service constants and configuration."""
    
    def test_treasury_series_completeness(self):
        """Test that all major Treasury maturities are included."""
        expected_maturities = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
        
        for maturity in expected_maturities:
            assert maturity in TREASURY_SERIES
            assert isinstance(TREASURY_SERIES[maturity], str)
            assert len(TREASURY_SERIES[maturity]) > 0
            
    def test_economic_series_structure(self):
        """Test economic series structure and completeness."""
        required_categories = ["rates", "inflation", "spreads", "employment", "growth"]
        
        categories_found = set()
        for series_id, info in ECONOMIC_SERIES.items():
            assert isinstance(info, dict)
            assert "name" in info
            assert "category" in info
            assert isinstance(info["name"], str)
            assert isinstance(info["category"], str)
            
            categories_found.add(info["category"])
            
        # Should have all major categories
        for category in required_categories:
            assert category in categories_found
            
    def test_series_id_format(self):
        """Test FRED series ID format consistency."""
        all_series_ids = list(TREASURY_SERIES.values()) + list(ECONOMIC_SERIES.keys())
        
        for series_id in all_series_ids:
            # Series IDs should be uppercase alphanumeric
            assert series_id.isupper()
            assert series_id.replace("Y", "").replace("M", "").replace("S", "").replace("L", "").isalnum()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])