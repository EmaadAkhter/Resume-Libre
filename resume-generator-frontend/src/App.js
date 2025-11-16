import React, { useState, useEffect } from 'react';
import { FileText, Settings, X, Copy, Download, Check, AlertCircle, Menu, ChevronLeft } from 'lucide-react';
import './App.css';

// Configure API URL - change this for production
const API_URL ='https://resume-libre.onrender.com';

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
  const [backendStatus, setBackendStatus] = useState('checking');
  const [exporting, setExporting] = useState(false);
  const [mobileView, setMobileView] = useState('form'); // 'form' or 'resume'
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    checkBackendHealth();
    loadDefaultSystemPrompt();

    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      if (response.ok) {
        setBackendStatus('connected');
      } else {
        setBackendStatus('error');
      }
    } catch (err) {
      console.error('Backend health check failed:', err);
      setBackendStatus('disconnected');
      showError('Cannot connect to backend server. Make sure it\'s running on port 8000.');
    }
  };

  const loadDefaultSystemPrompt = async () => {
    try {
      const response = await fetch(`${API_URL}/get-system-prompt`);
      if (!response.ok) throw new Error('Failed to load system prompt');
      const data = await response.json();
      setDefaultSystemPrompt(data.prompt);
      setSystemPromptEditor(data.prompt);
    } catch (err) {
      console.error('Could not load system prompt:', err);
      const fallbackPrompt = 'You are a professional resume writer. Create an ATS-friendly, one-page resume in markdown format.';
      setDefaultSystemPrompt(fallbackPrompt);
      setSystemPromptEditor(fallbackPrompt);
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

    if (backendStatus !== 'connected') {
      showError('Backend server is not connected. Please start the server first.');
      return;
    }

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
    if (useAsData && uploadedResumeText) {
      setAdditionalInfo(prev =>
        prev.replace(`\n\n--- Extracted from uploaded resume ---\n${uploadedResumeText}`, '')
           .replace(uploadedResumeText, '')
           .trim()
      );
    }
  };

  const handleGenerate = async () => {
    if (!githubUsername && !additionalInfo) {
      showError('Please provide either a GitHub username or additional information');
      return;
    }

    if (backendStatus !== 'connected') {
      showError('Backend server is not connected. Please start the server first.');
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
      setCurrentView('preview');
      if (isMobile) {
        setMobileView('resume');
      }
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

  const handleExport = async (format) => {
    if (!resumeContent) {
      showError('No resume to export');
      return;
    }

    if (backendStatus !== 'connected') {
      showError('Backend server is not connected.');
      return;
    }

    try {
      setExporting(true);
      setShowDownloadMenu(false);

      const response = await fetch(`${API_URL}/export-resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          markdown_content: resumeContent,
          format: format
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to export resume');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      const extension = format === 'pdf' ? 'pdf' : format === 'docx' ? 'docx' : 'md';
      a.download = `resume.${extension}`;

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      showSuccess(`Resume exported as ${format.toUpperCase()} successfully!`);
    } catch (err) {
      showError(err.message || 'Failed to export resume');
    } finally {
      setExporting(false);
    }
  };

  const handleDownloadMd = () => {
    handleExport('md');
  };

  const handleDownloadPdf = () => {
    handleExport('pdf');
  };

  const handleDownloadDocx = () => {
    handleExport('docx');
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
        const content = line.substring(2);
        const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
        const parts = [];
        let lastIndex = 0;
        let match;

        while ((match = linkRegex.exec(content)) !== null) {
          if (match.index > lastIndex) {
            parts.push(content.substring(lastIndex, match.index));
          }
          parts.push(<a key={match.index} href={match[2]} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">{match[1]}</a>);
          lastIndex = match.index + match[0].length;
        }

        if (lastIndex < content.length) {
          parts.push(content.substring(lastIndex));
        }

        return <li key={i} className="ml-5">{parts.length > 0 ? parts : content}</li>;
      } else {
        const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
        const parts = [];
        let lastIndex = 0;
        let match;

        while ((match = linkRegex.exec(line)) !== null) {
          if (match.index > lastIndex) {
            parts.push(line.substring(lastIndex, match.index));
          }
          parts.push(<a key={match.index} href={match[2]} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">{match[1]}</a>);
          lastIndex = match.index + match[0].length;
        }

        if (lastIndex < line.length) {
          parts.push(line.substring(lastIndex));
        }

        return <p key={i} className="mb-2">{parts.length > 0 ? parts : line}</p>;
      }
    });
  };

  // Mobile Layout
  if (isMobile) {
    return (
      <div className="flex flex-col h-screen bg-gray-50">
        {success && (
          <div className="fixed top-4 right-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2">
            <Check className="w-5 h-5" />
            {success}
          </div>
        )}

        {backendStatus !== 'connected' && (
          <div className="fixed top-4 left-4 right-4 bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            {backendStatus === 'checking' ? 'Checking...' : 'Backend disconnected'}
          </div>
        )}

        {showSystemPromptModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-end z-50">
            <div className="bg-white rounded-t-lg shadow-xl w-full max-h-[90vh] flex flex-col">
              <div className="p-4 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white">
                <h2 className="text-lg font-semibold text-gray-900">Edit System Prompt</h2>
                <button onClick={() => setShowSystemPromptModal(false)} className="text-gray-400 hover:text-gray-600">
                  <X className="w-6 h-6" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-4">
                <p className="text-sm text-gray-600 mb-4">
                  Customize the system prompt to change how the AI formats your resume.
                </p>
                <textarea
                  value={systemPromptEditor}
                  onChange={(e) => setSystemPromptEditor(e.target.value)}
                  className="w-full h-64 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
                />
              </div>
              <div className="p-4 border-t border-gray-200 flex flex-col gap-2 sticky bottom-0 bg-white">
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
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowSystemPromptModal(false)}
                    className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition text-sm font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      setCustomSystemPrompt(systemPromptEditor.trim());
                      setShowSystemPromptModal(false);
                      showSuccess('System prompt updated!');
                    }}
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium"
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {mobileView === 'form' ? (
          // Form View
          <div className="flex flex-col h-screen overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-white sticky top-0 z-10">
              <div className="flex items-center justify-between mb-1">
                <h1 className="text-xl font-bold text-gray-900">Resume Generator</h1>
                <button
                  onClick={() => {
                    setSystemPromptEditor(customSystemPrompt || defaultSystemPrompt);
                    setShowSystemPromptModal(true);
                  }}
                  className="px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-medium flex items-center gap-1"
                >
                  <Settings className="w-3 h-3" />
                </button>
              </div>
              <p className="text-xs text-gray-600">Generate ATS-friendly resumes</p>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">GitHub Username</label>
                <input
                  type="text"
                  value={githubUsername}
                  onChange={(e) => setGithubUsername(e.target.value)}
                  placeholder="e.g., octocat"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                />
                <p className="mt-1 text-xs text-gray-500">We'll fetch your README</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Upload Resume (Optional)</label>
                <input
                  type="file"
                  onChange={handleFileUpload}
                  accept=".pdf,.docx,.txt,.md"
                  className="hidden"
                  id="resumeUpload"
                  disabled={loading}
                />
                <label
                  htmlFor="resumeUpload"
                  className={`w-full px-3 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition text-gray-600 text-sm font-medium flex items-center justify-center gap-2 ${loading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
                >
                  <FileText className="w-4 h-4" />
                  {loading ? 'Uploading...' : 'Upload'}
                </label>
                {uploadedFile && (
                  <div className="mt-2 text-xs text-green-600 flex items-center gap-2">
                    <Check className="w-4 h-4" />
                    <span>{uploadedFile}</span>
                    <button onClick={handleRemoveUpload} className="text-red-600 hover:text-red-700 ml-auto">Remove</button>
                  </div>
                )}
                <div className="mt-2 space-y-2">
                  <label className="flex items-center text-xs text-gray-600">
                    <input type="checkbox" checked={useAsTemplate} onChange={(e) => setUseAsTemplate(e.target.checked)} className="mr-2" />
                    Use as template
                  </label>
                  <label className="flex items-center text-xs text-gray-600">
                    <input type="checkbox" checked={useAsData} onChange={(e) => setUseAsData(e.target.checked)} className="mr-2" />
                    Extract data
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Resume Focus</label>
                <div className="space-y-2">
                  <div
                    onClick={() => setPriority('experience')}
                    className={`border-2 rounded-lg p-3 cursor-pointer transition ${
                      priority === 'experience' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <input type="radio" checked={priority === 'experience'} onChange={() => setPriority('experience')} className="mt-1" />
                      <div>
                        <div className="font-semibold text-gray-900 text-sm">Experience First</div>
                        <div className="text-xs text-gray-600">Emphasize work history</div>
                      </div>
                    </div>
                  </div>
                  <div
                    onClick={() => setPriority('projects')}
                    className={`border-2 rounded-lg p-3 cursor-pointer transition ${
                      priority === 'projects' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <input type="radio" checked={priority === 'projects'} onChange={() => setPriority('projects')} className="mt-1" />
                      <div>
                        <div className="font-semibold text-gray-900 text-sm">Projects First</div>
                        <div className="text-xs text-gray-600">Highlight projects</div>
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
                  rows={6}
                  placeholder="Add details like contact info, experience, education, skills..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none font-mono text-sm"
                />
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-gray-200 bg-white sticky bottom-0">
              <button
                onClick={handleGenerate}
                disabled={loading || backendStatus !== 'connected'}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition"
              >
                {loading ? 'Generating...' : 'Generate Resume'}
              </button>
            </div>
          </div>
        ) : (
          // Resume View
          <div className="flex flex-col h-screen overflow-hidden">
            <div className="p-4 border-b border-gray-200 bg-white sticky top-0 z-10 flex items-center justify-between">
              <button
                onClick={() => setMobileView('form')}
                className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium text-sm"
              >
                <ChevronLeft className="w-4 h-4" />
                Back
              </button>
              <h2 className="text-lg font-semibold text-gray-900">Resume</h2>
              <div className="w-12"></div>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {currentView === 'edit' ? (
                <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                  <textarea
                    value={resumeContent}
                    onChange={(e) => setResumeContent(e.target.value)}
                    className="w-full min-h-[500px] p-4 font-mono text-xs text-gray-800 leading-relaxed resize-none focus:outline-none"
                  />
                </div>
              ) : (
                <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
                  <div className="font-serif leading-relaxed text-sm">{renderPreview()}</div>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-gray-200 bg-white sticky bottom-0 space-y-2">
              <div className="flex gap-2 mb-2">
                <button
                  onClick={() => setCurrentView(currentView === 'edit' ? 'preview' : 'edit')}
                  className="flex-1 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium"
                >
                  {currentView === 'edit' ? 'Preview' : 'Edit'}
                </button>
                <button
                  onClick={handleCopy}
                  className="flex-1 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium flex items-center justify-center gap-1"
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
              <div className="relative">
                <button
                  onClick={() => setShowDownloadMenu(!showDownloadMenu)}
                  disabled={exporting}
                  className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  {exporting ? 'Exporting...' : 'Download'}
                </button>
                {showDownloadMenu && (
                  <div className="absolute bottom-full left-0 right-0 mb-2 bg-white rounded-lg shadow-lg border border-gray-200">
                    <button
                      onClick={handleDownloadPdf}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 rounded-t-lg"
                    >
                      Download as PDF
                    </button>
                    <button
                      onClick={handleDownloadDocx}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
                    >
                      Download as Word
                    </button>
                    <button
                      onClick={handleDownloadMd}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 rounded-b-lg"
                    >
                      Download as Markdown
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Desktop Layout
  return (
    <div className="flex h-screen bg-gray-50">
      {success && (
        <div className="fixed top-4 right-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2">
          <Check className="w-5 h-5" />
          {success}
        </div>
      )}

      {backendStatus !== 'connected' && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {backendStatus === 'checking' ? 'Checking backend connection...' : 'Backend disconnected - Start server on port 8000'}
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
              disabled={loading}
            />
            <label
              htmlFor="resumeUpload"
              className={`w-full px-4 py-2.5 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition text-gray-600 text-sm font-medium flex items-center justify-center gap-2 ${loading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
            >
              <FileText className="w-4 h-4" />
              {loading ? 'Uploading...' : 'Click to upload resume'}
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
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <button
            onClick={handleGenerate}
            disabled={loading || backendStatus !== 'connected'}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition"
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
                  disabled={exporting}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg text-sm font-medium flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  {exporting ? 'Exporting...' : 'Download'}
                </button>
                {showDownloadMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
                    <button
                      onClick={handleDownloadPdf}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 rounded-t-lg flex items-center justify-between"
                    >
                      <span>Download as PDF</span>
                      <span className="text-xs text-gray-400">.pdf</span>
                    </button>
                    <button
                      onClick={handleDownloadDocx}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center justify-between"
                    >
                      <span>Download as Word</span>
                      <span className="text-xs text-gray-400">.docx</span>
                    </button>
                    <button
                      onClick={handleDownloadMd}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 rounded-b-lg flex items-center justify-between"
                    >
                      <span>Download as Markdown</span>
                      <span className="text-xs text-gray-400">.md</span>
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
