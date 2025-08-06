class AIVideoGeneratorException(Exception):
    """Base exception class for AI Video Generator"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ProjectException(AIVideoGeneratorException):
    """Project-related exceptions"""
    pass

class ProjectNotFound(ProjectException):
    def __init__(self, project_id: str):
        super().__init__(f"Project {project_id} not found", "PROJECT_NOT_FOUND")

class ProjectAlreadyExists(ProjectException):
    def __init__(self, project_name: str):
        super().__init__(f"Project '{project_name}' already exists", "PROJECT_EXISTS")

class InvalidProjectState(ProjectException):
    def __init__(self, current_state: str, required_state: str):
        super().__init__(
            f"Invalid project state. Current: {current_state}, Required: {required_state}",
            "INVALID_PROJECT_STATE"
        )

class AgentException(AIVideoGeneratorException):
    """Agent-related exceptions"""
    pass

class AgentProcessingError(AgentException):
    def __init__(self, agent_name: str, error_message: str):
        super().__init__(f"Agent {agent_name} failed: {error_message}", "AGENT_PROCESSING_ERROR")

class AgentTimeoutError(AgentException):
    def __init__(self, agent_name: str, timeout_seconds: int):
        super().__init__(
            f"Agent {agent_name} timed out after {timeout_seconds} seconds",
            "AGENT_TIMEOUT"
        )

class ModelAPIError(AgentException):
    def __init__(self, provider: str, error_message: str):
        super().__init__(f"API error from {provider}: {error_message}", "MODEL_API_ERROR")

class ServiceException(AIVideoGeneratorException):
    """External service exceptions"""
    pass

class GoogleDocsError(ServiceException):
    def __init__(self, error_message: str):
        super().__init__(f"Google Docs error: {error_message}", "GOOGLE_DOCS_ERROR")

class GoogleSheetsError(ServiceException):
    def __init__(self, error_message: str):
        super().__init__(f"Google Sheets error: {error_message}", "GOOGLE_SHEETS_ERROR")

class PiAPIError(ServiceException):
    def __init__(self, error_message: str):
        super().__init__(f"PiAPI error: {error_message}", "PIAPI_ERROR")

class GoToHumanError(ServiceException):
    def __init__(self, error_message: str):
        super().__init__(f"GoToHuman error: {error_message}", "GOTOHUMAN_ERROR")

class KlingAPIError(ServiceException):
    def __init__(self, error_message: str):
        super().__init__(f"Kling API error: {error_message}", "KLING_API_ERROR")

class ValidationException(AIVideoGeneratorException):
    """Data validation exceptions"""
    pass

class InvalidScriptFormat(ValidationException):
    def __init__(self, format_issues: list):
        issues_str = ", ".join(format_issues)
        super().__init__(f"Invalid script format: {issues_str}", "INVALID_SCRIPT_FORMAT")

class InvalidShotData(ValidationException):
    def __init__(self, shot_number: int, issues: list):
        issues_str = ", ".join(issues)
        super().__init__(
            f"Invalid shot {shot_number} data: {issues_str}",
            "INVALID_SHOT_DATA"
        )

class InvalidCharacterData(ValidationException):
    def __init__(self, character_name: str, issues: list):
        issues_str = ", ".join(issues)
        super().__init__(
            f"Invalid character '{character_name}' data: {issues_str}",
            "INVALID_CHARACTER_DATA"
        )

class ProcessingException(AIVideoGeneratorException):
    """Processing workflow exceptions"""
    pass

class StageNotReady(ProcessingException):
    def __init__(self, stage: str, dependencies: list):
        deps_str = ", ".join(dependencies)
        super().__init__(
            f"Stage {stage} not ready. Missing dependencies: {deps_str}",
            "STAGE_NOT_READY"
        )

class ApprovalRequired(ProcessingException):
    def __init__(self, stage: str, approval_url: str = None):
        message = f"Human approval required for stage: {stage}"
        if approval_url:
            message += f". Approval URL: {approval_url}"
        super().__init__(message, "APPROVAL_REQUIRED")

class ProcessingTimeout(ProcessingException):
    def __init__(self, stage: str, timeout_minutes: int):
        super().__init__(
            f"Processing timeout for stage {stage} after {timeout_minutes} minutes",
            "PROCESSING_TIMEOUT"
        )

class BatchProcessingError(ProcessingException):
    def __init__(self, batch_id: str, error_details: dict):
        super().__init__(
            f"Batch processing failed for batch {batch_id}: {error_details}",
            "BATCH_PROCESSING_ERROR"
        )

class DatabaseException(AIVideoGeneratorException):
    """Database-related exceptions"""
    pass

class DatabaseConnectionError(DatabaseException):
    def __init__(self, database: str):
        super().__init__(f"Failed to connect to {database} database", "DATABASE_CONNECTION_ERROR")

class DocumentNotFound(DatabaseException):
    def __init__(self, collection: str, document_id: str):
        super().__init__(
            f"Document {document_id} not found in collection {collection}",
            "DOCUMENT_NOT_FOUND"
        )

class DuplicateDocumentError(DatabaseException):
    def __init__(self, collection: str, key: str):
        super().__init__(
            f"Duplicate document in collection {collection} with key {key}",
            "DUPLICATE_DOCUMENT"
        )

class FileException(AIVideoGeneratorException):
    """File-related exceptions"""
    pass

class FileNotFound(FileException):
    def __init__(self, file_path: str):
        super().__init__(f"File not found: {file_path}", "FILE_NOT_FOUND")

class InvalidFileFormat(FileException):
    def __init__(self, file_path: str, expected_formats: list):
        formats_str = ", ".join(expected_formats)
        super().__init__(
            f"Invalid file format for {file_path}. Expected: {formats_str}",
            "INVALID_FILE_FORMAT"
        )

class FileSizeError(FileException):
    def __init__(self, file_path: str, max_size_mb: int):
        super().__init__(
            f"File {file_path} exceeds maximum size of {max_size_mb}MB",
            "FILE_SIZE_ERROR"
        )

class AuthenticationException(AIVideoGeneratorException):
    """Authentication and authorization exceptions"""
    pass

class InvalidAPIKey(AuthenticationException):
    def __init__(self, service: str):
        super().__init__(f"Invalid API key for {service}", "INVALID_API_KEY")

class RateLimitExceeded(AuthenticationException):
    def __init__(self, service: str, reset_time: int = None):
        message = f"Rate limit exceeded for {service}"
        if reset_time:
            message += f". Reset in {reset_time} seconds"
        super().__init__(message, "RATE_LIMIT_EXCEEDED")

class InsufficientPermissions(AuthenticationException):
    def __init__(self, required_permission: str):
        super().__init__(
            f"Insufficient permissions. Required: {required_permission}",
            "INSUFFICIENT_PERMISSIONS"
        )

# Error response helper
def create_error_response(exception: AIVideoGeneratorException, include_traceback: bool = False):
    """Create standardized error response from exception"""
    response = {
        "success": False,
        "error": {
            "message": exception.message,
            "code": exception.error_code or "UNKNOWN_ERROR",
            "type": exception.__class__.__name__
        }
    }
    
    if include_traceback:
        import traceback
        response["error"]["traceback"] = traceback.format_exc()
    
    return response