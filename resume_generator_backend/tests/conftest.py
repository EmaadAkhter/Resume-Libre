import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@pytest.fixture
def sample_resume_md():
    return """# John Doe
[john@email.com](mailto:john@email.com) | +1-555-123-4567 | San Francisco, CA

## Summary
Full-Stack Engineer with 3+ years building scalable web applications.

## Experience
**Software Engineer** | TechCorp | Jan 2022 - Present
- Built microservices backend processing 1M+ API requests daily
- Led migration from monolith to microservices

## Skills
**Languages:** Python, JavaScript, Go
"""


@pytest.fixture
def sample_resume_tex():
    return r"""\documentclass[11pt,a4paper]{article}
\begin{document}
\section*{Experience}
\textbf{Software Engineer} | TechCorp
\end{document}
"""


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing store modules."""
    with patch("services.auth.get_supabase_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def sample_user():
    return {"id": "test-user-id", "email": "test@test.com"}


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Set test environment variables."""
    os.environ["OPENROUTER_API_KEY"] = "test-key"
    os.environ["OPENROUTER_MODEL"] = "test-model"
    os.environ["SUPABASE_URL"] = "https://test.supabase.co"
    os.environ["SUPABASE_SERVICE_KEY"] = "test-service-key"
    yield
    # Cleanup is automatic since we're just setting env vars
