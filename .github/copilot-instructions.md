<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Clark County APN Property Scraper

This project is a high-performance web scraper for extracting property data from Clark County Nevada's assessor website.

## Code Guidelines

- Focus on performance: target 0.5-1 second per APN
- Use requests.Session() for connection pooling
- Parse HTML with lxml parser for speed
- Implement proper error handling and retry logic
- Use type hints for better code quality
- Follow PEP 8 naming conventions
- Add comprehensive logging for debugging