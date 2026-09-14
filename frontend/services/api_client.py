import os
import requests
from typing import Dict, Any, List

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class APIClient:
    """HTTP Client communicating strictly with the FastAPI Backend Service."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> Dict[str, Any]:
        """Checks if backend FastAPI service is running and healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=3)
            if response.status_code == 200:
                return {"status": "ok", "online": True}
            return {"status": "unhealthy", "online": False, "code": response.status_code}
        except requests.exceptions.RequestException as e:
            return {"status": "offline", "online": False, "error": str(e)}

    def send_question(self, question: str, user_id: str = "user_001") -> Dict[str, Any]:
        """Sends a permission-aware question request to the FastAPI /chat endpoint."""
        url = f"{self.base_url}/chat"
        payload = {"user_id": user_id, "question": question}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                try:
                    error_detail = response.json().get("detail", response.text)
                except Exception:
                    error_detail = response.text
                return {
                    "success": False,
                    "error": f"Server Error ({response.status_code}): {error_detail}",
                }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out. Please try again."}
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Failed to connect to backend server at http://localhost:8000. Is FastAPI running?",
            }
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def upload_documents(self, uploaded_files) -> Dict[str, Any]:
        """Uploads files to the FastAPI /upload endpoint and ingests into ChromaDB."""
        url = f"{self.base_url}/upload"
        files_payload = []
        for file in uploaded_files:
            files_payload.append(("files", (file.name, file.getvalue(), file.type)))

        try:
            response = requests.post(url, files=files_payload, timeout=120)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                try:
                    error_detail = response.json().get("detail", response.text)
                except Exception:
                    error_detail = response.text
                return {
                    "success": False,
                    "error": f"Upload Error ({response.status_code}): {error_detail}",
                }
        except Exception as e:
            return {"success": False, "error": f"Failed to upload files: {str(e)}"}
