# Password hashing and JWT creation live directly in app/api/auth.py,
# next to the endpoints that use them — same convention as the
# reference project. This file is kept for structural consistency and
# is where you'd put shared crypto helpers if a second module (e.g.
# admin panel auth, later) needs to reuse them.
