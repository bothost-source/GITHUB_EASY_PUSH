"""
TARRIFIC HOST BOT - Error Handler
Exact error messages with location
"""

class ErrorHandler:
    """Handle and format errors with exact location and message"""

    @staticmethod
    def format_error(error_type, step, location, message, file_path=None, suggestion=None):
        """
        Format error for display

        error_type: "validation", "github_api", "network", "file_system", "user"
        step: which step failed (1-5)
        location: where it happened
        message: exact error message
        file_path: which file caused it (if applicable)
        suggestion: how to fix it
        """
        error_data = {
            "type": error_type,
            "step": step,
            "location": location,
            "message": message,
            "file": file_path,
            "suggestion": suggestion
        }
        return error_data

    @staticmethod
    def github_error(response_status, response_text, step, file_path=None):
        """Format GitHub API errors"""
        errors = {
            401: "GitHub authentication failed. Token expired or invalid.",
            403: "GitHub API rate limit exceeded. Retry in 15 minutes.",
            404: "Repository or resource not found.",
            422: "Validation failed. Repository name may already exist.",
            500: "GitHub server error. Try again later.",
        }

        message = errors.get(response_status, f"GitHub API error: {response_text}")

        return ErrorHandler.format_error(
            error_type="github_api",
            step=step,
            location="GitHub API",
            message=message,
            file_path=file_path,
            suggestion="Check /settings to reconnect GitHub or try again later."
        )

    @staticmethod
    def file_error(error, step, file_path=None):
        """Format file system errors"""
        errors = {
            "FileTooLarge": f"File too large. GitHub limit is 25 MB.",
            "InvalidZip": "ZIP file is corrupted or invalid.",
            "NoIndexHtml": "No index.html found at root of ZIP.",
            "PermissionDenied": "Cannot read/write file. Check permissions.",
        }

        message = errors.get(type(error).__name__, str(error))

        return ErrorHandler.format_error(
            error_type="file_system",
            step=step,
            location="File Processing",
            message=message,
            file_path=file_path,
            suggestion="Check your ZIP structure and file sizes."
        )

    @staticmethod
    def network_error(error, step):
        """Format network errors"""
        return ErrorHandler.format_error(
            error_type="network",
            step=step,
            location="Network",
            message=f"Connection failed: {str(error)}",
            suggestion="Check your internet connection and try again."
        )

    @staticmethod
    def validation_error(message, step, file_path=None):
        """Format validation errors"""
        return ErrorHandler.format_error(
            error_type="validation",
            step=step,
            location="Validation",
            message=message,
            file_path=file_path,
            suggestion="Check the requirements and try again."
        )

# Common error messages for hosting
HOSTING_ERRORS = {
    "missing_index": "No index.html found at root of ZIP. Entry point required.",
    "zip_corrupted": "ZIP extraction failed: {detail}",
    "file_too_large": "File {file} exceeds 25MB limit ({size} MB).",
    "repo_exists": "Repository '{name}' already exists. Use /sites to manage.",
    "auth_expired": "GitHub token expired. Reconnect in /settings.",
    "pages_disabled": "GitHub Pages not enabled. Check repository settings.",
    "rate_limit": "GitHub API rate limit (60/hr). Retry in {minutes} minutes.",
    "timeout": "Connection timeout at {seconds}s. Check your network.",
    "max_sites": "Maximum {limit} sites reached. Delete old sites first.",
}
