Fact-Checking System using PIB Government Data

Project Overview:
This project implements an Automated Fact-Checking System that verifies public claims against official Indian Government data (PIB Press Releases).

Features:
1. Scraping latest PIB press releases
2. Indexing verified facts using FAISS
3. Extracting claims using spaCy
4. Numeric + semantic fact checking
5. Verdict: True, False, Unverifiable
6. Streamlit UI for interactive testing
7. No OpenAI API key required

Setup Instructions:
1. Clone repository and navigate into folder.

2. Create and activate virtual environment:
python -m venv venv
venv\Scripts\activate

3. Install dependencies:
pip install -r requirements.txt

4. Download spaCy model:
python -m spacy download en_core_web_sm
Usage:
Step 1: Scrape PIB data
python -m src.pib_scraper --limit 50
Step 2: Build FAISS index
python -m src.build_index
Step 3: Run Streamlit app
streamlit run app/streamlit_app.py

Example Claims:

1. "NBA released 39.84 crore..." → True
2. "NBA released 390.84 crore..." → False
3. "Govt will give 50,000 to all citizens." → Unverifiable

Limitations:- Only PIB data supported- No generative reasoning
