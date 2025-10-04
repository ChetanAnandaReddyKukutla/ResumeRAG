import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'

function CandidateDetail() {
  const { id } = useParams()
  const [resume, setResume] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showPII, setShowPII] = useState(false)
  const [userRole, setUserRole] = useState('user') // Mock role

  useEffect(() => {
    fetchResumeDetail()
  }, [id])

  const fetchResumeDetail = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await fetch(`/api/resumes/${id}`)
      const data = await response.json()

      if (response.ok) {
        setResume(data)
      } else {
        setError(data.error?.message || 'Failed to load resume')
      }
    } catch (err) {
      setError(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="px-4 py-6">
        <div className="bg-white shadow rounded-lg p-6">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="px-4 py-6">
        <div className="bg-white shadow rounded-lg p-6">
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    )
  }

  if (!resume) return null

  return (
    <div className="px-4 py-6">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Candidate Profile</h2>
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">Resume ID: {resume.id}</p>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">
                Uploaded: {new Date(resume.uploaded_at).toLocaleDateString()}
              </span>
              {userRole === 'recruiter' && (
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={showPII}
                    onChange={(e) => setShowPII(e.target.checked)}
                    className="rounded"
                  />
                  Show PII (Recruiter Only)
                </label>
              )}
            </div>
          </div>
        </div>

        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm font-medium text-gray-500 mb-1">Name</p>
            <p className="text-lg font-semibold text-gray-900">
              {resume.name || 'N/A'}
            </p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm font-medium text-gray-500 mb-1">Email</p>
            <p className="text-lg font-semibold text-gray-900">
              {showPII && userRole === 'recruiter' ? 'contact@example.com' : resume.email || 'N/A'}
            </p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm font-medium text-gray-500 mb-1">Phone</p>
            <p className="text-lg font-semibold text-gray-900">
              {showPII && userRole === 'recruiter' ? '(555) 123-4567' : resume.phone || 'N/A'}
            </p>
          </div>
        </div>

        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-3">Resume Content</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {resume.parsed_text_snippets && resume.parsed_text_snippets.length > 0 ? (
              resume.parsed_text_snippets.map((snippet, idx) => (
                <div key={idx} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-gray-500">
                      Page {snippet.page}
                    </span>
                    <span className="text-xs text-gray-400">
                      Chars {snippet.start}-{snippet.end}
                    </span>
                  </div>
                  <p className="text-sm text-gray-800 whitespace-pre-wrap">
                    {snippet.text}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm">No content available</p>
            )}
          </div>
        </div>

        {userRole !== 'recruiter' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              <strong>Note:</strong> Some personally identifiable information (PII) is redacted. 
              Only recruiters can view full contact details.
            </p>
          </div>
        )}

        {userRole === 'recruiter' && (
          <div className="mt-4">
            <button
              onClick={() => setUserRole('user')}
              className="text-sm text-indigo-600 hover:text-indigo-500"
            >
              Switch to User View (for demo)
            </button>
          </div>
        )}
        
        {userRole === 'user' && (
          <div className="mt-4">
            <button
              onClick={() => setUserRole('recruiter')}
              className="text-sm text-indigo-600 hover:text-indigo-500"
            >
              Switch to Recruiter View (for demo)
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default CandidateDetail
