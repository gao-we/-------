import urllib.request
import json

try:
    req = urllib.request.Request("http://localhost:8000/api/recommendation/suggest/attractions")
    with urllib.request.urlopen(req) as response:
        print("Attractions list API:")
        print(response.read().decode('utf-8')[:200])
except Exception as e:
    print(f"Error fetching first api: {e}")

try:
    req2 = urllib.request.Request("http://localhost:8000/api/recommendation/suggest/attractions/1")
    with urllib.request.urlopen(req2) as response:
        print("Attraction detail API:")
        print(response.read().decode('utf-8')[:200])
except Exception as e:
    print(f"Error fetching detail api: {e}")
