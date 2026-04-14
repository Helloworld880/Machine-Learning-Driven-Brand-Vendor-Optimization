"""UI page modules (not Streamlit multipage pages).

This project uses a single entrypoint (`app.py`) and imports page renderers from here.
Keeping these modules out of the root `pages/` folder prevents Streamlit from
auto-registering them as separate pages in the app switcher.
"""

