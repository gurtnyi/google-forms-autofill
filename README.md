# Google Forms Autofiller

A Python script that automates repeated Google Forms submissions. This project was entirely AI-generated through prompts to DeepSeek, with the code created and modified by the AI.

## Features
- Automated form submission with customizable request counts
- Proxy support for distributed requests
- Comprehensive logging system
- Session tracking across multiple runs

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

Create the following configuration files before running the script:

1. **`url.txt`** - Contains the Google Form URL
2. **`text.txt`** - Contains the text that identifies the option to select
3. **`proxies.txt`** (optional) - List of proxies for distributed requests

## Usage

Run the script with:
```bash
python google_form_automator.py
```

When prompted, enter the number of requests you want to perform per session.

## Log Files

The script generates two log files:

1. **`log.txt`** - Overwritten each time the script runs, contains current session details
2. **`completed_requests.txt`** - Persistent log tracking all completed sessions with:
   - Timestamp of execution
   - Number of successfully completed requests
   - Total desired requests
   - Remaining requests
   - Cumulative completed requests

## Project Structure

```
google-forms-autofill/
├── google_form_automator.py  # Main script
├── requirements.txt          # Python dependencies
├── url.txt                   # Form URL
├── text.txt                  # Option text to select
├── proxies.txt              # Optional proxy list
├── log.txt                  # Session log (overwritten)
└── completed_requests.txt   # Persistent request history
```
