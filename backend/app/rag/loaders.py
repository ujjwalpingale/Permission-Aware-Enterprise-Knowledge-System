import json
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document


class DocumentLoader:
    """Modular document loader with permission metadata extraction for Markdown, TXT, and JSON sources."""

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
            return []

    @staticmethod
    def _parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
        """Parses simple YAML-style frontmatter from markdown files."""
        metadata = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1]
                body = parts[2].strip()
                for line in frontmatter_text.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        metadata[k.strip()] = v.strip()
        return metadata, body

    @staticmethod
    def load_markdown(file_path: Path) -> List[Document]:
        raw_content = file_path.read_text(encoding="utf-8")
        parsed_meta, body = DocumentLoader._parse_frontmatter(raw_content)

        # Infer title from first H1 heading if present
        title = file_path.stem.replace("_", " ").title()
        for line in body.splitlines():
            if line.strip().startswith("# "):
                title = line.strip().lstrip("# ").strip()
                break

        metadata = {
            "source_type": "project_document",
            "source_file": file_path.name,
            "document_id": f"doc_{file_path.stem}",
            "title": title,
            # Permission Metadata Fields
            "department": str(parsed_meta.get("department", "engineering")),
            "account": str(parsed_meta.get("account", "*")),
            "access_level": str(parsed_meta.get("access_level", "internal")),
            "allowed_roles": str(parsed_meta.get("allowed_roles", "")),
            "allowed_users": str(parsed_meta.get("allowed_users", "")),
        }
        return [Document(page_content=body, metadata=metadata)]

    @staticmethod
    def load_txt(file_path: Path) -> List[Document]:
        content = file_path.read_text(encoding="utf-8")
        title = file_path.stem.replace("_", " ").title()

        metadata = {
            "source_type": "text_document",
            "source_file": file_path.name,
            "document_id": f"txt_{file_path.stem}",
            "title": title,
            "department": "general",
            "account": "*",
            "access_level": "internal",
            "allowed_roles": "",
            "allowed_users": "",
        }
        return [Document(page_content=content, metadata=metadata)]

    @staticmethod
    def load_json(file_path: Path) -> List[Document]:
        content_raw = file_path.read_text(encoding="utf-8")
        data = json.loads(content_raw)

        # Helper to format list fields to string for ChromaDB compatibility
        def format_field(val):
            if isinstance(val, list):
                return ",".join(val)
            return str(val) if val else ""

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
                "department": str(data.get("department", "support")),
                "account": str(data.get("account", customer)),
                "access_level": str(data.get("access_level", "internal")),
                "allowed_roles": format_field(data.get("allowed_roles", ["support_agent"])),
                "allowed_users": format_field(data.get("allowed_users", [])),
            }
            return [Document(page_content=text_content, metadata=metadata)]

        # Slack conversation JSON format (list of message dicts)
        elif isinstance(data, list):
            channel = "general"
            first_msg = data[0] if len(data) > 0 and isinstance(data[0], dict) else {}
            if "channel" in first_msg:
                channel = first_msg["channel"]

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
                "department": str(first_msg.get("department", "engineering")),
                "account": str(first_msg.get("account", "*")),
                "access_level": str(first_msg.get("access_level", "internal")),
                "allowed_roles": format_field(first_msg.get("allowed_roles", [])),
                "allowed_users": format_field(first_msg.get("allowed_users", [])),
            }
            return [Document(page_content=combined_content, metadata=metadata)]

        else:
            metadata = {
                "source_type": "json_document",
                "source_file": file_path.name,
                "document_id": f"json_{file_path.stem}",
                "title": file_path.stem.replace("_", " ").title(),
                "department": "general",
                "account": "*",
                "access_level": "internal",
                "allowed_roles": "",
                "allowed_users": "",
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
