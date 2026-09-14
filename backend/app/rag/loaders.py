import json
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document


class DocumentLoader:
    """Modular document loader for Markdown, TXT, and JSON sources."""

    @staticmethod
    def load_file(file_path: Path) -> List[Document]:
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()

        if suffix in [".md", ".markdown"]:
            return DocumentLoader.load_markdown(file_path)
        elif suffix in [".txt"]:
            return DocumentLoader.load_txt(file_path)
        elif suffix in [".json"]:
            return DocumentLoader.load_json(file_path)
        else:
            # Fallback or skip unsupported format for Phase 1
            return []

    @staticmethod
    def load_markdown(file_path: Path) -> List[Document]:
        content = file_path.read_text(encoding="utf-8")
        
        # Infer title from first H1 heading if present
        title = file_path.stem.replace("_", " ").title()
        for line in content.splitlines():
            if line.strip().startswith("# "):
                title = line.strip().lstrip("# ").strip()
                break

        metadata = {
            "source_type": "project_document",
            "source_file": file_path.name,
            "document_id": f"doc_{file_path.stem}",
            "title": title,
        }
        return [Document(page_content=content, metadata=metadata)]

    @staticmethod
    def load_txt(file_path: Path) -> List[Document]:
        content = file_path.read_text(encoding="utf-8")
        title = file_path.stem.replace("_", " ").title()

        metadata = {
            "source_type": "text_document",
            "source_file": file_path.name,
            "document_id": f"txt_{file_path.stem}",
            "title": title,
        }
        return [Document(page_content=content, metadata=metadata)]

    @staticmethod
    def load_json(file_path: Path) -> List[Document]:
        content_raw = file_path.read_text(encoding="utf-8")
        data = json.loads(content_raw)

        # Support Ticket JSON format
        if isinstance(data, dict) and "ticket_id" in data:
            ticket_id = data.get("ticket_id", file_path.stem)
            customer = data.get("customer", "Unknown Customer")
            title = f"Support Ticket {ticket_id} ({customer})"
            
            text_content = (
                f"Support Ticket ID: {ticket_id}\n"
                f"Customer: {customer}\n"
                f"Created At: {data.get('created_at', 'N/A')}\n"
                f"Priority: {data.get('priority', 'N/A')}\n"
                f"Status: {data.get('status', 'N/A')}\n"
                f"Issue: {data.get('issue', '')}\n"
                f"Resolution: {data.get('resolution', '')}"
            )
            metadata = {
                "source_type": "support_ticket",
                "source_file": file_path.name,
                "document_id": ticket_id,
                "title": title,
            }
            return [Document(page_content=text_content, metadata=metadata)]

        # Slack conversation JSON format (list of message dicts)
        elif isinstance(data, list):
            channel = "general"
            if len(data) > 0 and isinstance(data[0], dict) and "channel" in data[0]:
                channel = data[0]["channel"]

            messages_text = []
            for item in data:
                if isinstance(item, dict):
                    user = item.get("user", "Unknown")
                    msg = item.get("message", "")
                    ts = item.get("timestamp", "")
                    messages_text.append(f"[{ts}] {user}: {msg}")

            combined_content = f"Slack Channel: #{channel}\n\n" + "\n".join(messages_text)
            title = f"Slack #{channel}"
            metadata = {
                "source_type": "slack",
                "source_file": file_path.name,
                "document_id": f"slack_{file_path.stem}",
                "title": title,
            }
            return [Document(page_content=combined_content, metadata=metadata)]

        else:
            # Generic JSON document handling
            metadata = {
                "source_type": "json_document",
                "source_file": file_path.name,
                "document_id": f"json_{file_path.stem}",
                "title": file_path.stem.replace("_", " ").title(),
            }
            return [Document(page_content=json.dumps(data, indent=2), metadata=metadata)]

    @staticmethod
    def load_directory(data_dir: Path) -> List[Document]:
        data_dir = Path(data_dir)
        documents = []
        if not data_dir.exists():
            return documents

        for file_path in data_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                docs = DocumentLoader.load_file(file_path)
                documents.extend(docs)

        return documents
