with open("app/data/seed_osm_micro.py", "r") as f:
    text = f.read()

import re
text = re.sub(r"for food_data in foods_data:.*?db.add\(f\)", 
"""for food_data in foods_data:
                poi = random.choice(all_pois)
                f = Food(poi_id=poi.id, name=food_data.name, cuisine=food_data.category, price_level=2, rating=5.0, heat_score=1000, image_url=food_data.image_url)
                db.add(f)""", text, flags=re.DOTALL)

with open("app/data/seed_osm_micro.py", "w") as f:
    f.write(text)
