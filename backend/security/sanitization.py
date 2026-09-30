"""Input sanitization and prompt-injection protection."""
import re
import hashlib
from config import settings


# Patterns that indicate prompt injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?above",
    r"disregard\s+(all\s+)?previous",
    r"you\s+are\s+now\s+(?:a|an)\s+",
    r"new\s+instructions?\s*:",
    r"system\s*:\s*you",
    r"forget\s+(everything|all)",
    r"override\s+(your|the)\s+(instructions|rules|guidelines)",
    r"pretend\s+(you\s+are|to\s+be)",
    r"act\s+as\s+(if|though)",
    r"from\s+now\s+on\s+you",
    r"</?(system|assistant|user|prompt)>",
    r"\[INST\]|\[/INST\]",
    r"<\|im_start\|>|<\|im_end\|>",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def detect_prompt_injection(text: str) -> tuple[bool, list[str]]:
    """Check text for prompt injection patterns.
    Returns (is_suspicious, list_of_matched_patterns).
    """
    matches = []
    for i, pattern in enumerate(COMPILED_PATTERNS):
        if pattern.search(text):
            matches.append(INJECTION_PATTERNS[i])
    return len(matches) > 0, matches


def sanitize_input(text: str) -> str:
    """Sanitize user input — strip control characters, limit length."""
    if not text:
        return ""
    # Remove null bytes and control chars (keep newlines, tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Limit to reasonable length (50KB)
    text = text[:50000]
    return text.strip()


def mask_sensitive_data(text: str) -> str:
    """Mask PII and sensitive data patterns before sending to LLM."""
    # SSN pattern
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '***-**-****', text)
    # Credit card patterns (basic)
    text = re.sub(r'\b(?:\d{4}[-\s]?){3}\d{4}\b', '****-****-****-****', text)
    # Email addresses (partial mask)
    text = re.sub(
        r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
        lambda m: m.group(1)[:2] + '***@' + m.group(2),
        text
    )
    # Account numbers (sequences of 8+ digits)
    text = re.sub(r'\b\d{8,}\b', lambda m: '*' * len(m.group()), text)
    return text


def sanitize_llm_output(output: str) -> str:
    """Validate and clean LLM output before returning to users."""
    if not output:
        return ""
    # Remove any system-prompt leakage markers
    output = re.sub(r'<\|?(system|im_start|im_end)\|?>', '', output)
    # Remove potential code execution markers
    output = re.sub(r'```(bash|sh|cmd|powershell)\s*\n.*?```', '[code block removed]', output, flags=re.DOTALL)
    return output.strip()


def hash_content(content: str) -> str:
    """Create a SHA-256 hash of content for audit tracking."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def validate_file_type(filename: str) -> bool:
    """Check if uploaded file type is allowed."""
    allowed = {'.pdf', '.docx', '.txt', '.csv', '.md', '.json'}
    ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in allowed


def validate_file_size(size_bytes: int) -> bool:
    """Check if file size is within limits."""
    return size_bytes <= settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
