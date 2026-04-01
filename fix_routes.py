import re

with open("app/routes/routes_b.py", "r") as f:
    content = f.read()

# Make recommendations return the image_url
content = content.replace('"recommendations": [{"id": i.id, "name": i.name, "category": i.category} for i in top_items]', 
                          '"recommendations": [{"id": i.id, "name": i.name, "category": i.category, "image_url": getattr(i, "image_url", None), "score": score_func(i)} for i in top_items]')

with open("app/routes/routes_b.py", "w") as f:
    f.write(content)
