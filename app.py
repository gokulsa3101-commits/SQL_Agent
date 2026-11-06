import os
import sqlite3
import re
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()
DB_PATH = "sales.db"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.6-flash"

st.set_page_config(
    page_title="AI SQL Agent",
    page_icon="🤖",
    layout="wide"
)


def get_schema():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT name, sql
            FROM sqlite_master
            WHERE type='table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

    return "\n\n".join(
        f"TABLE {name}:\n{sql}"
        for name, sql in rows
    )


def execute_readonly(sql):
    sql = sql.strip().rstrip(";")

    if not re.match(r"^(SELECT|WITH)\b", sql, re.I):
        raise ValueError("Only SELECT/WITH queries are allowed.")

    forbidden = r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|REPLACE|VACUUM)\b"

    if re.search(forbidden, sql, re.I):
        raise ValueError("Potentially unsafe SQL detected.")

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn)


def generate_sql(question, schema):

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing in .env file.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
You are an expert SQLite SQL generator.

Your task is to convert the user's natural-language question
into a valid SQLite SQL query.

DATABASE SCHEMA:
{schema}

USER QUESTION:
{question}

RULES:
1. Use only the tables and columns provided in the schema.
2. Generate SQLite-compatible SQL only.
3. Generate only read-only SELECT or WITH queries.
4. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
   PRAGMA, ATTACH, DETACH, REPLACE, or VACUUM.
5. Do not invent tables or columns.
6. Use JOINs when data from multiple tables is required.
7. Use appropriate aggregations such as SUM, COUNT, AVG, MIN,
   and MAX when needed.
8. If the question cannot be answered using the available schema,
   return:
   SELECT 'Unable to answer from the available database schema.' AS message;
9. Return ONLY the SQL query.
10. Do not include markdown, explanations, comments, or SQL fences.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    return (
        response.text
        .strip()
        .replace("```sql", "")
        .replace("```", "")
        .strip()
    )


def explain_result(question, sql, df):

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing in .env file.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    preview = df.head(20).to_csv(index=False)

    prompt = f"""
Explain the SQL result to a non-technical user.

Question:
{question}

SQL:
{sql}

Result preview:
{preview}

Give a concise explanation:
1. What the query found.
2. The important numbers or patterns.
3. Any useful caveat if the result is empty or limited.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    return response.text.strip()


def init_db():

    if os.path.exists(DB_PATH):
        return

    with sqlite3.connect(DB_PATH) as conn:

        conn.executescript("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT,
            signup_date TEXT
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date TEXT,
            product TEXT,
            quantity INTEGER,
            unit_price REAL,
            FOREIGN KEY(customer_id)
                REFERENCES customers(customer_id)
        );

        INSERT INTO customers VALUES
        (1,'Arun','Chennai','2025-01-10'),
        (2,'Priya','Coimbatore','2025-02-15'),
        (3,'Kumar','Madurai','2025-03-20'),
        (4,'Divya','Trichy','2025-04-12'),
        (5,'Rahul','Chennai','2025-05-08');

        INSERT INTO orders VALUES
        (101,1,'2026-01-05','Laptop Stand',2,1200),
        (102,1,'2026-01-18','Keyboard',1,1800),
        (103,2,'2026-02-02','Mouse',3,700),
        (104,2,'2026-02-20','Monitor',1,15000),
        (105,3,'2026-03-01','Keyboard',2,1800),
        (106,3,'2026-03-11','Mouse',2,700),
        (107,4,'2026-03-18','Monitor',2,15000),
        (108,5,'2026-04-01','Laptop Stand',1,1200),
        (109,5,'2026-04-08','Keyboard',2,1800);
        """)


init_db()


st.title("🤖 AI SQL Agent")

st.caption(
    "Natural language → Gemini → SQL → SQLite → Result → AI explanation"
)


with st.sidebar:

    st.header("Database")

    st.code(
        get_schema(),
        language="sql"
    )

    st.info(f"Model: {GEMINI_MODEL}")

    if "history" not in st.session_state:
        st.session_state.history = []


question = st.text_area(
    "Ask a question about the sales database",
    placeholder="Example: Which customer spent the most money?",
    height=100,
)


if st.button("🚀 Ask AI", type="primary") and question.strip():

    try:

        schema = get_schema()

        with st.spinner("Generating SQL..."):
            sql = generate_sql(question, schema)

        st.subheader("Generated SQL")

        st.code(
            sql,
            language="sql"
        )

        with st.spinner("Executing query..."):
            df = execute_readonly(sql)

        st.subheader("Query Result")

        st.dataframe(
            df,
            use_container_width=True
        )

        with st.spinner("Generating explanation..."):
            explanation = explain_result(
                question,
                sql,
                df
            )

        st.subheader("🤖 AI Explanation")

        st.write(explanation)

        st.session_state.history.insert(
            0,
            {
                "question": question,
                "sql": sql,
                "rows": len(df),
            }
        )

    except Exception as e:

        st.error(f"Error: {e}")


st.divider()

st.subheader("🕘 Query History")


if not st.session_state.history:

    st.caption("No queries yet.")

else:

    for i, item in enumerate(
        st.session_state.history,
        1
    ):

        with st.expander(
            f"{i}. {item['question']} — {item['rows']} rows"
        ):

            st.code(
                item["sql"],
                language="sql"
            )