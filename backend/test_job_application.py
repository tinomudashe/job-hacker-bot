import requests

API_URL = "http://localhost:8000/api"
AUTH_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ii1sX0llanRjajJZRDRORi0ybjhpbSJ9.eyJpc3MiOiJodHRwczovL2Rldi1qdG1hOG9zdzY2dW01YnF1LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJobWNSQ3QzZjM1REpDMk5GMGlWaXB3Z3J1YjFqbGdUU0BjbGllbnRzIiwiYXVkIjoiaHR0cHM6Ly9kZXYtanRtYThvc3c2NnVtNWJxdS51cy5hdXRoMC5jb20vYXBpL3YyLyIsImlhdCI6MTc0OTc0NjE0OCwiZXhwIjoxNzQ5ODMyNTQ4LCJndHkiOiJjbGllbnQtY3JlZGVudGlhbHMiLCJhenAiOiJobWNSQ3QzZjM1REpDMk5GMGlWaXB3Z3J1YjFqbGdUUyJ9.V0lEoJWmnpVwIhtua7SzKCtmtnwXSUF15XQX2xzf8OqlEYGyXE8bFynBnqw5mfW6WHlFKPaqzm_CfEZD2j5aYirQ0TaDxM1fkFKMmP6U78VJkLg6kZaUwBKlWUG5afsYPcjFxWKhb41B9-RUslIf3zIBi3JatOkJlwfDVBA7noBRtDz8-qI-6Krrgxep_x1ZxWXCSYgT0WOnCd7kgpAsKdTpaCReNtM3FkUXHtZp2J2u1YfFVrq3olWqCv1AHm052YpyPgZ_zhtDs3H3ElpXF1LBIsNT3iQpioVWCxLqBw5M-XXUW0mZgxWGZJJfdR1ZxWHnbtLcCKtJJ8Rblf0HKg"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def apply_for_job():
    data = {
        "job_url": "https://jobs.eu.lever.co/olx/366fe518-2eb4-4b70-975b-2066dbb45ac2/apply?lever-origin=applied&lever-source%5B%5D=LinkedInJobWrap",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890"
    }
    response = requests.post(f"{API_URL}/agent/apply", json=data, headers=headers)
    print("Apply response:", response.status_code, response.json())

def list_applications():
    response = requests.get(f"{API_URL}/applications", headers=headers)
    print("Applications:", response.status_code)
    for app in response.json():
        print(app)

if __name__ == "__main__":
    print("Testing job application feature...\n")
    apply_for_job()
    print("\nFetching list of applications...\n")
    list_applications() 