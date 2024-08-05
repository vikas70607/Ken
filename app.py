import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json


st.set_page_config(page_title='Image Review',layout="wide")

st.markdown(
    """
<style>
button {
    height: auto;
    padding-top: 10px !important;
    padding-bottom: 10px !important;
    width = 100px;
}
</style>
""",
    unsafe_allow_html=True,
)

def connect_to_google_sheets(sheet_name):
    # Load credentials from Streamlit secrets
    creds_dict = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"],
        "universe_domain": st.secrets["universe_domain"]
    }

    # Set the scope and authorize the credentials
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet

# Example usage
sheet = connect_to_google_sheets("Your Google Sheet Name")


# Function to get the next active row
def get_next_active_row(sheet, current_row):
    records = sheet.get_all_records(head=2)  # Read data starting from row 2
    for idx, record in enumerate(records, start=3):
        if record['image_generated'] == 'yes' and not record['image_approved'] and not record['all_rejected']:
            return idx
    return None

# Function to display data and handle user interaction
def display_row_data(sheet, row):
    data = sheet.row_values(row)
    prompt = data[0]
    image_urls = data[1:5]

    st.header(f"Active Row Number: {row}")
    st.subheader(f"Supposed to look like a {prompt}")

    # Create two columns
    cols = st.columns([3, 1])  # Adjust the width ratio if needed
    with cols[0]:  # Column for images
        cols2 = st.columns(2)
        for i, url in enumerate(image_urls):
            with cols2[i % 2]:
                st.image(url, use_column_width='auto')
                if st.button(f"Option {i + 1}", key=f"option_{i + 1}"):
                    review_notes = st.session_state.get("review_notes", "")
                    sheet.update_cell(row, 9, review_notes)
                    sheet.update_cell(row, 7, f'image_url_{i + 1}')
                    st.session_state.active_row = get_next_active_row(sheet, row)
                    if st.session_state.active_row is None:
                        st.session_state.no_records = True
                    st.rerun()

    with cols[1]:  # Column for review notes and reject button
        st.text_area("Review Notes", key="review_notes", placeholder="Write review notes", height=500)
        if st.button("Reject All"):
            review_notes = st.session_state.get("review_notes", "")
            sheet.update_cell(row, 8, "REJECTED")
            sheet.update_cell(row, 9, review_notes)
            st.session_state.active_row = get_next_active_row(sheet, row)
            if st.session_state.active_row is None:
                st.session_state.no_records = True
            st.rerun()

def main():
    st.title("Image Review App")
    sheet_name = 'Ken'
    sheet = connect_to_google_sheets(sheet_name)

    # Initialize session state if not already set
    if 'active_row' not in st.session_state:
        st.session_state.active_row = get_next_active_row(sheet, 2)  # Start from row 3
        st.session_state.no_records = False

    if st.session_state.no_records:
        st.subheader("No records left to review.")
    else:
        display_row_data(sheet, st.session_state.active_row)

if __name__ == "__main__":
    main()
