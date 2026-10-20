MIN_NAME_LENGTH = 4

# Acronyms an intern would know. Anything else in capitals is flagged.
ALLOWED_ACRONYMS = {"ID", "URL", "HTTP", "HTTPS", "JSON", "HTML", "CSS", "XML", "API"}

# Names a framework requires, like Next.js route handlers, so they can't be lengthened.
FRAMEWORK_NAMES = {"GET", "PUT", "POST", "PATCH", "HEAD", "DELETE", "OPTIONS"}
