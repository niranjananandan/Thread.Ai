<div align="center">
  
# 🧵 THREAD.AI
**Smart Textile Intelligence & AI Assistant**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-latest-green.svg)](https://flask.palletsprojects.com/)
[![Gemini AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An advanced, AI-powered conversational agent tailored exclusively for the textile, fashion, and garment industry. THREAD.AI empowers users to manage inventory, query complex datasets, and get instant, domain-specific insights using Google's state-of-the-art Gemini LLM.

</div>

---

## ✨ Features

- 🤖 **Domain-Specific AI:** Fine-tuned prompts ensure the assistant exclusively handles textile-related inquiries, refusing out-of-domain questions to maintain professional focus.
- 📊 **Dynamic Dataset Analysis:** Upload CSV files containing fabric inventory, sales data, or supply chain metrics. The AI parses the data dynamically using `pandas` and provides intelligent, contextual answers.
- 🔐 **Secure Google Authentication:** Seamless and secure user login utilizing the latest Google Identity Services (GIS) One-Tap architecture.
- 💾 **Persistent Chat History:** Seamlessly picks up where you left off. All chat sessions are securely stored in a local SQLite database and tied to the user's authenticated Google ID.
- 📱 **Modern & Responsive UI:** A beautifully crafted interface heavily inspired by industry-leading chat applications. Features a fully responsive mobile-first design, interactive sidebars, and a persistent Light/Dark mode toggle.
- 🛡️ **Admin Dashboard:** Built-in administrative portal to monitor system analytics, track user registrations, and oversee total active chat sessions across the platform.

---

## 🛠️ Tech Stack

**Frontend:**
- HTML5, CSS3, Vanilla JavaScript
- Google Identity Services (OAuth)
- PapaParse (Client-side CSV validation)
- Marked.js (Markdown rendering)

**Backend:**
- **Python** (Core Logic)
- **Flask** (Web Framework)
- **SQLite3** (Database & Analytics)
- **Pandas** (Data manipulation and CSV ingestion)
- **Google Generative AI SDK** (Gemini 3.6 Flash integration)

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed:
- Python 3.9 or higher
- `pip` (Python package installer)
- A Google Cloud Platform account (for OAuth Credentials)
- A Google AI Studio API Key (for Gemini)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/thread-ai.git
   cd thread-ai
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install flask google-generativeai pandas werkzeug
   ```

4. **Configure API Keys:**
   Open `app.py` and replace the placeholder API key with your actual Google Gemini API Key:
   ```python
   genai.configure(api_key="YOUR_GEMINI_API_KEY_HERE")
   ```
   *(Note: For production, it is highly recommended to migrate this to a `.env` file.)*

5. **Initialize the Database:**
   The SQLite database (`textile.db`) will be created and configured automatically upon running the application for the first time.

### Running the Application

Start the Flask development server:
```bash
python app.py
```

Navigate to `http://127.0.0.1:5000` in your web browser to start using THREAD.AI.

---

## 🛡️ Admin Configuration

To access the Admin Dashboard:
1. Open `app.py`.
2. Locate the `ADMIN_EMAILS` list.
3. Add your Google Account email address to the list:
   ```python
   ADMIN_EMAILS = ['1u24ai024.niranjan@gmail.com', 'admin@example.com']
   ```
4. Log into the application using that email. A distinct "Admin Dashboard" access button will become available in the UI.

---

## 📂 Project Structure

```text
THREAD.AI/
├── app.py                 # Main Flask application and API routes
├── textile.db             # SQLite database (Git-ignored)
├── .gitignore             # Ignored files (API keys, databases, pycache)
├── templates/
│   ├── index.html         # Main Chat UI & Login Overlay
│   └── admin.html         # Administrator Dashboard UI
└── uploads/               # Temporary storage for uploaded CSVs
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/thread-ai/issues).

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🤖 Acknowledgements

The core concepts, industry-specific logic, and continuous fine-tuning of **THREAD.AI** are the original ideas of the author. 

The codebase was actively developed and brought to life through pair programming with **Antigravity**, an advanced AI coding agent.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
<div align="center">
  <i>Created and fine-tuned by NIRANJAN ANANDAN</i>
</div>
