# Automata Studio — DFA / NFA String Processing Visualizer

A Streamlit application for defining finite automata, visualizing state diagrams, and tracing string processing.

## Features
- DFA, NFA and ε-NFA modes
- Editable transition table
- Start and accepting state selection
- State diagram with start/final/active-state styling
- String acceptance/rejection
- Step-by-step computation trace
- Highlighted computation path
- Built-in example machines
- Downloadable trace as CSV

## Run locally
```bash
python -m pip install -r requirements.txt
streamlit run app.py
```
Open the local URL shown in the terminal (usually http://localhost:8501).

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository and upload `app.py`, `requirements.txt`, and `README.md`.
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Select the repository, branch (`main`), and main file path (`app.py`).
4. Click Deploy.

## Notes
- Alphabet symbols are single characters.
- DFA transitions must have exactly one destination for every state and alphabet symbol.
- NFA and ε-NFA cells can contain multiple destinations separated by commas.
- In ε-NFA mode, `ε` is handled as a transition label, not as an input character.
