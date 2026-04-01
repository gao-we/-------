import re

with open("app/routes/routes_b.py", "r") as f:
    content = f.read()

# Filter out null image_urls so we actually show real ones in UI
content = content.replace('query = db.query(POI)', 
                          "query = db.query(POI).filter(POI.image_url != None)")

with open("app/routes/routes_b.py", "w") as f:
    f.write(content)
