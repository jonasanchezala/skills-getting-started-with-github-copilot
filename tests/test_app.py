from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as api


client = TestClient(api.app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(api.activities)
    yield
    api.activities.clear()
    api.activities.update(original_activities)


def test_get_activities_returns_activity_details():
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert activities["Chess Club"] == {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    }


def test_signup_adds_participant():
    response = client.post(
        "/activities/Basketball Team/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up student@mergington.edu for Basketball Team"
    }
    assert "student@mergington.edu" in api.activities["Basketball Team"]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "status_code", "detail"),
    [
        ("Unknown Club", "student@mergington.edu", 404, "Activity not found"),
        (
            "Chess Club",
            "michael@mergington.edu",
            400,
            "Student is already signed up for this activity",
        ),
    ],
)
def test_signup_rejects_unknown_activity_or_duplicate(
    activity_name, email, status_code, detail
):
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == status_code
    assert response.json()["detail"] == detail


def test_unregister_removes_participant():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered michael@mergington.edu from Chess Club"
    }
    assert "michael@mergington.edu" not in api.activities["Chess Club"]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "detail"),
    [
        ("Unknown Club", "student@mergington.edu", "Activity not found"),
        (
            "Chess Club",
            "student@mergington.edu",
            "Student is not signed up for this activity",
        ),
    ],
)
def test_unregister_rejects_unknown_activity_or_missing_participant(
    activity_name, email, detail
):
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == detail
