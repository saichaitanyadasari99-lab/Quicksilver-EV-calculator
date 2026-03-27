# QuickSilver EV Calculator

Streamlit app for EV powertrain sizing and analysis (range, motor, battery, thermal, charging, sensitivity, and stakeholder views).

## Project Structure

- `app.py` - main Streamlit app
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules for Python project

## Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- Section navigation is horizontal (`st.radio`) in the UI.
- Payload is coupled into core mass calculations using:
  - rated GVW
  - rated payload
  - operating payload

## Create GitHub Repo and Push

From this folder:

```bash
git init
git add .
git commit -m "Initial QuickSilver EV calculator"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

## Suggested Repo Name

- `quicksilver-ev-calculator`
