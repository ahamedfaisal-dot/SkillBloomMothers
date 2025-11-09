# SkillBloom MVP

## Overview
SkillBloom is an AI-powered re-entry career platform designed for mothers returning to work after a career break. The platform provides personalized assessments, skill-building pods, AI career recommendations, and wellness tracking features.

## Tech Stack
- **Backend**: Flask (Python) REST API with JWT authentication
- **Frontend**: HTML, CSS, JavaScript with Chart.js for visualizations
- **Database**: SQLite (MVP - can be upgraded to PostgreSQL later)
- **AI**: Google Gemini 1.5 Flash for intelligent chatbot and career recommendations
- **Theme**: Dark mode with teal and lavender accents

## Project Structure
```
/
├── backend/
│   ├── routes/          # API route modules
│   ├── models/          # Database models
│   └── utils/           # Utility functions
├── static/
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
│   └── images/          # Image assets
├── templates/           # HTML templates
├── app.py              # Main Flask application
├── database.db         # SQLite database
└── requirements.txt    # Python dependencies
```

## Core Features
1. **User Authentication**: JWT-based login/signup with three roles (Returning Mother, Company, Admin)
2. **Assessment Engine**: Two-stage testing (personality + skills) with role fit scoring
3. **Six Pod Modules**:
   - Skill Pod: Learning paths and badges
   - Company Pod: Mock training projects
   - Health Pod: Wellness tracker
   - Baby Monitor Pod: Simulated IoT data with real-time charts
   - Mental Health Pod: Journaling and mood check-ins
   - Post-Placement Pod: Career growth tracker
4. **AI Recommendations**: Rule-based career matching
5. **AI Mentor Chatbot**: Pre-defined responses for guidance
6. **Dashboard**: Progress visualization with charts

## Database Schema
- **users**: User profiles with skills and personality data
- **assessments**: Test results and scores
- **pods**: Pod progress and badges
- **ai_logs**: Chatbot interaction history
- **baby_monitor_data**: Simulated IoT sensor readings

## Recent Changes
- 2025-11-07: Initial project setup with Flask backend structure
- 2025-11-07: Complete MVP implementation with all features
- 2025-11-07: Integrated Google Gemini AI for intelligent chatbot and career recommendations

## User Preferences
- Modern, responsive UI design
- Dark mode with teal/lavender color scheme
- Simulated AI/ML for MVP (no heavy models)
- Full-stack application running on Replit

## Development Notes
- Baby monitor updates every 10 seconds with mock sensor data
- AI Mentor uses Google Gemini 1.5 Flash for context-aware career guidance
- Career recommendations powered by Gemini AI with fallback to rule-based logic
- All features designed for demo/MVP purposes

## API Key Configuration
- GEMINI_API_KEY: Used for AI chatbot and career recommendations
- SESSION_SECRET: Used for JWT authentication
