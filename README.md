# AI SQL Agent

A beginner-friendly Gen AI project:

Natural Language Question
→ LLM SQL Generation
→ SQLite SQL Execution
→ Result Display
→ AI Explanation
→ Query History
→ Streamlit UI

## Features

- SQLite sample sales database
- Natural-language questions
- LLM-generated SQLite SQL
- Read-only SQL safety check
- Query execution with pandas
- AI explanation of results
- In-session query history
- Streamlit interface

## Setup

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your API key.

Windows PowerShell:
```powershell
$env:OPENAI_API_KEY="your_key"
```

Linux/macOS:
```bash
export OPENAI_API_KEY="your_key"
```

4. Run:

```bash
streamlit run app.py
```

The app creates `sales.db` automatically the first time.

## Example questions

- Which customer spent the most money?
- What is the total sales amount?
- Which product sold the most units?
- Show sales by city.
- What is the average order value?

## Architecture

User
  ↓
Streamlit UI
  ↓
Prompt + SQLite schema
  ↓
LLM
  ↓
Generated SQL
  ↓
Read-only SQL validation
  ↓
SQLite
  ↓
Pandas DataFrame
  ↓
LLM explanation
  ↓
Streamlit result

## Important learning concepts

This project demonstrates prompt engineering, LLM API usage, schema-aware SQL generation, tool execution, validation, structured application flow, and Streamlit UI.

For production use, add stronger SQL parsing/validation, authentication, logging, rate limits, and a database user with restricted permissions.
