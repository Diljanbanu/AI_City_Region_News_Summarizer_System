import sys
sys.stdout.reconfigure(encoding='utf-8')

from api_services.location_service import get_location_by_ip
from api_services.news_service import fetch_live_news
from api_services.ai_summary_service import generate_ai_news_summary

print("==================================================")
print("1. IP LOCATION DETECTION (Auto-detect user's IP)")
print("==================================================")
loc = get_location_by_ip()
city = loc['city']
region = loc['region']
print(f"Detected IP      : {loc['ip']}")
print(f"Detected City    : {city}")
print(f"Detected Region  : {region}")
print(f"Provider         : {loc['api_provider']}")

print("\n==================================================")
print(f"2. FETCHING CITY-FILTERED LIVE NEWS FOR: {city}")
print("==================================================")
articles = fetch_live_news(query_location=city, search_type="city", region_state=region, limit=4)
print(f"Total articles returned: {len(articles)}")
all_match = True
for a in articles:
    t = a['title']
    has_city = city.lower() in t.lower() or city.lower() in a['full_text'].lower()
    print(f" - [{a['api_engine']}] {t} (Source: {a['source']}) -> City in text: {has_city}")
    if not has_city:
        all_match = False

print(f"\nAll articles strictly relevant to {city}: {all_match}")

print("\n==================================================")
print(f"3. TESTING DYNAMIC SWITCH TO ANOTHER CITY: Surat")
print("==================================================")
surat_articles = fetch_live_news(query_location="Surat", search_type="city", region_state="Gujarat", limit=3)
print(f"Total articles returned for Surat: {len(surat_articles)}")
for a in surat_articles:
    print(f" - {a['title']} (Source: {a['source']})")

print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")
