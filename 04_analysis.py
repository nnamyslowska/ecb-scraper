# ============================================================
# FILE: 04_analysis.py
# STEP 4 of the ECB Web Scraping Project
#
# WHAT THIS FILE DOES:
# Loads all scraped data, applies regex patterns to find
# mentions of AI, digital finance, and monetary policy,
# creates a final structured dataframe, and produces
# analysis charts.
#
# HOW TO USE:
# Open Jupyter Notebook (run: jupyter notebook) and paste
# each section (separated by # %% comments) into a new cell.
# Or open this file in VS Code which recognizes # %% as cells.
#
# LIBRARIES USED:
# - pandas: for dataframes (structured data tables)
# - re: for regular expressions (text pattern matching)
# - matplotlib: for charts and visualizations
#
# INPUT:  data/ecb_full_text.csv (from Step 2 or 3)
#         data/ecb_articles.csv (from Step 1, as fallback)
# OUTPUT: data/ecb_final_dataset.csv
# ============================================================

# %% [markdown]
# # ECB Communication Analysis
# ## How has ECB communication about AI and digital regulation evolved (2019-2026)?
#
# This notebook analyses scraped ECB documents using regex to track
# mentions of artificial intelligence, digital finance, and monetary policy.

# %%
# ============================================================
# CELL 1: IMPORTS
# ============================================================

import pandas as pd
import re
import os
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime

print("Libraries loaded successfully!")

# %%
# ============================================================
# CELL 2: LOAD THE DATA
# ============================================================

# Try to load the full-text data first (from Selenium or Scrapy)
# Fall back to the articles-only data (from Step 1) if needed

if os.path.exists("data/ecb_full_text.csv"):
    print("Loading full-text data from Selenium (Step 2)...")
    df = pd.read_csv("data/ecb_full_text.csv", encoding="utf-8")
    print(f"Loaded {len(df)} articles with full text")

elif os.path.exists("data/ecb_scrapy_output.csv"):
    print("Loading full-text data from Scrapy (Step 3)...")
    df = pd.read_csv("data/ecb_scrapy_output.csv", encoding="utf-8")
    print(f"Loaded {len(df)} articles with full text")

elif os.path.exists("data/ecb_articles.csv"):
    print("Loading article metadata from Step 1...")
    print("(No full text available — analysis will use titles and descriptions)")
    df = pd.read_csv("data/ecb_articles.csv", encoding="utf-8")
    print(f"Loaded {len(df)} articles")

else:
    print("ERROR: No data files found! Run Steps 1-3 first.")

# Show the first few rows
print(f"\nColumns: {list(df.columns)}")
print(f"Shape: {df.shape}")
df.head()

# %%
# ============================================================
# CELL 3: NORMALIZE DATES
# ============================================================

# The dates may be in different formats depending on the source.
# We normalize everything to YYYY-MM-DD format.

def normalize_date(date_str):
    """
    Converts various date formats to YYYY-MM-DD.
    Handles: "2024-08-30", "Wed, 12 Mar 2025 12:00:00 GMT", etc.
    Returns empty string if parsing fails.
    """
    if pd.isna(date_str) or date_str == "":
        return ""

    date_str = str(date_str).strip()

    # Already in YYYY-MM-DD format?
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str

    # Try common date formats
    formats_to_try = [
        "%Y-%m-%d",                      # 2024-08-30
        "%a, %d %b %Y %H:%M:%S %Z",     # Wed, 12 Mar 2025 12:00:00 GMT
        "%a, %d %b %Y %H:%M:%S %z",     # with timezone offset
        "%d %B %Y",                       # 30 August 2024
        "%d %b %Y",                       # 30 Aug 2024
    ]

    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Last resort: try to extract just the date part with regex
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
    if match:
        return match.group(0)

    return date_str  # return original if nothing works


# Apply the normalization function to the date column
df["date_normalised"] = df["date"].apply(normalize_date)

# Extract year from the normalized date
df["year"] = df["date_normalised"].apply(
    lambda d: int(d[:4]) if len(str(d)) >= 4 and str(d)[:4].isdigit() else 0
)

# Filter to our study period (2019-2026)
df = df[df["year"].between(2019, 2026)]
print(f"Articles in study period (2019-2026): {len(df)}")

# Show date distribution
print("\nArticles per year:")
print(df["year"].value_counts().sort_index())

# %%
# ============================================================
# CELL 4: DEFINE REGEX PATTERNS
# ============================================================

# These regex patterns search for specific topics in the text.
#
# KEY CONCEPT: \b means "word boundary" — it prevents matching
# parts of other words. For example, \bAI\b matches the word
# "AI" but NOT "said", "contain", or "explain".
#
# re.IGNORECASE means the search is case-insensitive:
# "AI" matches "ai", "Ai", "AI"
#
# DEFENSE QUESTION: "What does \b mean in regex?"
# ANSWER: \b is a word boundary anchor. It matches the position
# between a word character and a non-word character. This ensures
# we match whole words only, not parts of other words.

# --- Pattern 1: AI and machine learning mentions ---
RE_AI = re.compile(
    r'\b('
    r'artificial intelligence|machine learning|\bAI\b|'
    r'large language model|\bLLM\b|ChatGPT|generative AI|'
    r'AI Act|neural network|deep learning|automation'
    r')\b',
    re.IGNORECASE
)

# --- Pattern 2: Digital finance mentions ---
RE_DIGITAL = re.compile(
    r'\b('
    r'digital euro|\bCBDC\b|central bank digital currency|'
    r'crypto|blockchain|fintech|digital finance|'
    r'Digital Markets Act|\bDMA\b|digitalisation|digitalization'
    r')\b',
    re.IGNORECASE
)

# --- Pattern 3: Monetary policy mentions ---
RE_MONETARY = re.compile(
    r'\b('
    r'interest rate|key rate|deposit facility|'
    r'quantitative easing|\bQE\b|inflation|price stability|'
    r'monetary policy|basis point|tightening|hiking|cutting'
    r')\b',
    re.IGNORECASE
)

# --- Pattern 4: Extract percentage values ---
RE_RATE_PERCENT = re.compile(
    r'(\d+\.?\d*)\s*(?:%|percent|per cent)',
    re.IGNORECASE
)

# --- Pattern 5: Extract basis points values ---
RE_BASIS_POINTS = re.compile(
    r'(\d+)\s*(?:basis points?|bps)',
    re.IGNORECASE
)

print("Regex patterns defined!")
print("Example: RE_AI matches 'artificial intelligence', 'AI', 'machine learning', etc.")
print("Example: RE_AI does NOT match 'said', 'contain', 'explain' (thanks to \\b)")

# %%
# ============================================================
# CELL 5: APPLY REGEX PATTERNS TO THE DATA
# ============================================================

# Create a single text column that combines title + description + full_text
# This ensures we search across all available text for each article

def build_search_text(row):
    """Combines all text fields into one string for regex searching."""
    parts = []
    for col in ["title", "description", "full_text"]:
        if col in row and pd.notna(row[col]):
            parts.append(str(row[col]))
    return " ".join(parts)

df["search_text"] = df.apply(build_search_text, axis=1)

# --- Apply regex patterns ---

# AI mentions: does the text mention AI topics?
df["has_ai_mention"] = df["search_text"].apply(
    lambda text: bool(RE_AI.search(text))
)

# AI mention count: how many times are AI topics mentioned?
df["ai_mention_count"] = df["search_text"].apply(
    lambda text: len(RE_AI.findall(text))
)

# Digital finance mentions
df["has_digital_mention"] = df["search_text"].apply(
    lambda text: bool(RE_DIGITAL.search(text))
)

df["digital_mention_count"] = df["search_text"].apply(
    lambda text: len(RE_DIGITAL.findall(text))
)

# Monetary policy mentions
df["has_monetary_mention"] = df["search_text"].apply(
    lambda text: bool(RE_MONETARY.search(text))
)

df["monetary_mention_count"] = df["search_text"].apply(
    lambda text: len(RE_MONETARY.findall(text))
)

# Print summary of mentions
print("=== REGEX ANALYSIS RESULTS ===")
print(f"Articles mentioning AI:              {df['has_ai_mention'].sum()} / {len(df)}")
print(f"Articles mentioning digital finance: {df['has_digital_mention'].sum()} / {len(df)}")
print(f"Articles mentioning monetary policy: {df['has_monetary_mention'].sum()} / {len(df)}")

# %%
# ============================================================
# CELL 6: ANALYSIS — AI MENTIONS BY YEAR
# ============================================================

# Group by year and count AI mentions
ai_by_year = df.groupby("year").agg(
    total_articles=("title", "count"),
    ai_articles=("has_ai_mention", "sum"),
    ai_total_mentions=("ai_mention_count", "sum"),
).reset_index()

# Calculate percentage of articles mentioning AI
ai_by_year["ai_percentage"] = (
    ai_by_year["ai_articles"] / ai_by_year["total_articles"] * 100
).round(1)

print("AI Mentions by Year:")
print(ai_by_year.to_string(index=False))

# --- CHART: AI mentions over time ---
fig, ax1 = plt.subplots(figsize=(10, 6))

# Bar chart: number of articles mentioning AI
ax1.bar(ai_by_year["year"], ai_by_year["ai_articles"],
        color="steelblue", alpha=0.7, label="Articles mentioning AI")
ax1.set_xlabel("Year")
ax1.set_ylabel("Number of articles", color="steelblue")
ax1.tick_params(axis="y", labelcolor="steelblue")

# Line chart: percentage on second axis
ax2 = ax1.twinx()
ax2.plot(ai_by_year["year"], ai_by_year["ai_percentage"],
         color="red", marker="o", linewidth=2, label="% of articles")
ax2.set_ylabel("% of articles mentioning AI", color="red")
ax2.tick_params(axis="y", labelcolor="red")

plt.title("AI Mentions in ECB Communications (2019-2026)")
fig.tight_layout()
plt.savefig("data/chart_ai_by_year.png", dpi=150, bbox_inches="tight")
plt.show()
print("Chart saved to data/chart_ai_by_year.png")

# %%
# ============================================================
# CELL 7: ANALYSIS — MENTIONS BY DOCUMENT TYPE
# ============================================================

# Group by document type
by_type = df.groupby("doc_type").agg(
    total=("title", "count"),
    ai_count=("has_ai_mention", "sum"),
    digital_count=("has_digital_mention", "sum"),
    monetary_count=("has_monetary_mention", "sum"),
).reset_index()

print("Mentions by Document Type:")
print(by_type.to_string(index=False))

# --- CHART: Document type comparison ---
fig, ax = plt.subplots(figsize=(10, 6))

x = range(len(by_type))
width = 0.25

ax.bar([i - width for i in x], by_type["ai_count"],
       width, label="AI", color="steelblue")
ax.bar(x, by_type["digital_count"],
       width, label="Digital Finance", color="orange")
ax.bar([i + width for i in x], by_type["monetary_count"],
       width, label="Monetary Policy", color="green")

ax.set_xlabel("Document Type")
ax.set_ylabel("Number of Articles with Mentions")
ax.set_title("Topic Mentions by ECB Document Type")
ax.set_xticks(x)
ax.set_xticklabels(by_type["doc_type"], rotation=45, ha="right")
ax.legend()

fig.tight_layout()
plt.savefig("data/chart_by_doc_type.png", dpi=150, bbox_inches="tight")
plt.show()
print("Chart saved to data/chart_by_doc_type.png")

# %%
# ============================================================
# CELL 8: ANALYSIS — ALL THREE TOPICS OVER TIME
# ============================================================

topics_by_year = df.groupby("year").agg(
    ai=("has_ai_mention", "sum"),
    digital=("has_digital_mention", "sum"),
    monetary=("has_monetary_mention", "sum"),
).reset_index()

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(topics_by_year["year"], topics_by_year["ai"],
        marker="o", label="AI", linewidth=2)
ax.plot(topics_by_year["year"], topics_by_year["digital"],
        marker="s", label="Digital Finance", linewidth=2)
ax.plot(topics_by_year["year"], topics_by_year["monetary"],
        marker="^", label="Monetary Policy", linewidth=2)

ax.set_xlabel("Year")
ax.set_ylabel("Number of Articles")
ax.set_title("Evolution of ECB Communication Topics (2019-2026)")
ax.legend()
ax.grid(True, alpha=0.3)

fig.tight_layout()
plt.savefig("data/chart_topics_over_time.png", dpi=150, bbox_inches="tight")
plt.show()
print("Chart saved to data/chart_topics_over_time.png")

# %%
# ============================================================
# CELL 9: SHOW EXAMPLE AI-MENTIONING ARTICLES
# ============================================================

# Show some example articles that mention AI
ai_articles = df[df["has_ai_mention"] == True].sort_values("date_normalised")

print(f"Found {len(ai_articles)} articles mentioning AI topics\n")
print("First 10 AI-mentioning articles:")
for _, row in ai_articles.head(10).iterrows():
    print(f"  [{row['date_normalised']}] [{row['doc_type']}] {row['title'][:80]}")

# %%
# ============================================================
# CELL 10: CREATE AND SAVE FINAL DATAFRAME
# ============================================================

# Select the columns for the final dataset
final_columns = [
    "doc_type",
    "title",
    "date_normalised",
    "year",
    "link",
    "has_ai_mention",
    "ai_mention_count",
    "has_digital_mention",
    "digital_mention_count",
    "has_monetary_mention",
    "monetary_mention_count",
]

# Add full_text and description if available
if "full_text" in df.columns:
    final_columns.append("full_text")
if "description" in df.columns:
    final_columns.append("description")

# Create the final dataframe
df_final = df[final_columns].copy()

# Sort by date
df_final = df_final.sort_values("date_normalised").reset_index(drop=True)

# Save to CSV
OUTPUT_FILE = "data/ecb_final_dataset.csv"
df_final.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

print(f"Final dataset saved to {OUTPUT_FILE}")
print(f"Shape: {df_final.shape}")
print(f"\nColumns in final dataset:")
for col in df_final.columns:
    print(f"  - {col}")

print(f"\n=== FINAL SUMMARY ===")
print(f"Total articles: {len(df_final)}")
print(f"Date range: {df_final['date_normalised'].min()} to {df_final['date_normalised'].max()}")
print(f"AI mentions: {df_final['has_ai_mention'].sum()}")
print(f"Digital mentions: {df_final['has_digital_mention'].sum()}")
print(f"Monetary mentions: {df_final['has_monetary_mention'].sum()}")

# Show the final dataframe
df_final.head(10)
