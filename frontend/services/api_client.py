import os
import requests
from typing import Dict, Any, List, Optional

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
VALID_EMPLOYEE_ROLES = {"engineer", "hr", "sales", "support"}


class APIClient:
    """HTTP Client communicating strictly with the FastAPI Backend Service."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url.rstrip("/")

    def _parse_error_response(self, response: requests.Response, default_prefix: str = "Error") -> Dict[str, Any]:
        """Extracts structured error details and flags HTTP 401 Unauthorized status."""
        status_code = response.status_code
        is_unauthorized = (status_code == 401)
        
        try:
            body = response.json()
            detail = body.get("detail", response.text)
            if isinstance(detail, list):
                # Pydantic validation error list formatting
                detail = "; ".join([f"{err.get('loc', [])}: {err.get('msg')}" for err in detail])
        except Exception:
            detail = response.text or "Unknown server error"

        return {
            "success": False,
            "status_code": status_code,
            "unauthorized": is_unauthorized,
            "error": f"{default_prefix} ({status_code}): {detail}",
        }

    def check_health(self) -> Dict[str, Any]:
        """Checks if backend FastAPI service is running and healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=3)
            if response.status_code == 200:
                return {"status": "ok", "online": True}
            return {"status": "unhealthy", "online": False, "code": response.status_code}
        except requests.exceptions.RequestException as e:
            return {"status": "offline", "online": False, "error": str(e)}

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticates user against POST /auth/login and returns signed JWT access token."""
        url = f"{self.base_url}/auth/login"
        payload = {"email": email.strip(), "password": password}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            return self._parse_error_response(response, "Login Failed")
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": f"Unable to reach backend at {self.base_url}. Is FastAPI running?"}
        except Exception as e:
            return {"success": False, "error": f"Login failed due to unexpected error: {str(e)}"}

    def register_company(
        self,
        company_name: str,
        admin_name: str,
        admin_email: str,
        password: str,
    ) -> Dict[str, Any]:
        """Registers a new company and initial Admin user via POST /auth/register-company."""
        url = f"{self.base_url}/auth/register-company"
        payload = {
            "company_name": company_name.strip(),
            "admin_name": admin_name.strip(),
            "admin_email": admin_email.strip(),
            "password": password,
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            if response.status_code in [200, 201]:
                return {"success": True, "data": response.json()}
            return self._parse_error_response(response, "Company Registration Failed")
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": f"Unable to reach backend at {self.base_url}. Is FastAPI running?"}
        except Exception as e:
            return {"success": False, "error": f"Company registration failed: {str(e)}"}

    def register_employee(
        self,
        full_name: str,
        email: str,
        password: str,
        company_id: str,
        role: str,
        invite_code: str,
    ) -> Dict[str, Any]:
        """Registers an employee for an existing company via POST /auth/register."""
        clean_role = role.strip().lower()
        if clean_role == "admin" or clean_role not in VALID_EMPLOYEE_ROLES:
            return {
                "success": False,
                "error": f"Invalid employee role '{role}'. Allowed roles: {sorted(list(VALID_EMPLOYEE_ROLES))}",
            }

        url = f"{self.base_url}/auth/register"
        payload = {
            "full_name": full_name.strip(),
            "email": email.strip(),
            "password": password,
            "company_id": company_id.strip(),
            "role": clean_role,
            "invite_code": invite_code.strip(),
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            if response.status_code in [200, 201]:
                return {"success": True, "data": response.json()}
            return self._parse_error_response(response, "Employee Registration Failed")
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": f"Unable to reach backend at {self.base_url}. Is FastAPI running?"}
        except Exception as e:
            return {"success": False, "error": f"Employee registration failed: {str(e)}"}

    def get_me(self, access_token: str) -> Dict[str, Any]:
        """Retrieves authenticated user profile information via GET /auth/me."""
        url = f"{self.base_url}/auth/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            return self._parse_error_response(response, "Failed to load user profile")
        except Exception as e:
            return {"success": False, "error": f"Failed to retrieve user info: {str(e)}"}

    def get_documents(self, access_token: str) -> Dict[str, Any]:
        """Fetches authorized company documents via GET /documents."""
        url = f"{self.base_url}/documents"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            return self._parse_error_response(response, "Failed to load documents")
        except Exception as e:
            return {"success": False, "error": f"Failed to retrieve documents: {str(e)}"}

    def upload_document(
        self,
        file_name: str,
        file_bytes: bytes,
        allowed_roles: List[str],
        access_token: str,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Uploads document payload to POST /documents/upload using JWT authentication."""
        clean_roles = [r.strip().lower() for r in allowed_roles if r.strip()]
        for r in clean_roles:
            if r == "admin" or r not in VALID_EMPLOYEE_ROLES:
                return {
                    "success": False,
                    "error": f"Invalid document permission role '{r}'. 'admin' is not allowed.",
                }

        url = f"{self.base_url}/documents/upload"
        headers = {"Authorization": f"Bearer {access_token}"}

        data_payload = {
            "allowed_roles": ",".join(clean_roles),
        }
        if title and title.strip():
            data_payload["title"] = title.strip()

        files_payload = {
            "file": (file_name, file_bytes, "application/octet-stream"),
        }

        try:
            response = requests.post(url, data=data_payload, files=files_payload, headers=headers, timeout=120)
            if response.status_code in [200, 201]:
                return {"success": True, "data": response.json()}
            return self._parse_error_response(response, "Document Upload Failed")
        except Exception as e:
            return {"success": False, "error": f"Failed to upload document: {str(e)}"}

    def send_question(self, question: str, access_token: str) -> Dict[str, Any]:
        """Sends RAG question request to POST /chat using JWT Bearer authentication."""
        url = f"{self.base_url}/chat"
        payload = {"question": question.strip()}
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            return self._parse_error_response(response, "Chat Request Failed")
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out. Please try again."}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": f"Unable to reach backend at {self.base_url}."}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error during chat request: {str(e)}"}
