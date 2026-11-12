from copy import deepcopy


def test_root_redirects_to_homepage(client):
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client, activity_data):
    # Arrange
    expected = deepcopy(activity_data)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected
    for activity in response.json().values():
        assert set(activity) == {
            "description", "schedule", "max_participants", "participants"
        }


def test_signup_adds_one_participant(client, activity_data):
    # Arrange
    email = "new-student@mergington.edu"
    expected = deepcopy(activity_data)
    expected["Chess Club"]["participants"].append(email)

    # Act
    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Chess Club"
    }
    assert activities_response.status_code == 200
    assert activities_response.json() == expected
    assert activity_data == expected


def test_signup_unknown_activity_does_not_change_data(client, activity_data):
    # Arrange
    before = deepcopy(activity_data)

    # Act
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new-student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_data == before


def test_duplicate_signup_does_not_change_data(client, activity_data):
    # Arrange
    email = activity_data["Chess Club"]["participants"][0]
    before = deepcopy(activity_data)

    # Act
    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activity_data == before


def test_signup_full_activity_does_not_change_data(client, activity_data):
    # Arrange
    activity = activity_data["Chess Club"]
    activity["participants"] = [
        f"student-{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]
    before = deepcopy(activity_data)

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new-student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}
    assert activity_data == before


def test_signup_fills_last_available_place(client, activity_data):
    # Arrange
    email = "last-student@mergington.edu"
    activity = activity_data["Chess Club"]
    activity["participants"] = [
        f"student-{index}@mergington.edu"
        for index in range(activity["max_participants"] - 1)
    ]
    expected = deepcopy(activity_data)
    expected["Chess Club"]["participants"].append(email)

    # Act
    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Chess Club"
    }
    assert activity_data == expected
    assert len(activity["participants"]) == activity["max_participants"]


def test_signup_requires_email(client, activity_data):
    # Arrange
    before = deepcopy(activity_data)

    # Act
    response = client.post("/activities/Chess Club/signup")

    # Assert
    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"]
        and error["type"] == "missing"
        for error in response.json()["detail"]
    )
    assert activity_data == before
