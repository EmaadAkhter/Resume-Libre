<div align="center">

# 🗂️ Resume-Libre

**AI-powered resume generator that transforms your GitHub profile & experience into an ATS-ready, one-page resume — in seconds.**

[![Backend](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge&logo=render)](https://resume-libre.onrender.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Made with React](https://img.shields.io/badge/Made%20with-React%2019-61DAFB?style=for-the-badge&logo=react)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)


</div>

---

## ✨ What is Resume-Libre?

Resume-Libre is a full-stack application that reads your **GitHub profile README**, combines it with any extra information you provide, and uses a large language model to produce a polished, **ATS-friendly one-page resume** — formatted in Markdown with live preview, editable output, and export to PDF, DOCX, or Markdown.

No templates to fight. No forms to fill for 20 minutes. Just paste your GitHub username and go.

---

## 🚀 Features

| Feature | Details |
|---|---|
| 🤖 **AI Generation** | Powered by multiple LLMs via OpenRouter with automatic key rotation |
| 🐙 **GitHub Integration** | Fetches your profile README via MCP (Model Context Protocol) |
| 📄 **Resume Upload** | Extracts text from existing PDF/DOCX/TXT resumes as context or template |
| 🎯 **Focus Modes** | Experience-first or Projects-first section ordering |
| ✏️ **Live Editor** | Edit the raw Markdown in-browser after generation |
| 👁️ **Preview Mode** | Toggle between Markdown source and rendered preview |
| 📤 **Export** | Download as **PDF**, **DOCX**, or **Markdown** |
| 🛠️ **Custom System Prompt** | Override the AI's instructions for full formatting control |
| 📱 **Responsive UI** | Full mobile layout with dedicated form/resume views |
| ⚡ **ATS Validated** | Output is checked for HTML tags, icon codes, and generic filler text |

---

## 🏗️ Architecture

```
resume-libre/
├── resume-generator-frontend/   # React 19 + Tailwind CSS
│   └── src/
│       └── App.js               # Single-page app — form, editor, preview
│
├── resume_generator_backend/    # FastAPI (Python)
│   ├── main.py                  # API routes
│   ├── Utils/
│   │   ├── fetch_readme.py      # GitHub README via MCP client
│   │   ├── prompt.py            # Prompt construction + contact extraction
│   │   ├── genrate_resume.py    # OpenRouter LLM call with key rotation
│   │   ├── clean_up.py          # Markdown validation + quality checks
│   │   └── export_utils.py      # PDF (ReportLab) + DOCX (python-docx) export
│   ├── system_promt.txt         # Master LLM system prompt
│   └── template.md              # Resume section template for the prompt
│
└── MCP_SERVER/
    └── MCP.py                   # FastMCP server — GitHub README fetcher
```

**Data flow:**

```
GitHub Username ──► MCP Server ──► GitHub API ──► README text
                                                        │
Additional Info ──────────────────────────────────► Prompt Builder
                                                        │
Uploaded Resume ──────────────────────────────────►     │
                                                        ▼
                                               OpenRouter LLM
                                                        │
                                                        ▼
                                         Validated Markdown Resume
                                                        │
                              ┌─────────────────────────┤
                              ▼                         ▼
                          PDF Export              DOCX Export
```

---

## 🛠️ Tech Stack

### Frontend
- **React 19** — UI framework
- **Tailwind CSS 3** — Utility-first styling
- **lucide-react** — Icon set
- **Create React App** — Build tooling

### Backend
- **FastAPI** — Async Python web framework
- **OpenRouter** — Multi-model LLM API (with 6-key rotation)
- **FastMCP** — MCP client for GitHub README fetching
- **ReportLab** — PDF generation
- **python-docx** — DOCX generation
- **pypdf** — PDF text extraction
- **python-dotenv** — Environment config

### Infrastructure
- **Vercel** — Frontend hosting
- **Render** — Backend hosting

---

## ⚙️ Local Development

### Prerequisites

- Node.js 18+
- Python 3.10+
- An [OpenRouter](https://openrouter.ai) API key
- (Optional) A hosted FastMCP server for GitHub fetching

### 1. Clone the repo

```bash
git clone https://github.com/EmaadAkhter/resume-libre.git
cd resume-libre
```

### 2. Backend setup

```bash
cd resume_generator_backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in `resume_generator_backend/`:

```env
# OpenRouter API Keys (at least one required)
O_R_API1=sk-or-...
O_R_API2=sk-or-...   # optional, enables rotation

# Models to use (at least one required)
MODEL1=google/gemini-flash-1.5
MODEL2=anthropic/claude-3-haiku
MODEL3=meta-llama/llama-3.1-8b-instruct

# MCP Server (for GitHub README fetching)
MCP_API=your-mcp-bearer-token
MCP_URL=https://your-mcp-server.com/mcp
```

Start the backend:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs → [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. MCP Server setup (optional — enables GitHub fetching)

```bash
cd MCP_SERVER
pip install fastmcp requests
python MCP.py
```

This exposes a `get_github_readme(user_name)` tool that the backend calls via MCP.

### 4. Frontend setup

```bash
cd resume-generator-frontend
npm install
```

Update the API URL in `src/App.js`:

```js
const API_URL = 'http://localhost:8000';   // for local dev
```

Start the dev server:

```bash
npm start
```

App → [http://localhost:3000](http://localhost:3000)

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/get-system-prompt` | Fetch the current LLM system prompt |
| `POST` | `/generate-resume` | Generate a resume from inputs |
| `POST` | `/export-resume` | Export Markdown to PDF / DOCX / MD |
| `POST` | `/extract-resume` | Extract text from an uploaded file |

### `POST /generate-resume`

```json
{
  "github_username": "octocat",
  "additional_info": "Senior engineer at Acme Corp. Email: hi@example.com",
  "priority": "experience",
  "custom_system_prompt": null,
  "resume_template": null
}
```

**Response:**
```json
{
  "resume": "# John Doe\n[hi@example.com](...) | ...",
  "status": "success"
}
```

### `POST /export-resume`

```json
{
  "markdown_content": "# John Doe\n...",
  "format": "pdf"
}
```

Returns a binary file download (`application/pdf`, `.docx`, or `text/markdown`).

---

## 🧠 How the AI Works

The system prompt (`system_promt.txt`) enforces strict output rules:

- **No HTML** — only standard Markdown elements
- **No icon codes** — no Iconify or emoji shortcodes
- **Clickable hyperlinks** — all URLs wrapped in `[text](url)` format
- **Concrete achievements** — no buzzwords like "passionate" or "team player"
- **35–40 line cap** — enforced for one-page fit
- **ATS-safe formatting** — pipe separators, clean headers, no tables

Output is validated by `clean_up.py` which strips leftover fences, normalises whitespace, and rejects resumes with critical issues before they reach the user.

---

## 🔑 LLM Key Rotation

The backend supports up to **6 concurrent OpenRouter API keys** (`O_R_API1` → `O_R_API6`) and **6 model slots** (`MODEL1` → `MODEL6`). Each generation call picks a random key and model, distributing rate-limit pressure across accounts.

---

## 📁 Project Structure (detailed)

```
resume_generator_backend/
├── main.py                   # FastAPI app + all route handlers
├── system_promt.txt          # Master system prompt for the LLM
├── template.md               # Section layout injected into the user prompt
├── requirements.txt
└── Utils/
    ├── clean_up.py           # Markdown sanitisation + quality validation
    ├── export_utils.py       # ReportLab PDF + python-docx DOCX generators
    ├── fetch_readme.py       # Async MCP client → GitHub README
    ├── genrate_resume.py     # OpenRouter call with key/model rotation
    └── prompt.py             # Contact extraction + full prompt assembly

resume-generator-frontend/
├── public/
├── src/
│   ├── App.js                # Entire React app (form, editor, preview, export)
│   ├── App.css               # Global styles + scrollbar overrides
│   ├── index.js
│   └── index.css             # Tailwind directives
├── tailwind.config.js
└── package.json

MCP_SERVER/
├── MCP.py                    # FastMCP server exposing get_github_readme tool
└── requirements.txt
```

---

## 🤝 Contributing

Contributions are welcome! Here are some areas that could use improvement:

- [ ] Add more export formats (plain text, LaTeX)
- [ ] LinkedIn profile URL scraping
- [ ] Resume scoring / ATS keyword analysis
- [ ] Multi-page resume support
- [ ] Dark mode
- [ ] Unit tests for backend utilities
- [ ] Rate limiting & abuse protection

To contribute:

```bash
# Fork & clone
git checkout -b feature/your-feature
# make your changes
git commit -m "feat: your feature description"
git push origin feature/your-feature
# open a PR
```

---

## 📝 License

MIT — see [LICENSE](LICENSE) for details. Use it, fork it, ship it.

---

<div align="center">

Built by [Emaad Ansari](https://github.com/emaadansari) · Powered by OpenRouter 

**If this saved you an hour of resume formatting, drop a ⭐**

</div>
