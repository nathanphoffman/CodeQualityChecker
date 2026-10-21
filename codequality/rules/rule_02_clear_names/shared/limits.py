MIN_NAME_LENGTH = 4

# Acronyms an intern would know. Anything else in capitals is flagged.
ALLOWED_ACRONYMS = {"ID", "URL", "HTTP", "HTTPS", "JSON", "HTML", "CSS", "XML", "API"}

# Names a framework requires, like Next.js route handlers, so they can't be lengthened.
FRAMEWORK_NAMES = {"GET", "PUT", "POST", "PATCH", "HEAD", "DELETE", "OPTIONS"}

# Share of names allowed to be bad at full credit, since some short names like num are fine and hard to list: 1 in 36
# (about 2.8%), so a 36 line function may have one. Past it the credit slides like rule 1's: 90% at 6 ** 0.5 times this
# share (about 6.8%), about 9% at 6 times it (about 17%).
FREE_SHARE = 1 / 6 ** 2
SHARE_EDGE_POWER, SHARE_EDGE_CREDIT = 0.5, 0.90
