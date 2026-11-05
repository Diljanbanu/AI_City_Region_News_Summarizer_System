# 🏙️ AI-Powered City/Region News Summarization System

An intelligent, location-aware news summarization platform built with Python, Streamlit, FastAPI, and Google Gemini AI. The system automatically identifies the user's location via IP address, retrieves live location-relevant news articles, enriches them with real-time local weather context, and generates structured AI summaries highlighting key events and regional impacts.

---

## 🌟 Key Features

- **📍 Automatic IP Geolocation**: Detects user's City, Region/State, Country, and IP address using a multi-provider fallback API engine (`ipapi.co`, `ip-api.com`, `ipinfo.io`). Includes manual city/region search override.
- **📰 Live City & Region News Retrieval**: Fetches live news for any city or region worldwide via Google News RSS & NewsAPI.
- **🤖 AI-Powered Article Summarization**: Leverages **Google Gemini AI API** (`google-genai` SDK) with an integrated smart NLP fallback summarizer. Generates:
  - 📝 Concise 2-3 sentence article summary
  - 🔑 Bulleted important points & key facts
  - 🎯 Main event / core development
  - 🏙️ Impact on the city/region and local residents
  - ⚠️ Urgency rating & category tags
- **🌤️ Live Weather Context (4th API)**: Integrates Open-Meteo API to display real-time local weather metrics alongside city news.
- **🔎 Dual Search Modes**:
  - 🏙️ **City-based News**: Tailored news focusing on urban transit, local infrastructure, civic alerts, and city events.
  - 🌎 **Region-based News**: Broader news covering state developments, regional policies, energy, and inter-district trade.
- **🎨 Modern Glassmorphism UI**: Beautiful, interactive Streamlit frontend with responsive cards, badges, dark theme styling, and interactive AI summarization triggers.

---

## 🏗️ Project Architecture & APIs Used

| API Type | Provider / Engine | Purpose |
|---|---|---|
| **📍 Location / IP API** | `ipapi.co` / `ip-api.com` / `ipinfo.io` | Auto-detect user IP, city, region, country & lat/lon |
| **📰 News API** | Google News Live RSS / NewsAPI.org | Retrieve live news articles for target city or region |
| **🤖 AI API** | Google Gemini AI (`google-genai` SDK) | Deep article analysis, structured summaries & regional impact |
| **🌤️ 4th Relevant API** | Open-Meteo Weather API | Real-time weather, temperature & environment metrics |

---

## 📁 File Structure

```
d:\MCA\News_Summerise_System_API\
│
├── .env                       # API Key configuration
├── .env.example               # Template for API keys
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation & instructions
│
├── api_services/              # Modular API Services
│   ├── __init__.py
│   ├── location_service.py    # 📍 IP Geolocation API Service
│   ├── weather_service.py     # 🌤️ Live Weather API Service (4th API)
│   ├── news_service.py        # 📰 Live News Retrieval API Service
│   └── ai_summary_service.py  # 🤖 AI & Gemini Summarization Service
│
├── app.py                     # 🏙️ Streamlit Main Interactive Web Frontend
└── main.py                    # 🌐 FastAPI REST API Backend Server
```

---

## 🚀 Terminal Execution Guide (VS Code)

Follow these exact steps in your VS Code terminal to run the application:

### Step 1: Open Terminal in VS Code
Ensure your terminal working directory is set to `d:\MCA\News_Summerise_System_API`.

### Step 2: Activate the Virtual Environment
Activate the pre-configured virtual environment in PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```
*(If using standard Command Prompt, run `.\venv\Scripts\activate.bat` instead)*

### Step 3: Run the Streamlit Web Application (Frontend UI)
Execute the following command to launch the full interactive UI in your web browser:
```powershell
streamlit run app.py
```
*The app will automatically open at `http://localhost:8501`*

---

## 🌐 Optional: Run the FastAPI REST API Server

If you wish to test the backend API endpoints or access interactive Swagger documentation (`http://127.0.0.1:8000/docs`), run:

```powershell
uvicorn main:app --reload
```

---

## 🔑 Environment Configuration (.env)

The application operates out-of-the-box using free live news and smart NLP summarization. For enhanced AI summarization powered by Google Gemini AI, add your free key to `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
NEWS_API_KEY=optional_news_api_key
```
