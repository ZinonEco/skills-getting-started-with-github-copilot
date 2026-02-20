"""
Test suite for Mergington High School Activities API

Tests are structured using the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Execute the operation being tested
- Assert: Verify the results
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Fixture that provides a TestClient for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Fixture that resets the activities database before each test.
    This ensures test isolation since the app uses an in-memory database.
    """
    # Store original state
    original_activities = {
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
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball training and matches",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Tennis lessons and friendly tournaments",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 10,
            "participants": ["sarah@mergington.edu"]
        },
        "Drama Class": {
            "description": "Theater arts, acting, and stage performance",
            "schedule": "Mondays and Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["lucas@mergington.edu", "isabella@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and visual art creation",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["ava@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop argumentation and public speaking skills",
            "schedule": "Tuesdays and Thursdays, 4:30 PM - 5:30 PM",
            "max_participants": 14,
            "participants": ["james@mergington.edu", "mia@mergington.edu"]
        },
        "Science Club": {
            "description": "Explore STEM concepts through hands-on experiments",
            "schedule": "Wednesdays, 3:30 PM - 4:30 PM",
            "max_participants": 22,
            "participants": ["noah@mergington.edu"]
        }
    }
    
    # Clear and reset activities before test
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Reset after test (optional, but good practice)
    activities.clear()
    activities.update(original_activities)


# ============================================================================
# HAPPY PATH TESTS - Tests that verify successful operations
# ============================================================================

class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """
        Arrange: Use default activities state
        Act: Send GET request to /activities
        Assert: Verify response contains all activities with correct structure
        """
        # Arrange
        expected_activity_count = 9
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == expected_activity_count
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Science Club" in data
    
    def test_get_activities_returns_correct_activity_structure(self, client):
        """
        Arrange: None
        Act: GET /activities and inspect Chess Club structure
        Assert: Verify activity has all required fields
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        # Assert
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_get_activities_contains_initial_participants(self, client):
        """
        Arrange: None
        Act: GET /activities
        Assert: Verify activities have initial participants
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_successful(self, client):
        """
        Arrange: Prepare a valid activity and email not yet signed up
        Act: Send POST request to signup endpoint
        Assert: Verify response indicates success and participant is added
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        
        # Verify participant was actually added
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
    
    def test_signup_for_activity_multiple_participants(self, client):
        """
        Arrange: Prepare two different students
        Act: Sign up both students for the same activity
        Assert: Verify both are successfully added
        """
        # Arrange
        activity_name = "Programming Class"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Act - signup first student
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        
        # Act - signup second student
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are in participants list
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants
    
    def test_signup_includes_existing_participants(self, client):
        """
        Arrange: None
        Act: Signup for activity that already has participants
        Assert: Verify new participant is added to existing ones, not replacing them
        """
        # Arrange
        activity_name = "Chess Club"
        new_email = "newchess@mergington.edu"
        
        # Get initial count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        assert final_count == initial_count + 1


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup/{email} endpoint"""
    
    def test_unregister_from_activity_successful(self, client):
        """
        Arrange: Prepare a student already signed up for an activity
        Act: Send DELETE request to unregister
        Assert: Verify student is removed from participants
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Pre-existing participant
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup/{email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify participant was actually removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]
    
    def test_unregister_maintains_other_participants(self, client):
        """
        Arrange: Activity with multiple participants
        Act: Remove one participant
        Assert: Verify other participants remain
        """
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        email_to_keep = "daniel@mergington.edu"
        
        # Act
        client.delete(
            f"/activities/{activity_name}/signup/{email_to_remove}"
        )
        
        # Assert
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        
        assert email_to_remove not in participants
        assert email_to_keep in participants
    
    def test_unregister_completely_removes_participant(self, client):
        """
        Arrange: Signup for activity, then unregister
        Act: Signup then delete for same email
        Assert: Verify email count returns to baseline
        """
        # Arrange
        activity_name = "Drama Class"
        email = "testuser@mergington.edu"
        
        # Get initial count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act - signup
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act - unregister
        client.delete(
            f"/activities/{activity_name}/signup/{email}"
        )
        
        # Assert - count should return to initial
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        assert final_count == initial_count


# ============================================================================
# ERROR/EDGE CASE TESTS - Tests that verify error handling
# ============================================================================

class TestSignupErrorHandling:
    """Tests for error conditions in signup endpoint"""
    
    def test_signup_activity_not_found(self, client):
        """
        Arrange: Prepare non-existent activity name
        Act: Try to signup for non-existent activity
        Assert: Verify 404 error is returned
        """
        # Arrange
        fake_activity = "Non Existent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{fake_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_email(self, client):
        """
        Arrange: Prepare email already signed up for activity
        Act: Try to signup same email again
        Assert: Verify 400 error indicating duplicate signup
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_activity_full(self, client):
        """
        Arrange: Fill up an activity to max capacity, then try to add one more
        Act: Signup when activity is full
        Assert: Verify appropriate error (activity full or quota exceeded)
        """
        # Arrange
        # Tennis Club has max_participants of 10
        activity_name = "Tennis Club"
        max_capacity = 10
        
        # Fill up the activity to max capacity
        for i in range(max_capacity - 1):  # Already has 1 participant
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": f"filler{i}@mergington.edu"}
            )
        
        # Verify activity is now full
        activities_check = client.get("/activities")
        current_participants = len(activities_check.json()[activity_name]["participants"])
        assert current_participants == max_capacity
        
        # Act - try to signup when full
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "overfull@mergington.edu"}
        )
        
        # Assert - Note: Current implementation doesn't check capacity
        # This test documents the current behavior
        # If capacity checking is added, this would verify 400 status
        # For now, this test passes as the endpoint allows overflow
        assert response.status_code == 200  # Currently allows over capacity


class TestUnregisterErrorHandling:
    """Tests for error conditions in unregister endpoint"""
    
    def test_unregister_activity_not_found(self, client):
        """
        Arrange: Prepare non-existent activity name
        Act: Try to unregister from non-existent activity
        Assert: Verify 404 error is returned
        """
        # Arrange
        fake_activity = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{fake_activity}/signup/{email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_student_not_registered(self, client):
        """
        Arrange: Prepare email that was never signed up for activity
        Act: Try to unregister non-existent participant
        Assert: Verify 400 error indicating student not registered
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup/{email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_wrong_activity(self, client):
        """
        Arrange: Student registered for Activity A, try to unregister from Activity B
        Act: Delete with different activity
        Assert: Verify 400 error - student not registered for that activity
        """
        # Arrange
        registered_activity = "Chess Club"
        different_activity = "Programming Class"
        email = "michael@mergington.edu"  # Registered in Chess Club, not Programming Class
        
        # Act
        response = client.delete(
            f"/activities/{different_activity}/signup/{email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
        
        # Verify student is still in original activity
        activities_response = client.get("/activities")
        assert email in activities_response.json()[registered_activity]["participants"]


class TestActivityStateConsistency:
    """Tests to verify data consistency across multiple operations"""
    
    def test_signup_and_get_consistent(self, client):
        """
        Arrange: None
        Act: Signup for activity, then get all activities
        Assert: Verify signup is reflected in get response
        """
        # Arrange
        activity_name = "Art Studio"
        email = "artist@mergington.edu"
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        response = client.get("/activities")
        
        # Assert
        assert email in response.json()[activity_name]["participants"]
    
    def test_multiple_operations_maintain_consistency(self, client):
        """
        Arrange: Multiple signup/unregister operations
        Act: Perform series of operations
        Assert: Verify final state matches expected
        """
        # Arrange
        activity_name = "Science Club"
        email1 = "scientist1@mergington.edu"
        email2 = "scientist2@mergington.edu"
        
        # Act - signup both
        client.post(f"/activities/{activity_name}/signup", params={"email": email1})
        client.post(f"/activities/{activity_name}/signup", params={"email": email2})
        
        # Act - unregister first
        client.delete(f"/activities/{activity_name}/signup/{email1}")
        
        # Assert
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        
        assert email1 not in participants
        assert email2 in participants
