import pytest
import mongomock
from backend.app import create_app
from backend.database import mongo

@pytest.fixture(scope="session")
def app():
    """Create a Flask app for testing."""
    # Mock the database connection before creating the app
    with mongomock.patch(servers=(('localhost', 27017),)):
        # We need to ensure that when get_db() is called, it uses mongomock
        app = create_app()
        app.config.update({
            "TESTING": True,
            "MONGODB_DB_NAME": "test_db"
        })
        yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(autouse=True)
def mock_db(monkeypatch):
    """
    Ensure every test uses a clean mock database.
    """
    mock_client = mongomock.MongoClient()
    mock_database = mock_client["test_db"]
    
    def mock_get_db():
        return mock_database
    
    monkeypatch.setattr(mongo, "get_db", mock_get_db)
    monkeypatch.setattr(mongo, "get_client", lambda: mock_client)
    
    return mock_database
