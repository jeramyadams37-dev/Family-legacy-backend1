# Family Hub - Turning Dynasties Into Golden Legacies

## Overview
Family Hub is a comprehensive web application designed to foster family connection, shared moments, and the preservation of legacies. It aims to transform family relationships into "golden legacies" through engaging features, ensuring families stay connected and memories are preserved for future generations.

## User Preferences
- Focus on warmth, love, and meaningful family connections
- Emphasis on legacy preservation and turning "dynasties into golden legacies"
- Keep families engaged with heartwarming fun
- Extensive profile capabilities are essential
- AI-powered smart assistance for genealogy and family questions
- Family-based organization with surname pages and invite system

## System Architecture
The application is built with Python Flask and uses PostgreSQL for data persistence. Authentication is handled via Replit Auth, supporting various providers. Email functionalities are integrated using Replit Mail, and AI capabilities leverage OpenAI through Replit AI Integrations. File storage for photos will utilize Replit Object Storage. The application is designed for family-based data isolation, ensuring users only access their own family's information.

**UI/UX Decisions:**
The design emphasizes a beautiful, responsive interface with gradient themes, animations, and modern aesthetics, particularly seen in the personal walls and data marketplace.

**Core Features:**
- **Family-Based Signup & Invite System:** Users can create or join families using unique invite codes, with the first member becoming an administrator.
- **Extensive Profile System:** Rich personal profiles include legacy sections for members to articulate their desired impact.
- **Remembrance Memorial Page:** Dedicated space to honor deceased family members, preserving their life stories and memories.
- **Digital Family Scrapbook:** Create beautiful scrapbook pages to preserve special family moments, celebrations, and memories. Features include cover photos, story narratives, event dates, location tracking, mood/feeling tags, and AI-powered suggestions when posting to profile feed that detect meaningful moments worth scrapbooking. Fully editable with family-wide access.
- **Family Calendar:** Shared events and chore management with assignments.
- **Photo Galleries:** Organized albums for sharing and preserving family moments.
- **Messaging System:** Direct communication within the family with read/unread status.
- **Personal Walls & Social Feed:** Individual member feeds for sharing thoughts, media, and interacting with posts via likes and comments. AI Harmony intelligently suggests creating scrapbook pages for special moments.
- **Video Calling:** Integration with Jitsi Meet for family video calls.
- **Data Marketplace & ILAH Token Integration:** Users can earn Ilah Hughs (ILAH) cryptocurrency tokens by sharing anonymized data, with granular consent controls, a built-in wallet, and exchange integration for trading and withdrawals.
- **AI Harmony:** An AI assistant powered by GPT-4o, providing insights, genealogy support, activity suggestions, planning assistance, and smart scrapbook moment detection based on comprehensive family data.

**System Design Choices:**
- Session-based authentication with OAuth2.
- Responsive design for optimal viewing across devices.
- AI and Email integrations managed through Replit services, simplifying API key management.
- Gunicorn WSGI server for application deployment.

## External Dependencies
- **Database:** PostgreSQL
- **Authentication:** Replit Auth (Google, GitHub, X, Apple, email/password)
- **Email:** Replit Mail (via blueprint:replitmail)
- **AI:** OpenAI (via Replit AI Integrations)
- **File Storage:** Replit Object Storage (for future photo uploads)
- **Video Calling:** Jitsi Meet
- **Blockchain:** Solana (for ILAH token and data marketplace)
- **Cryptocurrency Exchanges:** Raydium, Jupiter, Orca, Gate.io, MEXC (for ILAH token trading)
- **Solana Wallets:** Phantom, Solflare (for ILAH token withdrawals)