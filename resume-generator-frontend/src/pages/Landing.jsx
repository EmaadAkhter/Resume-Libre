import { Link } from 'react-router-dom'
import { Github, Sparkles, FileText, GitBranch, Server, ShieldCheck } from 'lucide-react'

const REPO_URL = 'https://github.com/EmaadAkhter/Resume-Libre'

export default function Landing() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto w-full">
        <img src="/logo.png" alt="ResumeLibre" className="h-8 w-auto" style={{ viewTransitionName: 'site-logo' }} />
        <div className="flex items-center gap-3">
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <Github className="w-4 h-4" />
            GitHub
          </a>
          <Link
            to="/login"
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            Sign in
          </Link>
          <Link
            to="/register"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition"
          >
            Get started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <main className="flex-1 max-w-6xl mx-auto px-6 w-full">
        <section className="text-center py-16 sm:py-24">
          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 tracking-tight">
            Your GitHub profile,
            <br />
            <span className="text-blue-600">turned into a resume that gets read.</span>
          </h1>
          <p className="mt-6 text-lg text-gray-600 max-w-2xl mx-auto">
            Point Resume-Libre at your GitHub, paste your LinkedIn, add a job description — get a
            polished, one-page LaTeX PDF tailored to the role. Open source, self-hostable, no fake
            "ATS scores".
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to="/register"
              className="w-full sm:w-auto px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              Generate your resume
            </Link>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noreferrer"
              className="w-full sm:w-auto px-6 py-3 bg-white border border-gray-300 hover:border-gray-400 text-gray-800 rounded-lg font-medium transition flex items-center justify-center gap-2"
            >
              <Github className="w-4 h-4" />
              Star on GitHub
            </a>
          </div>
          <p className="mt-4 text-xs text-gray-500">
            Free while in beta · Self-host with one command:{' '}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded text-gray-700">docker compose up</code>
          </p>
        </section>

        {/* Features */}
        <section className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 pb-20">
          {[
            {
              icon: <FileText className="w-5 h-5 text-blue-600" />,
              title: 'Real LaTeX, real PDFs',
              body: 'Every resume is a compilable LaTeX document rendered by Tectonic — the typesetting that recruiters recognize, not a styled web page.',
            },
            {
              icon: <Sparkles className="w-5 h-5 text-blue-600" />,
              title: 'Tailored to the job',
              body: 'Paste a job description and the AI reshapes your experience, projects, and skills to match the role.',
            },
            {
              icon: <GitBranch className="w-5 h-5 text-blue-600" />,
              title: 'Version control built in',
              body: 'Branches, commits, and history for your resume — try a variant for every application without losing the original.',
            },
            {
              icon: <Github className="w-5 h-5 text-blue-600" />,
              title: 'Starts from your GitHub',
              body: 'Your profile README and projects become the raw material. Add LinkedIn by pasting your profile text — no scraping required.',
            },
            {
              icon: <Server className="w-5 h-5 text-blue-600" />,
              title: 'Self-hostable',
              body: 'AGPL-3.0 open source. Run the whole stack — frontend, API, LaTeX compiler — on your own machine with Docker Compose.',
            },
            {
              icon: <ShieldCheck className="w-5 h-5 text-blue-600" />,
              title: 'Privacy first',
              body: 'Uploads are processed in memory and never written to disk. Your resumes are yours — row-level security keeps it that way.',
            },
          ].map((f) => (
            <div key={f.title} className="bg-white rounded-lg border border-gray-200 p-5">
              <div className="flex items-center gap-2 mb-2">
                {f.icon}
                <h3 className="font-semibold text-gray-900 text-sm">{f.title}</h3>
              </div>
              <p className="text-sm text-gray-600">{f.body}</p>
            </div>
          ))}
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-500">
          <span>AGPL-3.0 open source · Built by the community</span>
          <div className="flex items-center gap-4">
            <a href={REPO_URL} target="_blank" rel="noreferrer" className="hover:text-gray-700">
              GitHub
            </a>
            <a
              href={`${REPO_URL}/blob/main/PRIVACY.md`}
              target="_blank"
              rel="noreferrer"
              className="hover:text-gray-700"
            >
              Privacy
            </a>
            <a
              href={`${REPO_URL}/blob/main/TERMS.md`}
              target="_blank"
              rel="noreferrer"
              className="hover:text-gray-700"
            >
              Terms
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
