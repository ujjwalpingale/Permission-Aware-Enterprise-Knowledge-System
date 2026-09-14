from langchain_google_genai import GoogleGenerativeAIEmbeddings


def get_embedding_function(api_key: str, model_name: str = "models/gemini-embedding-001") -> GoogleGenerativeAIEmbeddings:
    """Returns an initialized GoogleGenerativeAIEmbeddings instance."""
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing or empty.")
    
    return GoogleGenerativeAIEmbeddings(
        google_api_key=api_key,
        model=model_name,
    )
