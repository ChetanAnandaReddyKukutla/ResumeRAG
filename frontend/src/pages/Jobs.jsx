import { useState } from 'react'

function Jobs() {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [createdJob, setCreatedJob] = useState(null)
  const [matches, setMatches] = useState(null)
  const [topN, setTopN] = useState(10)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleCreateJob = async (e) => {
    e.preventDefault()
    
    if (!title.trim() || !description.trim()) {
      setError('Please fill in all fields')
      return
    }

    setLoading(true)
    setError('')

    try {
      const idempotencyKey = crypto.randomUUID()

      const response = await fetch('/api/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': idempotencyKey,
        },
        body: JSON.stringify({ title, description }),
      })

      const data = await response.json()

      if (response.ok) {
        setCreatedJob(data)
        setError('')
      } else {
        setError(data.error?.message || 'Failed to create job')
      }
    } catch (err) {
      setError(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleMatch = async () => {
    if (!createdJob) return

    setLoading(true)
    setError('')

    try {
      const response = await fetch(`/api/jobs/${createdJob.id}/match`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ top_n: topN }),
      })

      const data = await response.json()

      if (response.ok) {
        setMatches(data)
      } else {
        setError(data.error?.message || 'Failed to match candidates')
      }
    } catch (err) {
      setError(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="px-4 py-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Job Matching</h2>
        <p className="text-gray-600">Create job postings and find the best candidate matches</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Create Job Form */}
        <div className="bg-white shadow-xl rounded-2xl overflow-hidden border border-gray-100">
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4">
            <h3 className="text-white text-lg font-semibold flex items-center">
              <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Create Job Posting
            </h3>
          </div>
          
          <form onSubmit={handleCreateJob} className="p-6">
            <div className="mb-5">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Job Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Frontend Engineer"
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200"
              />
            </div>

            <div className="mb-5">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Job Description & Requirements
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g., React, Node, GraphQL, Docker..."
                rows={6}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-6 border border-transparent rounded-xl shadow-lg text-base font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02]"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating...
                </span>
              ) : (
                'Create Job'
              )}
            </button>
          </form>

          {error && (
            <div className="mx-6 mb-6 p-4 rounded-xl bg-red-50 border-l-4 border-red-500 text-red-800 text-sm flex items-start animate-fade-in">
              <svg className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          )}

          {createdJob && (
            <div className="mx-6 mb-6 animate-fade-in">
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-5 rounded-xl border border-green-200">
                <h4 className="font-semibold text-green-900 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Job Created Successfully!
                </h4>
                <dl className="text-sm text-green-800 space-y-2">
                  <div>
                    <dt className="font-semibold">ID:</dt>
                    <dd className="font-mono text-xs bg-white px-2 py-1 rounded border border-green-300 mt-1">{createdJob.id}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold mb-1">Parsed Requirements:</dt>
                    <dd className="flex flex-wrap gap-1">
                      {createdJob.parsed_requirements?.map((req, i) => (
                        <span key={i} className="px-2 py-1 text-xs bg-white text-green-700 rounded-full border border-green-300">
                          {req}
                        </span>
                      ))}
                    </dd>
                  </div>
                </dl>

                <div className="mt-4 pt-4 border-t border-green-200">
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    Number of Matches
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      value={topN}
                      onChange={(e) => setTopN(parseInt(e.target.value))}
                      min="1"
                      max="50"
                      className="flex-1 px-4 py-2 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                    <button
                      onClick={handleMatch}
                      disabled={loading}
                      className="px-6 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 font-semibold transition-all duration-200 transform hover:scale-105"
                    >
                      Find Matches
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Matches Display */}
        <div className="bg-white shadow-xl rounded-2xl overflow-hidden border border-gray-100">
          <div className="bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-4">
            <h3 className="text-white text-lg font-semibold flex items-center">
              <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Candidate Matches
            </h3>
          </div>
          
          <div className="p-6">
            {!matches ? (
              <div className="text-center py-12">
                <svg className="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <p className="mt-4 text-gray-500 font-medium">No matches yet</p>
                <p className="text-sm text-gray-400 mt-2">Create a job and click "Find Matches"</p>
              </div>
            ) : (
              <div className="space-y-4 max-h-[calc(100vh-300px)] overflow-y-auto">
                {matches.matches.length === 0 ? (
                  <div className="text-center py-8">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="mt-4 text-gray-500">No matches found.</p>
                  </div>
                ) : (
                  matches.matches.map((match, idx) => {
                    // Function to highlight matched keyword in text
                    const highlightText = (text, keyword) => {
                      if (!keyword || !text) return text;
                      
                      // Escape special regex characters
                      const escapeRegex = (str) => {
                        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                      };
                      
                      // Split on commas to handle multiple keywords
                      const keywords = keyword.split(',').map(k => k.trim());
                      
                      // Create regex pattern for all keywords
                      const pattern = keywords.map(k => escapeRegex(k)).join('|');
                      const regex = new RegExp(`(${pattern})`, 'gi');
                      
                      // Split text by matches
                      const parts = text.split(regex);
                      
                      return parts.map((part, index) => {
                        // Check if this part matches any keyword (case-insensitive)
                        const isMatch = keywords.some(k => 
                          part.toLowerCase() === k.toLowerCase()
                        );
                        
                        if (isMatch) {
                          return (
                            <mark
                              key={index}
                              className="bg-yellow-200 font-semibold px-1 rounded"
                            >
                              {part}
                            </mark>
                          );
                        }
                        return <span key={index}>{part}</span>;
                      });
                    };

                    return (
                      <div key={idx} className="border border-gray-200 rounded-xl p-5 hover:shadow-lg transition-all duration-200 bg-white hover:border-green-300 animate-fade-in">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-gray-900 flex items-center">
                              <svg className="w-5 h-5 mr-2 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                              {match.filename || `Resume ${match.resume_id}`}
                            </span>
                            <a
                              href={`/api/resumes/${match.resume_id}/download`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-3 py-1 text-xs bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 font-semibold"
                            >
                              View PDF
                            </a>
                          </div>
                          <span className="px-3 py-1 text-sm font-bold bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 rounded-full border border-green-300">
                            {(match.score * 100).toFixed(1)}% Match
                          </span>
                        </div>

                        {match.evidence.length > 0 && (
                          <div className="mt-4">
                            <p className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                              <svg className="w-4 h-4 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              Evidence:
                            </p>
                            <div className="space-y-2">
                              {match.evidence.map((ev, eidx) => (
                                <div key={eidx} className="bg-gradient-to-r from-gray-50 to-green-50 p-3 rounded-lg border border-gray-200 hover:border-green-300 transition-colors duration-200">
                                  <p className="text-xs font-semibold text-green-700 mb-2">
                                    Matched: {ev.matched_keyword}
                                  </p>
                                  <p className="text-sm text-gray-800 leading-relaxed">
                                    {highlightText(ev.text, ev.matched_keyword)}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {match.missing_requirements && match.missing_requirements.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-xs font-semibold text-gray-600 mb-2 flex items-center">
                              <svg className="w-4 h-4 mr-2 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                              </svg>
                              Missing: 
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {match.missing_requirements.map((req, ridx) => (
                                <span key={ridx} className="px-2 py-1 text-xs bg-amber-100 text-amber-800 rounded-full border border-amber-300">
                                  {req}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Jobs
