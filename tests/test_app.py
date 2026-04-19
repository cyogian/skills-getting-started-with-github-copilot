import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

# Test data for consistent testing
TEST_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    }
}

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the activities data before each test"""
    from src.app import activities
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        }
    })

class TestRootEndpoint:
    def test_root_redirect(self):
        # Arrange - No special setup needed

        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        assert response.url.path == "/static/index.html"

class TestActivitiesEndpoint:
    def test_get_activities(self):
        # Arrange - Activities are set up by fixture

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 2
        assert "Chess Club" in data
        assert "Programming Class" in data

        # Check structure of Chess Club
        chess = data["Chess Club"]
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess
        assert chess["max_participants"] == 12
        assert len(chess["participants"]) == 2

class TestSignupEndpoint:
    def test_successful_signup(self):
        # Arrange
        new_email = "newstudent@mergington.edu"
        activity_name = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={new_email}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert f"Signed up {new_email} for {activity_name}" in data["message"]

        # Verify the participant was added
        response = client.get("/activities")
        activities = response.json()
        assert new_email in activities[activity_name]["participants"]

    def test_signup_activity_not_found(self):
        # Arrange
        invalid_activity = "NonExistent"
        email = "test@mergington.edu"

        # Act
        response = client.post(f"/activities/{invalid_activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_already_registered(self):
        # Arrange
        existing_email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={existing_email}")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Student is already signed up" in data["detail"]

    def test_signup_activity_full(self):
        # Arrange - Fill up Programming Class (max 20, currently 2 participants)
        activity_name = "Programming Class"
        for i in range(18):
            email = f"student{i}@mergington.edu"
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200

        # Act - Try to add one more
        overflow_email = "overflow@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={overflow_email}")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Activity is full" in data["detail"]

class TestUnregisterEndpoint:
    def test_successful_unregister(self):
        # Arrange
        existing_email = "michael@mergington.edu"  # In Chess Club
        activity_name = "Chess Club"

        # Act
        response = client.delete(f"/activities/{activity_name}/signup?email={existing_email}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert f"Unregistered {existing_email} from {activity_name}" in data["message"]

        # Verify the participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert existing_email not in activities[activity_name]["participants"]

    def test_unregister_activity_not_found(self):
        # Arrange
        invalid_activity = "NonExistent"
        email = "test@mergington.edu"

        # Act
        response = client.delete(f"/activities/{invalid_activity}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_unregister_not_signed_up(self):
        # Arrange
        not_signed_up_email = "notsignedup@mergington.edu"
        activity_name = "Chess Club"

        # Act
        response = client.delete(f"/activities/{activity_name}/signup?email={not_signed_up_email}")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Student is not signed up" in data["detail"]

class TestIntegration:
    def test_full_signup_unregister_cycle(self):
        # Arrange
        test_email = "cycle@mergington.edu"
        activity_name = "Programming Class"

        # Act - Sign up
        response = client.post(f"/activities/{activity_name}/signup?email={test_email}")

        # Assert - Verify signup
        assert response.status_code == 200
        response = client.get("/activities")
        activities = response.json()
        assert test_email in activities[activity_name]["participants"]

        # Act - Unregister
        response = client.delete(f"/activities/{activity_name}/signup?email={test_email}")

        # Assert - Verify unregistration
        assert response.status_code == 200
        response = client.get("/activities")
        activities = response.json()
        assert test_email not in activities[activity_name]["participants"]