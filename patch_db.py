import re

def patch_file(filepath, pattern, replacement):
    with open(filepath, 'r') as f:
        content = f.read()
    content = re.sub(pattern, replacement, content)
    with open(filepath, 'w') as f:
        f.write(content)

patch_file("docs/database.sql", r"(category VARCHAR\(50\),\n\s*latitude DECIMAL\(10, 7\),\n\s*longitude DECIMAL\(10, 7\))", r"\1,\n    image_url VARCHAR(255)")
patch_file("docs/database.sql", r"(rating DECIMAL\(3, 2\) DEFAULT 0.0 CHECK \(rating BETWEEN 0.0 AND 5.0\))", r"\1,\n    image_url VARCHAR(255)")

patch_file("app/models/domain.py", r"(longitude = Column\(DECIMAL\(10, 7\)\))", r"\1\n    image_url = Column(String(255))")
patch_file("app/models/domain.py", r"(rating = Column\(DECIMAL\(3, 2\), default=0.0\))", r"\1\n    image_url = Column(String(255))")

patch_file("app/models/schemas.py", r"(longitude: float\n\s*category: str\s*# e.g., 'attraction', 'restaurant', 'hotel')", r"\1\n    image_url: Optional[str] = None")

