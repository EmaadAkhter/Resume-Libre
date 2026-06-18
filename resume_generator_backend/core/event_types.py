class Events:
    """Central registry of all event names in the system.

    Use these constants instead of bare strings so typos fail at import time.
    """

    # Pipeline events
    README_FETCHED = "readme:fetched"
    PROMPT_BUILT = "prompt:built"
    LLM_GENERATING = "llm:generating"
    LLM_TOKEN = "llm:token"
    LLM_COMPLETED = "llm:completed"
    VALIDATION_PASSED = "validation:passed"
    VALIDATION_FAILED = "validation:failed"

    # API events
    API_REQUEST = "api:request"
    API_RESPONSE = "api:response"
    API_ERROR = "api:error"

    # Template events
    TEMPLATE_SELECTED = "template:selected"
    TEMPLATE_UPLOADED = "template:uploaded"

    # Resume events
    RESUME_CREATED = "resume:created"
    RESUME_DELETED = "resume:deleted"
    VERSION_COMMITTED = "version:committed"
    BRANCH_CREATED = "branch:created"
    BRANCH_MERGED = "branch:merged"
    TAG_CREATED = "tag:created"

    # Debug
    DEBUG_SUBSCRIBER_JOINED = "debug:subscriber:joined"
    DEBUG_SUBSCRIBER_LEFT = "debug:subscriber:left"
