import streamlit as st
import requests
import json

# Streamlit app title
st.title("🚀 Risk Assessment File Upload")

# Description
st.write("Upload a CSV or text file to assess transaction risks using the `/entity/assessment` endpoint.")

# File uploader
uploaded_file = st.file_uploader("Choose a file", type=["csv", "txt"])

# Button to trigger the upload
if st.button("Upload and Assess"):
    if uploaded_file is not None:
        # Display a loading spinner
        with st.spinner("Processing..."):
            try:
                # Prepare the file for upload
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}

                # Call the FastAPI endpoint
                response = requests.post("http://127.0.0.1:8000/entity/assessment", files=files)

                # Check if the response is successful
                if response.status_code == 200:
                    # Parse and display the JSON response
                    result = response.json()
                    st.success("File processed successfully!")
                    st.json(result)
                else:
                    # Display an error message
                    st.error(f"Error: {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please upload a file before clicking the button.")