---
sidebar_position: 4
sidebar_label: Features and Requirements
---

# Features and Requirements

## Main Feature: Bot /search Command
### Feature Overview
Main interaction with the bot- allows user to submit a query for the bot to return suitable jobs that match the query contents. This allows users who can use/already use the free service of Discord to assist them in finding jobs, saving them the trouble of running into any costs trying to apply somewhere. (v.1)
### Functional Requirements
- Accepts raw input from the user which is then saved to a temporary string variablr
- The variable is sent off to the search handler to for a quick blank test check before returning a placeholder message
- Discord bot displays placeholder message to the user
(end v.1)
### Non-Functional Requirements
- Response is instant
- Functionality consistent through multiple calls
- Easy to use, simple slash command- easy to test
- Bot token protected and hidden via local .env
(end v.1)
### Design and Architecture
discord_bot.py is responsible for housing the slash command and its dependecies, while search_handler.py generates and returns the placeholder message for the user to see. The backend would connect to the search_handler.py to parse the string into a JSON format to be able to use for job scraping with the help of AI. (v.1)
### Implementation Details
Keeping the core dependecies and commands separate from the search allows not only for ease of readibility, but also allows for easier maintainance, breaking the code down into enough smaller componenents to make any additions or fixes easy. Discord bot token (enviroment variable) is loading from local .env file where it is protected and hidden. The token is neccesary for the bot to work. (v.1)
### Testing and Verification
Four automated tests were created to test the Python code before building the bot itself- One was a generic search test to simulate a Discord interaction, making sure the code would respond to it. The rest were minor error handling tests for the search query- a valid query test, a blank space test, and whitespace test. Finally, with the bot live and in a test server, several live tests were performed with no issues. (v.1)
### Future Work
For now, this simple code only returns a generic placeholder message with the user's query string in formatted into it. With the backend properly setup and the AI (Gemini) functional, eventually the string will be parsed and used to job scrape via JobSpy to return proper results to the user. (v.1)