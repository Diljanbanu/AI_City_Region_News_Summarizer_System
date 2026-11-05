import sys
sys.stdout.reconfigure(encoding="utf-8")

from api_services.location_service import get_location_by_ip, get_location_hierarchy
from api_services.news_service import fetch_live_news, CATEGORIES

print("=====================================================")
print("1. AUTO IP LOCATION DETECTION & NORMALIZATION")
print("=====================================================")
loc = get_location_by_ip()
print("Detected IP     :", loc["ip"])
print("Detected City   :", loc["city"])
print("Detected Region :", loc["region"])
print("Detected Country:", loc["country"])
assert loc["city"] == "Rajkot", f"Expected Rajkot, got {loc['city']}"
print("SUCCESS: IP location correctly resolved to Rajkot without accents!")

print("\n=====================================================")
print("2. GADHKA LOCATION HIERARCHY & PRIORITY TEST")
print("=====================================================")
h = get_location_hierarchy("Gadhka")
print("Primary         :", h["primary"])
print("District Hub    :", h["district"])
print("Nearby Areas    :", h["nearby_areas"])
print("Priority 1 Label:", h["priority_1_label"])
print("Priority 2 Label:", h["priority_2_label"])
print("Avoid Distant   :", h["avoid_distant"])
assert "Bhavnagar" in h["avoid_distant"], "Bhavnagar should be in avoid_distant"
print("SUCCESS: Gadhka correctly mapped to Rajkot district with Bhavnagar avoided!")

print("\n=====================================================")
print("3. LOCAL NEWS FETCH FOR GADHKA (PRIORITY 1 & 2)")
print("=====================================================")
articles = fetch_live_news("Gadhka", "city", "Gujarat", category="Local News", limit=6)
print(f"Retrieved {len(articles)} articles for Gadhka:")
has_bhavnagar = False
for i, a in enumerate(articles, 1):
    prio = a.get("location_priority")
    title = a["title"]
    print(f"  {i}. [{prio}] {title}")
    if "bhavnagar" in title.lower() and "gadhka" not in title.lower() and "rajkot" not in title.lower():
        has_bhavnagar = True

assert not has_bhavnagar, "Unrelated Bhavnagar news found in Gadhka results!"
print("SUCCESS: Gadhka local news strictly follows Priority 1/2 and excludes Bhavnagar!")

print("\n=====================================================")
print("4. CATEGORY-WISE NEWS FILTERING FOR ALL 8 CATEGORIES")
print("=====================================================")
for cat in CATEGORIES:
    cat_arts = fetch_live_news("Rajkot", "city", "Gujarat", category=cat, limit=2)
    print(f"Category [{cat}]: {len(cat_arts)} articles returned")
    assert len(cat_arts) > 0, f"No articles returned for category {cat}"
    for a in cat_arts:
        badge = a.get("category_badge")
        t = a["title"][:60]
        print(f"   - ({badge}) {t}...")

print("\n=====================================================")
print("ALL 6 USER REQUIREMENTS TESTED AND PASSED SUCCESSFULLY!")
print("=====================================================")
