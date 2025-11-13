# Family Hub - Turning Dynasties Into Golden Legacies

![Family Hub](https://img.shields.io/badge/Family-Hub-purple?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-3.0-green?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue?style=for-the-badge)

## 🌟 Overview

Family Hub is a comprehensive web application designed to foster family connection, shared moments, and the preservation of legacies. It transforms family relationships into "golden legacies" through engaging features, ensuring families stay connected and memories are preserved for future generations.

**Live Site:** [harmonizedlegacy.live](https://harmonizedlegacy.live)

## ✨ Key Features

### 👨‍👩‍👧‍👦 Family Management
- **Family-Based Signup & Invite System**: Unique invite codes for joining families
- **Extensive Profile System**: Rich personal profiles with legacy sections
- **Family Administration**: First member becomes admin with full management capabilities

### 📖 Memory Preservation
- **Digital Family Scrapbook**: Create beautiful scrapbook pages with photos, stories, dates, locations, and mood tags
- **Remembrance Memorial Page**: Honor deceased family members with detailed life stories
- **Personal Walls & Social Feed**: Share thoughts, media, and interact via likes and comments
- **Photo Galleries**: Organized albums for preserving family moments

### 🗓️ Organization
- **Family Calendar**: Shared events and celebrations
- **Chore Management**: Assign and track family tasks
- **Messaging System**: Direct communication with read/unread status

### 🤖 AI Harmony Assistant
- Powered by GPT-4o
- Genealogy support and family insights
- Activity suggestions tailored to your family
- Smart scrapbook moment detection
- Event planning assistance

### 💎 Data Marketplace & ILAH Tokens
- Earn cryptocurrency (ILAH) by sharing anonymized data
- Granular consent controls
- Built-in wallet integration
- Exchange integration for trading

### 📞 Communication
- **Video Calling**: Integrated Jitsi Meet for family video calls
- **Email Integration**: Notifications via Replit Mail

## 🏗️ Technical Architecture

### Backend Stack
- **Framework**: Python Flask 3.0
- **Database**: PostgreSQL (Neon-backed via Replit)
- **Authentication**: Replit Auth (OAuth2) - Google, GitHub, X, Apple, email/password
- **Server**: Gunicorn WSGI on port 5000

### Frontend Stack
- **Template Engine**: Jinja2
- **Styling**: Custom CSS with gradient themes and animations
- **JavaScript**: Vanilla JS for interactive features

### Integrations
- **AI**: OpenAI GPT-4o via Replit AI Integrations
- **Email**: Replit Mail
- **File Storage**: Replit Object Storage (future enhancement)
- **Video**: Jitsi Meet
- **Blockchain**: Solana for ILAH tokens

### Security
- Session-based authentication
- OAuth2 compliance
- Environment variable secret management
- Family-based data isolation

## 📁 Project Structure

```
family-hub/
├── docs/                      # Documentation
│   ├── agent-notes/          # AI Agent session notes
│   ├── architecture/         # System architecture docs
│   ├── database/            # Database schemas & exports
│   └── deployment/          # Deployment guides
├── static/                   # Static assets
│   ├── css/                 # Stylesheets
│   ├── js/                  # JavaScript files
│   └── uploads/             # User uploads
├── templates/               # HTML templates
│   ├── base.html           # Base template
│   ├── landing.html        # Landing page
│   └── ...                 # Feature templates
├── app.py                  # Flask application factory
├── main.py                 # Application entry point
├── models.py               # Database models
├── routes.py               # Application routes
├── replit_auth.py          # Authentication handler
├── ai_helper.py            # AI Harmony assistant
├── data_marketplace.py     # ILAH token marketplace
├── email_helper.py         # Email functionality
├── upload_helper.py        # File upload handling
└── replit.md              # Project memory & preferences
```

## 🚀 Getting Started

### Prerequisites
- Replit account
- Python 3.11+
- PostgreSQL database

### Installation

1. **Clone the repository** or open in Replit

2. **Install dependencies**:
```bash
# Python packages are managed via pyproject.toml and automatically installed
```

3. **Setup database**:
   - Development and production databases are managed via Replit Database pane
   - Run the app to auto-create tables

4. **Configure integrations**:
   - Replit Auth (automatic)
   - OpenAI AI Integration (automatic)
   - Replit Mail (automatic)
   - Object Storage (setup required)

5. **Run the application**:
```bash
gunicorn --bind=0.0.0.0:5000 --reuse-port main:app
```

## 🔧 Configuration

### Environment Variables
All secrets are managed via Replit's secure environment:
- `AI_INTEGRATIONS_OPENAI_API_KEY` - Auto-managed
- `AI_INTEGRATIONS_OPENAI_BASE_URL` - Auto-managed
- `DATABASE_URL` - Auto-managed
- `REPLIT_DB_URL` - Auto-managed

### Database Migration
To migrate data from development to production:
```bash
# Use safe_production_import.sql in the Database pane (Production mode)
```

## 📊 Database Schema

### Core Tables
- `families` - Family information and invite codes
- `users` - User accounts with family associations
- `family_profiles` - Detailed profile information and legacy messages

### Features
- `events` - Calendar events and celebrations
- `chores` - Task assignments
- `messages` - Direct messaging
- `posts` - Social feed content
- `post_likes`, `post_comments` - Engagement
- `scrapbook_pages`, `scrapbook_photos` - Memory preservation
- `remembrance_members` - Memorial tributes
- `photos` - Photo gallery
- `user_wallets`, `token_transactions`, `exchanges` - ILAH marketplace

## 🎨 Design Philosophy

- **Warmth & Connection**: Gradient purple/blue themes conveying love and family
- **Accessibility**: Responsive design for all devices
- **Engagement**: Smooth animations and interactive elements
- **Legacy Focus**: Dedicated sections for preserving family heritage

## 📝 Recent Updates

### November 2025
- ✅ Fixed critical authentication bugs (JWT verification, OAuth state)
- ✅ Resolved login redirect loops
- ✅ Improved database session handling
- ✅ Enhanced navbar with smooth animations and sticky positioning
- ✅ Fixed website boundaries and responsive layout
- ✅ Created production data export system

## 🤝 Contributing

This is a private family application. For feature requests or bug reports, contact the administrator.

## 📄 License

Proprietary - All rights reserved

## 🔗 Links

- **Live Site**: [harmonizedlegacy.live](https://harmonizedlegacy.live)
- **Documentation**: See `/docs` folder
- **Support**: Contact family administrator

## 👨‍💻 Developed With

Built with ❤️ using Replit's integrated development environment and AI Agent assistance.

---

**Turning Dynasties Into Golden Legacies** 💝
