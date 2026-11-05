import os, sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from api_services.location_service import get_location_by_ip
from api_services.news_service import fetch_live_news
from api_services.ai_summary_service import generate_ai_news_summary

print("=== STEP 1: IP LOCATION DETECTION (ipinfo.io with IPINFO_TOKEN) ===")
loc = get_location_by_ip()
city = loc['city']
print("IP       :", loc['ip'])
print("City     :", city)
print("Region   :", loc['region'])
print("Country  :", loc['country'])
print("Provider :", loc['api_provider'])
print("Postal   :", loc.get('postal', 'N/A'))
print("Timezone :", loc.get('timezone', 'N/A'))

print()
print(f"=== STEP 2: LIVE NEWS FOR {city} ===")
articles = fetch_live_news(city, 'city', limit=4)
print(f"Found {len(articles)} live articles:")
for a in articles:
    eng = a.get('api_engine', '?')
    print(f"  [{eng}] {a['title']} -- {a['source']}")

print()
print("=== STEP 3: GEMINI AI SUMMARY ===")
summary = generate_ai_news_summary(articles[0])
print("AI Engine :", summary['ai_engine'])
print("Summary   :", summary['concise_summary'])
print("Main Event:", summary['main_event'])
print("Urgency   :", summary['urgency_level'])
print()
print("ALL SYSTEMS WORKING PERFECTLY!")
