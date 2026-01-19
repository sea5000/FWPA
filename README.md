# FWPA

## Overview
BookMe — a web based study tool for you to build flashcard sets, upload study content, study with, and share content with friends.

## Technologies Used
- Flask Backend
- Model View Controller structure
- Peppering / Salting with Python's argon2 library
- Incorporated API for Gemini to create flashcard decks from prompts and documents

## Running
- Install requirments from `requirements.txt`
- run the main app.py, `python app.py`

## Team Overview:
Although we did try to divide the project up as cleanly as possible there is always bleedover but for the most part these tasks were handled by each person:

### Viktoria
- Handled community / Freinds / Notes / Timer pages
- Appropriate database models / mongodb collections
### Elisabed
- Instituted major UI / UX updates, setting the theme for the whole project.
- Handled profile / login / streak / signup pages
- Appropriate user profile database managment
### Spencer
- Hanled flashcard pages (edit / study / overview)
- Appropriate database models and routes
- Managed salting and peppering implementation
- Implemented Gemini API