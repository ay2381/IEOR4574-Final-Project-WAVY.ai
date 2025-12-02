"""
Basic tests for the API endpoints
Run with: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"


def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "database" in response.json()


def test_create_patient():
    """Test creating a patient"""
    patient_data = {
        "name": "Test Patient",
        "age": 30,
        "gender": "male",
        "medicalConditions": [],
        "allergies": [],
        "dietaryRestrictions": [],
        "calorieTarget": 2000,
        "macroTargets": {"protein": 150, "carbs": 200, "fat": 65}
    }
    
    response = client.post("/api/patients", json=patient_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Patient"
    assert "id" in data


def test_get_patients():
    """Test getting all patients"""
    response = client.get("/api/patients")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_plans():
    """Test getting all plans"""
    response = client.get("/api/plans")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_generate_plan_rule_based():
    """Test generating a rule-based meal plan"""
    # First create a patient
    patient_data = {
        "name": "Test Patient",
        "age": 30,
        "gender": "male",
        "medicalConditions": [],
        "allergies": [],
        "dietaryRestrictions": [],
        "calorieTarget": 2000,
        "macroTargets": {"protein": 150, "carbs": 200, "fat": 65}
    }
    
    patient_response = client.post("/api/patients", json=patient_data)
    patient_id = patient_response.json()["id"]
    
    # Generate plan
    plan_data = {
        "patientIds": [patient_id],
        "weekStart": "2024-01-15",
        "strategy": "rule_based"
    }
    
    response = client.post("/api/plans/generate", json=plan_data)
    assert response.status_code == 201
    plans = response.json()
    assert len(plans) == 1
    assert len(plans[0]["days"]) == 7


def test_delete_patient():
    """Test deleting a patient"""
    # Create patient
    patient_data = {
        "name": "Test Patient",
        "age": 30,
        "gender": "male",
        "medicalConditions": [],
        "allergies": [],
        "dietaryRestrictions": [],
        "calorieTarget": 2000,
        "macroTargets": {"protein": 150, "carbs": 200, "fat": 65}
    }
    
    create_response = client.post("/api/patients", json=patient_data)
    patient_id = create_response.json()["id"]
    
    # Delete patient
    delete_response = client.delete(f"/api/patients/{patient_id}")
    assert delete_response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f"/api/patients/{patient_id}")
    assert get_response.status_code == 404
