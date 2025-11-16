#!/bin/bash

# Resume Generator Frontend Setup Script
# This script sets up a complete React frontend for the Resume Generator

set -e  # Exit on error

echo "🚀 Starting Resume Generator Frontend Setup..."
echo ""

# Step 1: Create React App
echo "📦 Step 1/8: Creating React app..."
npx create-react-app resume-generator-frontend
cd resume-generator-frontend

# Step 2: Install dependencies
echo ""
echo "📚 Step 2/8: Installing dependencies..."
npm install lucide-react

# Step 3: Install Tailwind CSS
echo ""
echo "🎨 Step 3/8: Installing Tailwind CSS..."
npm install -D tailwindcss postcss autoprefixer

# Step 4: Manually create Tailwind config (skip npx command)
echo ""
echo "⚙️  Step 4/8: Creating Tailwind config files..."

cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF

cat > postcss.config.js << 'EOF'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF

echo "✓ Tailwind config files created"

# Step 5: Update index.css with Tailwind directives
echo ""
echo "🎨 Step 5/8: Updating index.css..."
cat > src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
EOF

# Step 6: Create App.css
echo ""
echo "💅 Step 6/8: Creating App.css..."
cat > src/App.css << 'EOF'
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#root {
  width: 100%;
  height: 100vh;
}

/* Custom scrollbar styles */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Smooth transitions */
button {
  transition: all 0.2s ease-in-out;
}

/* Focus states for accessibility */
button:focus-visible,
input:focus-visible,
textarea:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Disable number input spinners */
input[type='number']::-webkit-inner-spin-button,
input[type='number']::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type='number'] {
  -moz-appearance: textfield;
}
EOF

# Step 7: Create App.js with Resume Generator component
echo ""
echo "⚛️  Step 7/8: Creating App.js..."
cat > src/App.js << 'ENDOFFILE'
import React, { useState, useEffect } from 'react';
import { FileText, Settings, X, Copy, Download, Check } from 'lucide-react';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [githubUsername, setGithubUsername] = useState('');
  const [additionalInfo, setAdditionalInfo] = useState('');
  const [priority, setPriority] = useState('experience');
  const [resumeContent, setResumeContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [currentView, setCurrentView] = useState('edit');
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadedResumeText, setUploadedResumeText] = useState(null);
  const [useAsTemplate, setUseAsTemplate] = useState(false);
  const [useAsData, setUseAsData] = useState(true);
  const [showSystemPromptModal, setShowSystemPromptModal] = useState(false);
  const [systemPromptEditor, setSystemPromptEditor] = useState('');
  const [customSystemPrompt, setCustomSystemPrompt] = useState(null);
  const [defaultSystemPrompt, setDefaultSystemPrompt] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadDefaultSystemPrompt();
  }, []);

  const loadDefaultSystemPrompt = async () => {
    try {
      const response = await fetch(`${API_URL}/get-system-prompt`);
      if (!response.ok) throw new Error('Failed to load system prompt');
      const data = await response.json();
      setDefaultSystemPrompt(data.prompt);
      setSystemPromptEditor(data.prompt);
    } catch (err) {
      console.error('Could not load system prompt:', err);
    }
  };

  const showError = (message) => {
    setError(message);
    setTimeout(() => setError(''), 5000);
  };

  const showSuccess = (message) => {
    setSuccess(message);
    setTimeout(() => setSuccess(''), 3000);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/extract-resume`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload resume');
      }

      const data = await response.json();
      setUploadedResumeText(data.text);
      setUploadedFile(file.name);

      if (useAsData) {
        setAdditionalInfo(prev =>
          prev.trim()
            ? `${prev}\n\n--- Extracted from uploaded resume ---\n${data.text}`
            : data.text
        );
      }

      showSuccess('Resume uploaded successfully!');
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveUpload = () => {
    setUploadedFile(null);
    setUploadedResumeText(null);
  };

  const handleGenerate = async () => {
    if (!githubUsername && !additionalInfo) {
      showError('Please provide either a GitHub username or additional information');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const requestBody = {
        github_username: githubUsername || null,
        additional_info: additionalInfo || null,
        priority: priority
      };

      if (customSystemPrompt) {
        requestBody.custom_system_prompt = customSystemPrompt;
      }

      if (uploadedResumeText && useAsTemplate) {
        requestBody.resume_template = uploadedResumeText;
      }

      const response = await fetch(`${API_URL}/generate-resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate resume');
      }

      const data = await response.json();
      setResumeContent(data.resume);
      showSuccess('Resume generated successfully!');
    } catch (err) {
      showError(err.message || 'An error occurred while generating the resume');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(resumeContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      showError('Failed to copy to clipboard');
    }
  };

  const handleDownloadMd = () => {
    const blob = new Blob([resumeContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'resume.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setShowDownloadMenu(false);
  };

  const renderPreview = () => {
    const lines = resumeContent.split('\n');
    return lines.map((line, i) => {
      line = line.trim();
      if (!line) return <br key={i} />;

      if (line.startsWith('# ')) {
        return <h1 key={i} className="text-2xl font-bold mb-2 text-center">{line.substring(2)}</h1>;
      } else if (line.startsWith('## ')) {
        return <h2 key={i} className="text-xl font-bold mt-4 mb-2 border-b-2 border-gray-800">{line.substring(3)}</h2>;
      } else if (line.startsWith('### ')) {
        return <h3 key={i} className="text-lg font-bold mt-3 mb-1">{line.substring(4)}</h3>;
      } else if (line.startsWith('- ') || line.startsWith('* ')) {
        return <li key={i} className="ml-5">{line.substring(2)}</li>;
      } else {
        return <p key={i} className="mb-2">{line}</p>;
      }
    });
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {success && (
        <div className="fixed top-4 right-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg shadow-lg z-50">
          {success}
        </div>
      )}

      {showSystemPromptModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col m-4">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Edit System Prompt</h2>
              <button onClick={() => setShowSystemPromptModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <p className="text-sm text-gray-600 mb-4">
                Customize the system prompt to change how the AI formats your resume.
              </p>
              <textarea
                value={systemPromptEditor}
                onChange={(e) => setSystemPromptEditor(e.target.value)}
                className="w-full h-96 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
              />
            </div>
            <div className="p-6 border-t border-gray-200 flex justify-between">
              <button
                onClick={() => {
                  setCustomSystemPrompt(null);
                  setSystemPromptEditor(defaultSystemPrompt);
                  showSuccess('System prompt reset to default');
                }}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition text-sm font-medium"
              >
                Reset to Default
              </button>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowSystemPromptModal(false)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    setCustomSystemPrompt(systemPromptEditor.trim());
                    setShowSystemPromptModal(false);
                    showSuccess('System prompt updated!');
                  }}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="w-1/2 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-2xl font-bold text-gray-900">Resume Generator</h1>
            <button
              onClick={() => {
                setSystemPromptEditor(customSystemPrompt || defaultSystemPrompt);
                setShowSystemPromptModal(true);
              }}
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-xs font-medium flex items-center gap-1"
            >
              <Settings className="w-3 h-3" />
              Edit Prompt
            </button>
          </div>
          <p className="text-sm text-gray-600">Generate ATS-friendly resumes from your GitHub profile</p>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">GitHub Username</label>
            <input
              type="text"
              value={githubUsername}
              onChange={(e) => setGithubUsername(e.target.value)}
              placeholder="e.g., octocat"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
            <p className="mt-1.5 text-xs text-gray-500">We'll fetch your README to extract relevant information</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Upload Old Resume (Optional)</label>
            <input
              type="file"
              onChange={handleFileUpload}
              accept=".pdf,.docx,.txt,.md"
              className="hidden"
              id="resumeUpload"
            />
            <label
              htmlFor="resumeUpload"
              className="w-full px-4 py-2.5 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition text-gray-600 text-sm font-medium flex items-center justify-center gap-2 cursor-pointer"
            >
              <FileText className="w-4 h-4" />
              Click to upload resume
            </label>
            {uploadedFile && (
              <div className="mt-2 text-xs text-green-600 flex items-center gap-2">
                <Check className="w-4 h-4" />
                <span>{uploadedFile}</span>
                <button onClick={handleRemoveUpload} className="text-red-600 hover:text-red-700 ml-auto">Remove</button>
              </div>
            )}
            <div className="mt-2 space-y-1">
              <label className="flex items-center text-xs text-gray-600">
                <input type="checkbox" checked={useAsTemplate} onChange={(e) => setUseAsTemplate(e.target.checked)} className="mr-2" />
                Use as template structure
              </label>
              <label className="flex items-center text-xs text-gray-600">
                <input type="checkbox" checked={useAsData} onChange={(e) => setUseAsData(e.target.checked)} className="mr-2" />
                Extract data from resume
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">Resume Focus</label>
            <div className="grid grid-cols-2 gap-3">
              <div
                onClick={() => setPriority('experience')}
                className={`border-2 rounded-lg p-4 cursor-pointer transition hover:-translate-y-0.5 ${
                  priority === 'experience' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-start gap-3">
                  <input type="radio" checked={priority === 'experience'} onChange={() => setPriority('experience')} className="mt-1" />
                  <div>
                    <div className="font-semibold text-gray-900 mb-1">Experience First</div>
                    <div className="text-xs text-gray-600">Emphasize work history</div>
                  </div>
                </div>
              </div>
              <div
                onClick={() => setPriority('projects')}
                className={`border-2 rounded-lg p-4 cursor-pointer transition hover:-translate-y-0.5 ${
                  priority === 'projects' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                }`}
              >
                <div className="flex items-start gap-3">
                  <input type="radio" checked={priority === 'projects'} onChange={() => setPriority('projects')} className="mt-1" />
                  <div>
                    <div className="font-semibold text-gray-900 mb-1">Projects First</div>
                    <div className="text-xs text-gray-600">Highlight technical projects</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Additional Information</label>
            <textarea
              value={additionalInfo}
              onChange={(e) => setAdditionalInfo(e.target.value)}
              rows={8}
              placeholder="Add details like contact info, experience, education, skills..."
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none font-mono text-sm"
            />
          </div>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-3 px-4 rounded-lg transition"
          >
            {loading ? 'Generating...' : 'Generate Resume'}
          </button>
        </div>
      </div>

      <div className="w-1/2 bg-gray-50 flex flex-col">
        <div className="p-6 border-b border-gray-200 bg-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-gray-900">Resume</h2>
            {resumeContent && (
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setCurrentView('edit')}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition ${
                    currentView === 'edit' ? 'bg-white shadow-sm' : 'text-gray-600'
                  }`}
                >
                  Edit
                </button>
                <button
                  onClick={() => setCurrentView('preview')}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition ${
                    currentView === 'preview' ? 'bg-white shadow-sm' : 'text-gray-600'
                  }`}
                >
                  Preview
                </button>
              </div>
            )}
          </div>
          {resumeContent && (
            <div className="flex gap-2">
              <button
                onClick={handleCopy}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium flex items-center gap-2"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
              <div className="relative">
                <button
                  onClick={() => setShowDownloadMenu(!showDownloadMenu)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
                {showDownloadMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
                    <button onClick={handleDownloadMd} className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 rounded-lg">
                      Download as Markdown
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {!resumeContent ? (
            <div className="h-full flex items-center justify-center text-gray-400">
              <div className="text-center">
                <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">No resume generated yet</p>
                <p className="text-sm mt-2">Fill in your information and click "Generate Resume"</p>
              </div>
            </div>
          ) : currentView === 'edit' ? (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
              <textarea
                value={resumeContent}
                onChange={(e) => setResumeContent(e.target.value)}
                className="w-full h-full min-h-[600px] p-6 font-mono text-sm text-gray-800 leading-relaxed resize-none focus:outline-none"
              />
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-8">
              <div className="font-serif leading-relaxed">{renderPreview()}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
ENDOFFILE

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Make sure your backend is running on http://localhost:8000"
echo "   2. Start the development server:"
echo "      cd resume-generator-frontend"
echo "      npm start"
echo ""
echo "🌐 The app will open at http://localhost:3000"
echo ""
echo "🎉 Happy coding!"