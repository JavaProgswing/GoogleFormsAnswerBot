# Google Forms Answer Bot

Google Forms Answer Bot is a Chrome extension designed to enhance the user experience when filling out Google Forms. By utilizing ChatGPT for text-based answers and Tesseract.js for OCR (image-based question recognition), this tool simplifies the process of answering both text and image-based questions directly within the Google Forms interface.

---

## Features
- **Text-based Answering**: Automatically provides answers to text-based questions using ChatGPT.
- **OCR Support**: Detects text from images in questions using Tesseract.js.
- **Seamless Integration**: Operates directly within Google Forms for a streamlined experience.

---

## Setup Guide

### Prerequisites
- Python (3.8 or later).
- Chrome browser.

### Steps to Set Up the Extension

1. **Install Python Dependencies**:  
   Navigate to the `tools/` directory and install the required Python dependencies:
   ```bash
   pip install -r tools/requirements.txt
   ```

2. **Run the Python Script**:  
   Start the backend process by running the `main.py` script:
   ```bash
   python tools/main.py
   ```
   - Ensure the script continues running in the background.
   - During the first run, you may be prompted to enter google account credentials for accessing ChatGPT services. Follow the on-screen instructions.

3. **Load the Unpacked Extension in Chrome**:  
   - Open Chrome and navigate to `chrome://extensions/`.
   - Enable **Developer Mode** (toggle on the switch in the top-right corner).
   - Click **Load unpacked**.
   - Select the directory containing your extension files (the folder where `manifest.json` is located).
   - The extension should now appear in your list of installed extensions.

---

## Usage
- Open any Google Form at `https://docs.google.com/forms/`.
- The extension will activate automatically, providing answers for text and image-based questions.

---

## Notes
- Ensure that the `tools/main.py` script is running in the background while using the extension.
- Verify that the Tesseract.js library is accessible, as defined in the `web_accessible_resources` section of `manifest.json`.
- Keep Chrome updated for the best performance.

---

This extension combines the power of AI and OCR technology to make filling out Google Forms quicker and more efficient. Enjoy the convenience!
