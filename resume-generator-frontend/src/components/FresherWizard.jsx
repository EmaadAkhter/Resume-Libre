import { useState, useMemo } from 'react'
import { Sparkles } from 'lucide-react'

const PROFESSIONS = {
  software: {
    label: 'Software / IT',
    steps: {
      skills: { title: 'Technical Skills', placeholder: 'Python, JavaScript, React, Docker, SQL...', hint: 'Programming languages, frameworks, databases, tools' },
      projects: { title: 'Projects', nameLabel: 'Project Name', techLabel: 'Tech Stack', descLabel: 'Description', linkLabel: 'GitHub Repo URL', linkPlaceholder: 'https://github.com/username/project', hint: 'College projects, hackathon projects, open source' },
      experience: { title: 'Internships', companyLabel: 'Company', roleLabel: 'Role', hint: 'Internships, part-time dev work, freelancing' },
      achievements: { title: 'Achievements', placeholder: 'Hackathon wins, AWS/Google certs, open source contributions, coding competition ranks...', hint: 'Certifications, awards, competition results' },
    },
  },
  finance: {
    label: 'Finance / Commerce',
    steps: {
      skills: { title: 'Financial & Accounting Skills', placeholder: 'Financial Modeling, Excel, Tally, Bloomberg, Accounting, GST, Taxation...', hint: 'Financial tools, accounting software, domain expertise' },
      projects: { title: 'Internships / Deal Experience', nameLabel: 'Deal/Assignment Name', techLabel: 'Domain', descLabel: 'Your Role & Work', linkLabel: '', linkPlaceholder: '', hint: 'Internships, audit assignments, deals you supported' },
      experience: { title: 'Work Experience', companyLabel: 'Organization', roleLabel: 'Position', hint: 'Full-time or part-time work' },
      achievements: { title: 'Certifications', placeholder: 'CFA, CA (inter), CMA, CPA, CS, GST certification...', hint: 'Professional certifications, workshops, seminars' },
    },
  },
  medical: {
    label: 'Medical / Healthcare',
    steps: {
      skills: { title: 'Clinical Skills', placeholder: 'Patient assessment, suturing, ECG interpretation, EMR systems...', hint: 'Clinical procedures, diagnostic skills, equipment' },
      projects: { title: 'Clinical Rotations', nameLabel: 'Department', techLabel: 'Hospital', descLabel: 'Responsibilities & Learnings', linkLabel: '', linkPlaceholder: '', hint: 'Rotations in various departments during MBBS' },
      experience: { title: 'Internships / Residency', companyLabel: 'Hospital / Institution', roleLabel: 'Position', hint: 'Medical internships, residency, observerships' },
      achievements: { title: 'Licenses & Research', placeholder: 'Medical license, NEET PG rank, publications, research papers, conferences...', hint: 'Licenses, publications, research, conferences' },
    },
  },
  legal: {
    label: 'Legal',
    steps: {
      skills: { title: 'Legal Skills', placeholder: 'Legal research, drafting, contract review, litigation, negotiation...', hint: 'Areas of law, legal tools, court procedures' },
      projects: { title: 'Clerkships / Casework', nameLabel: 'Case / Clerkship Name', techLabel: 'Court / Firm', descLabel: 'Work Done', linkLabel: '', linkPlaceholder: '', hint: 'Judicial clerkships, pro bono cases, moot court' },
      experience: { title: 'Work Experience', companyLabel: 'Law Firm / Organization', roleLabel: 'Position', hint: 'Legal internships, associate roles, paralegal work' },
      achievements: { title: 'Bar Admissions & Publications', placeholder: 'Bar council registration, publications, moot court wins, seminars...', hint: 'Bar admissions, publications, certifications' },
    },
  },
  design: {
    label: 'Design / Creative',
    steps: {
      skills: { title: 'Design Skills', placeholder: 'Figma, Adobe Suite (XD, PS, AI), UI/UX, prototyping, motion design...', hint: 'Design tools, software, creative disciplines' },
      projects: { title: 'Design Projects', nameLabel: 'Project Name', techLabel: 'Tools Used', descLabel: 'Description', linkLabel: 'Portfolio URL', linkPlaceholder: 'https://behance.net/... or https://dribbble.com/...', hint: 'Design projects, freelance work, personal projects' },
      experience: { title: 'Work Experience', companyLabel: 'Agency / Company', roleLabel: 'Role', hint: 'Design internships, freelance, in-house roles' },
      achievements: { title: 'Awards & Exhibitions', placeholder: 'Design awards, featured projects, exhibitions, speaking...', hint: 'Awards, exhibitions, publications' },
    },
  },
  mba: {
    label: 'MBA / Management',
    steps: {
      skills: { title: 'Management Skills', placeholder: 'Strategic planning, team leadership, P&L analysis, operations, consulting...', hint: 'Leadership, strategy, analytical skills' },
      projects: { title: 'Projects / Case Competitions', nameLabel: 'Project / Competition Name', techLabel: 'Domain', descLabel: 'Your Contribution', linkLabel: '', linkPlaceholder: '', hint: 'Consulting projects, case competitions, business plans' },
      experience: { title: 'Work Experience', companyLabel: 'Company', roleLabel: 'Position', hint: 'Full-time, internships, consulting engagements' },
      achievements: { title: 'Achievements', placeholder: 'Awards, leadership roles in college clubs, certifications, workshops...', hint: 'Awards, leadership, certifications' },
    },
  },
  general: {
    label: 'General',
    steps: {
      skills: { title: 'Skills', placeholder: 'List your key professional skills...', hint: 'Your core competencies and expertise' },
      projects: { title: 'Key Projects', nameLabel: 'Project / Work Title', techLabel: 'Tools / Area', descLabel: 'Description', linkLabel: '', linkPlaceholder: '', hint: 'Notable projects, key accomplishments' },
      experience: { title: 'Work Experience', companyLabel: 'Organization', roleLabel: 'Role', hint: 'Your professional experience' },
      achievements: { title: 'Achievements', placeholder: 'Awards, certifications, notable accomplishments...', hint: 'Certifications, awards, recognition' },
    },
  },
}

const STEP_LABELS = ['Field', 'Basic Info', 'Education', 'Skills', 'Projects', 'Experience', 'Achievements']

const INITIAL_DATA = {
  name: '',
  email: '',
  phone: '',
  location: '',
  linkedinUrl: '',
  githubUsername: '',
  education: { college: '', degree: '', field: '', graduationYear: '', score: '' },
  skills: '',
  projects: [{ title: '', techStack: '', description: '', link: '' }],
  experience: [{ company: '', role: '', duration: '', description: '' }],
  achievements: '',
}

function buildResumeText(data, profession) {
  const config = PROFESSIONS[profession]
  const s = config.steps

  let text = `--- PROFESSION ---\n${config.label}\n\n`
  text += `--- BASIC INFO ---\nName: ${data.name}\nEmail: ${data.email}\nPhone: ${data.phone}\nLocation: ${data.location}\n`
  if (data.linkedinUrl) text += `LinkedIn: ${data.linkedinUrl}\n`

  text += `\n--- EDUCATION ---\n${data.education.degree || data.education.field} | ${data.education.college} | ${data.education.graduationYear}\n`
  if (data.education.score) text += `Score: ${data.education.score}\n`

  text += `\n--- ${s.skills.title.toUpperCase()} ---\n${data.skills}\n`

  if (data.projects.length > 0) {
    text += `\n--- ${s.projects.title.toUpperCase()} ---\n`
    data.projects.forEach((p, i) => {
      text += `${i + 1}. ${p.title}`
      if (p.techStack) text += ` | ${p.techStack}`
      text += '\n'
      if (p.link) text += `   Link: ${p.link}\n`
      if (p.description) text += `   ${p.description}\n`
    })
  }

  if (data.experience.length > 0) {
    text += `\n--- ${s.experience.title.toUpperCase()} ---\n`
    data.experience.forEach((exp, i) => {
      text += `${i + 1}. ${exp.role} at ${exp.company} (${exp.duration})\n`
      if (exp.description) text += `   ${exp.description}\n`
    })
  }

  if (data.achievements) {
    text += `\n--- ${s.achievements.title.toUpperCase()} ---\n${data.achievements}\n`
  }

  return text
}

export default function FresherWizard({ onGenerate, loading }) {
  const [step, setStep] = useState(0)
  const [profession, setProfession] = useState('software')
  const [data, setData] = useState(INITIAL_DATA)
  const [jobDescription, setJobDescription] = useState('')

  const config = PROFESSIONS[profession]
  const stepConfig = config.steps

  function set(field, value) {
    setData((prev) => ({ ...prev, [field]: value }))
  }

  function handleGenerate() {
    const structuredText = buildResumeText(data, profession)
    onGenerate({
      github_username: data.githubUsername || null,
      linkedin_url: data.linkedinUrl || null,
      additional_info: structuredText || null,
      job_description: jobDescription || null,
      template_format: 'tex',
    })
  }

  function isStepValid() {
    if (step === 0) return true
    if (step === 1) return data.name.trim() && data.email.trim()
    if (step === 2) return data.education.college.trim() && data.education.graduationYear.trim()
    return true
  }

  function renderProfessionPicker() {
    return (
      <div className="space-y-3">
        <p className="text-sm text-gray-600">Select your field to get a tailored resume format:</p>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(PROFESSIONS).map(([key, p]) => (
            <button
              key={key}
              onClick={() => { setProfession(key); setStep(1) }}
              className={`px-3 py-3 border-2 rounded-lg text-sm font-medium text-left transition
                ${profession === key
                  ? 'border-blue-600 bg-blue-50 text-blue-700'
                  : 'border-gray-200 text-gray-700 hover:border-gray-300'
                }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
    )
  }

  function renderBasicInfo() {
    return (
      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Full Name *</label>
          <input type="text" value={data.name} onChange={(e) => set('name', e.target.value)} placeholder="e.g., Priya Sharma" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Email *</label>
          <input type="email" value={data.email} onChange={(e) => set('email', e.target.value)} placeholder="e.g., priya@example.com" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Phone</label>
          <input type="tel" value={data.phone} onChange={(e) => set('phone', e.target.value)} placeholder="e.g., +91-9876543210" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Location (City, State)</label>
          <input type="text" value={data.location} onChange={(e) => set('location', e.target.value)} placeholder="e.g., Mumbai, Maharashtra" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">LinkedIn URL (optional)</label>
          <input type="url" value={data.linkedinUrl} onChange={(e) => set('linkedinUrl', e.target.value)} placeholder="https://linkedin.com/in/username" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">GitHub Username (optional)</label>
          <input type="text" value={data.githubUsername} onChange={(e) => set('githubUsername', e.target.value)} placeholder="e.g., octocat" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
      </div>
    )
  }

  function renderEducation() {
    const ed = data.education
    function setEd(field, value) {
      setData((prev) => ({ ...prev, education: { ...prev.education, [field]: value } }))
    }
    return (
      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">College / University *</label>
          <input type="text" value={ed.college} onChange={(e) => setEd('college', e.target.value)} placeholder="e.g., IIT Bombay" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Degree</label>
          <select value={ed.degree} onChange={(e) => setEd('degree', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white">
            <option value="">Select...</option>
            <option value="B.Tech">B.Tech</option>
            <option value="B.Sc">B.Sc</option>
            <option value="B.Com">B.Com</option>
            <option value="BA">BA</option>
            <option value="BCA">BCA</option>
            <option value="BBA">BBA</option>
            <option value="BDS">BDS</option>
            <option value="B.Arch">B.Arch</option>
            <option value="MBBS">MBBS</option>
            <option value="LLB">LLB</option>
            <option value="M.Tech">M.Tech</option>
            <option value="MBA">MBA</option>
            <option value="M.Sc">M.Sc</option>
            <option value="Other">Other</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Field / Major</label>
          <input type="text" value={ed.field} onChange={(e) => setEd('field', e.target.value)} placeholder="e.g., Computer Science, Finance" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Graduation Year *</label>
          <input type="text" value={ed.graduationYear} onChange={(e) => setEd('graduationYear', e.target.value)} placeholder="e.g., 2025" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">CGPA / Percentage (optional)</label>
          <input type="text" value={ed.score} onChange={(e) => setEd('score', e.target.value)} placeholder="e.g., 8.5/10 or 85%" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
      </div>
    )
  }

  function renderSkills() {
    const sc = stepConfig.skills
    return (
      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">{sc.title} *</label>
          <textarea value={data.skills} onChange={(e) => set('skills', e.target.value)} placeholder={sc.placeholder} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm h-28 resize-none" />
          <p className="mt-1 text-xs text-gray-500">{sc.hint}</p>
        </div>
      </div>
    )
  }

  function renderProjects() {
    const pc = stepConfig.projects
    function setProject(i, field, value) {
      setData((prev) => {
        const projects = [...prev.projects]
        projects[i] = { ...projects[i], [field]: value }
        return { ...prev, projects }
      })
    }
    function addProject() {
      setData((prev) => ({ ...prev, projects: [...prev.projects, { title: '', techStack: '', description: '', link: '' }] }))
    }
    function removeProject(i) {
      setData((prev) => ({ ...prev, projects: prev.projects.filter((_, idx) => idx !== i) }))
    }
    return (
      <div className="space-y-3">
        {data.projects.map((proj, i) => (
          <div key={i} className="p-3 border border-gray-200 rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-gray-500">{pc.title} #{i + 1}</span>
              {data.projects.length > 1 && (
                <button onClick={() => removeProject(i)} className="text-xs text-red-500 hover:text-red-700">Remove</button>
              )}
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-0.5">{pc.nameLabel} *</label>
              <input type="text" value={proj.title} onChange={(e) => setProject(i, 'title', e.target.value)} placeholder={pc.nameLabel} className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-0.5">{pc.techLabel}</label>
              <input type="text" value={proj.techStack} onChange={(e) => setProject(i, 'techStack', e.target.value)} placeholder={pc.techLabel} className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-0.5">{pc.descLabel}</label>
              <textarea value={proj.description} onChange={(e) => setProject(i, 'description', e.target.value)} placeholder={pc.descLabel} className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm h-16 resize-none" />
            </div>
            {pc.linkLabel && (
              <div>
                <label className="block text-xs text-gray-600 mb-0.5">{pc.linkLabel}</label>
                <input type="url" value={proj.link} onChange={(e) => setProject(i, 'link', e.target.value)} placeholder={pc.linkPlaceholder} className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
              </div>
            )}
          </div>
        ))}
        <button onClick={addProject} className="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add another {pc.title.toLowerCase()}</button>
        <p className="text-xs text-gray-500">{pc.hint}</p>
      </div>
    )
  }

  function renderExperience() {
    const ec = stepConfig.experience
    function setExp(i, field, value) {
      setData((prev) => {
        const experience = [...prev.experience]
        experience[i] = { ...experience[i], [field]: value }
        return { ...prev, experience }
      })
    }
    function addExp() {
      setData((prev) => ({ ...prev, experience: [...prev.experience, { company: '', role: '', duration: '', description: '' }] }))
    }
    function removeExp(i) {
      setData((prev) => ({ ...prev, experience: prev.experience.filter((_, idx) => idx !== i) }))
    }
    return (
      <div className="space-y-3">
        {data.experience.map((exp, i) => (
          <div key={i} className="p-3 border border-gray-200 rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-gray-500">{ec.title} #{i + 1}</span>
              {data.experience.length > 1 && (
                <button onClick={() => removeExp(i)} className="text-xs text-red-500 hover:text-red-700">Remove</button>
              )}
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-0.5">{ec.companyLabel} *</label>
              <input type="text" value={exp.company} onChange={(e) => setExp(i, 'company', e.target.value)} placeholder={ec.companyLabel} className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-0.5">{ec.roleLabel} *</label>
              <input type="text" value={exp.role} onChange={(e) => setExp(i, 'role', e.target.value)} placeholder={ec.roleLabel} className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-0.5">Duration</label>
              <input type="text" value={exp.duration} onChange={(e) => setExp(i, 'duration', e.target.value)} placeholder="e.g., Jun 2024 - Aug 2024" className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-0.5">Description</label>
              <textarea value={exp.description} onChange={(e) => setExp(i, 'description', e.target.value)} placeholder="What you did and achieved" className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm h-16 resize-none" />
            </div>
          </div>
        ))}
        <button onClick={addExp} className="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Add another {ec.title.toLowerCase()}</button>
        {stepConfig.experience.hint && <p className="text-xs text-gray-500">{stepConfig.experience.hint}</p>}
      </div>
    )
  }

  function renderAchievements() {
    const ac = stepConfig.achievements
    return (
      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">{ac.title}</label>
          <textarea value={data.achievements} onChange={(e) => set('achievements', e.target.value)} placeholder={ac.placeholder} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm h-24 resize-none" />
          <p className="mt-1 text-xs text-gray-500">{ac.hint}</p>
        </div>
        <details className="mt-2">
          <summary className="text-xs font-medium text-gray-600 cursor-pointer">Target a specific job (optional)</summary>
          <textarea value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} placeholder="Paste the job description here... AI will tailor your resume to match." className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm h-24 resize-none mt-2" />
        </details>
      </div>
    )
  }

  const stepRenderers = [renderProfessionPicker, renderBasicInfo, renderEducation, renderSkills, renderProjects, renderExperience, renderAchievements]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {STEP_LABELS.map((label, i) => (
            <div key={i} className={`text-[10px] px-1.5 py-0.5 rounded ${step === i ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-400'}`}>
              {label}
            </div>
          ))}
        </div>
        <span className="text-xs text-gray-400">{step + 1}/{STEP_LABELS.length}</span>
      </div>

      <div className="min-h-[200px]">
        {stepRenderers[step]()}
      </div>

      <div className="flex gap-2 pt-2">
        {step > 0 && (
          <button onClick={() => setStep(step - 1)} className="px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 flex-1">
            Back
          </button>
        )}
        {step < STEP_LABELS.length - 1 ? (
          <button onClick={() => setStep(step + 1)} disabled={!isStepValid()} className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium flex-1">
            Next
          </button>
        ) : (
          <button onClick={handleGenerate} disabled={loading} className="w-full flex items-center justify-center gap-2 px-3 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg text-sm font-medium flex-1">
            <Sparkles className="w-4 h-4" />
            {loading ? 'Generating...' : 'Generate Resume'}
          </button>
        )}
      </div>
    </div>
  )
}
