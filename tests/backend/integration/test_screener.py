import pytest
import json

class TestScreenerAPI:
    """
    Integration tests for Bond Screener API.
    """

    @pytest.fixture
    def sample_bonds(self, mock_db):
        bonds = [
            {
                "cusip": "123456789",
                "issuer": "Test Issuer A",
                "type": "corporate",
                "rating": "AAA",
                "sector": "Technology",
                "coupon_rate": 5.0,
                "price": 100.0,
                "maturity_date": "2030-01-01",
                "face_value": 100.0,
                "callable": False,
                "tax_exempt": False
            },
            {
                "cusip": "987654321",
                "issuer": "Muni Corp",
                "type": "municipal",
                "rating": "AA",
                "sector": "Government",
                "coupon_rate": 3.0,
                "price": 95.0,
                "maturity_date": "2035-01-01",
                "face_value": 100.0,
                "callable": True,
                "tax_exempt": True,
                "state": "NY"
            }
        ]
        mock_db.bonds.insert_many(bonds)
        return bonds

    def test_search_no_filters(self, client, sample_bonds):
        response = client.post("/api/v1/screener/search", data=json.dumps({}), content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert len(data["data"]["bonds"]) == 2

    def test_search_with_type_filter(self, client, sample_bonds):
        payload = {"type": "corporate"}
        response = client.post("/api/v1/screener/search", data=json.dumps(payload), content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["data"]["bonds"]) == 1
        assert data["data"]["bonds"][0]["type"] == "corporate"

    def test_search_with_rating_filter(self, client, sample_bonds):
        payload = {"rating": ["AA", "AAA"]}
        response = client.post("/api/v1/screener/search", data=json.dumps(payload), content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["data"]["bonds"]) == 2

    def test_search_with_coupon_range(self, client, sample_bonds):
        payload = {"min_coupon": 4.0}
        response = client.post("/api/v1/screener/search", data=json.dumps(payload), content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["data"]["bonds"]) == 1
        assert data["data"]["bonds"][0]["coupon_rate"] == 5.0

    def test_get_filters(self, client, sample_bonds):
        response = client.get("/api/v1/screener/filters")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "corporate" in data["data"]["types"]
        assert "municipal" in data["data"]["types"]
        assert "AAA" in data["data"]["ratings"]
        assert "NY" in data["data"]["states"]
