import { Link } from 'react-router-dom'

function Home() {
  return (
    <div className="relative overflow-hidden">
      {/* Hero Section */}
      <div className="relative z-10 pb-12 sm:pb-16 md:pb-20 lg:pb-28 xl:pb-32">
        <main className="mt-8 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 xl:mt-28">
          <div className="text-center">
            {/* Badge */}
            <div className="flex justify-center mb-6 sm:mb-8">
              <span className="inline-flex items-center px-3 py-1.5 sm:px-4 sm:py-2 rounded-full text-xs sm:text-sm font-medium bg-gradient-to-r from-indigo-100 to-purple-100 text-indigo-800 border border-indigo-200 animate-fade-in">
                <svg className="w-4 h-4 sm:w-5 sm:h-5 mr-1.5 sm:mr-2 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                AI-Powered Resume Matching
              </span>
            </div>

            {/* Main Heading */}
            <h1 className="text-3xl tracking-tight font-extrabold text-gray-900 sm:text-4xl md:text-5xl lg:text-6xl px-2">
              <span className="block mb-1 sm:mb-2">Find the Perfect</span>
              <span className="block bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                Candidate Match
              </span>
            </h1>

            {/* Subtitle */}
            <p className="mt-4 max-w-md mx-auto text-sm text-gray-600 sm:text-base sm:mt-6 md:mt-8 md:text-lg lg:text-xl md:max-w-3xl px-4">
              Leverage cutting-edge RAG (Retrieval-Augmented Generation) technology to instantly search, 
              match, and discover top talent from your resume database with semantic precision.
            </p>

            {/* CTA Buttons */}
            <div className="mt-8 sm:mt-10 md:mt-12 max-w-md mx-auto flex flex-col sm:flex-row sm:justify-center gap-3 sm:gap-4 px-4">
              <div className="rounded-xl shadow">
                <Link
                  to="/upload"
                  className="w-full flex items-center justify-center px-6 py-3 sm:px-8 sm:py-4 border border-transparent text-sm sm:text-base font-semibold rounded-xl text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 md:text-lg md:px-10 transition-all duration-200 transform hover:scale-105 shadow-lg"
                >
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Upload Resumes
                </Link>
              </div>
              <div className="rounded-xl shadow">
                <Link
                  to="/search"
                  className="w-full flex items-center justify-center px-6 py-3 sm:px-8 sm:py-4 border-2 border-indigo-600 text-sm sm:text-base font-semibold rounded-xl text-indigo-600 bg-white hover:bg-indigo-50 md:text-lg md:px-10 transition-all duration-200"
                >
                  <svg className="w-4 h-4 sm:w-5 sm:h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  Search Now
                </Link>
              </div>
            </div>

            {/* Stats */}
            <div className="mt-12 sm:mt-16 grid grid-cols-1 gap-6 sm:grid-cols-3 sm:gap-8 lg:gap-16 px-4">
              <div className="flex flex-col items-center animate-fade-in">
                <div className="flex items-center justify-center h-12 w-12 sm:h-16 sm:w-16 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 mb-3 sm:mb-4">
                  <svg className="h-6 w-6 sm:h-8 sm:w-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <p className="text-2xl sm:text-3xl font-bold text-gray-900">10x Faster</p>
                <p className="text-xs sm:text-sm text-gray-600 mt-1 sm:mt-2">Resume screening speed</p>
              </div>
              <div className="flex flex-col items-center animate-fade-in" style={{ animationDelay: '0.1s' }}>
                <div className="flex items-center justify-center h-12 w-12 sm:h-16 sm:w-16 rounded-full bg-gradient-to-br from-green-100 to-emerald-100 mb-3 sm:mb-4">
                  <svg className="h-6 w-6 sm:h-8 sm:w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-2xl sm:text-3xl font-bold text-gray-900">95%</p>
                <p className="text-xs sm:text-sm text-gray-600 mt-1 sm:mt-2">Match accuracy</p>
              </div>
              <div className="flex flex-col items-center animate-fade-in" style={{ animationDelay: '0.2s' }}>
                <div className="flex items-center justify-center h-12 w-12 sm:h-16 sm:w-16 rounded-full bg-gradient-to-br from-pink-100 to-rose-100 mb-3 sm:mb-4">
                  <svg className="h-6 w-6 sm:h-8 sm:w-8 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-2xl sm:text-3xl font-bold text-gray-900">&lt; 1 sec</p>
                <p className="text-xs sm:text-sm text-gray-600 mt-1 sm:mt-2">Average search time</p>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Features Section */}
      <div className="py-12 sm:py-16 bg-white rounded-2xl sm:rounded-3xl mx-3 sm:mx-6 lg:mx-8 shadow-xl border border-gray-100 mt-12 sm:mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-gray-900 md:text-4xl">
              Powerful Features
            </h2>
            <p className="mt-3 sm:mt-4 text-base sm:text-lg text-gray-600 px-2">
              Everything you need to find the perfect candidate
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1 */}
            <div className="relative group h-full">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-200"></div>
              <div className="relative bg-white p-5 rounded-xl border border-gray-200 hover:border-transparent transition-all duration-200 h-full flex flex-col">
                <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center mb-3">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Semantic Search</h3>
                <p className="text-sm text-gray-600 flex-grow">
                  Ask questions in natural language and get intelligent, context-aware matches from your resume database.
                </p>
              </div>
            </div>

            {/* Feature 2 */}
            <div className="relative group h-full">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-green-600 to-emerald-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-200"></div>
              <div className="relative bg-white p-5 rounded-xl border border-gray-200 hover:border-transparent transition-all duration-200 h-full flex flex-col">
                <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center mb-3">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Job Matching</h3>
                <p className="text-sm text-gray-600 flex-grow">
                  Create job postings and automatically rank candidates by skills, experience, and requirements fit.
                </p>
              </div>
            </div>

            {/* Feature 3 */}
            <div className="relative group h-full">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-pink-600 to-rose-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-200"></div>
              <div className="relative bg-white p-5 rounded-xl border border-gray-200 hover:border-transparent transition-all duration-200 h-full flex flex-col">
                <div className="w-10 h-10 bg-gradient-to-br from-pink-500 to-rose-600 rounded-lg flex items-center justify-center mb-3">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Bulk Upload</h3>
                <p className="text-sm text-gray-600 flex-grow">
                  Upload single resumes or entire ZIP archives. Supports PDF, DOCX, TXT formats with automatic parsing.
                </p>
              </div>
            </div>

            {/* Feature 4 */}
            <div className="relative group h-full">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-200"></div>
              <div className="relative bg-white p-5 rounded-xl border border-gray-200 hover:border-transparent transition-all duration-200 h-full flex flex-col">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-lg flex items-center justify-center mb-3">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Evidence Highlighting</h3>
                <p className="text-sm text-gray-600 flex-grow">
                  See exactly where skills and keywords appear in resumes with intelligent paragraph extraction.
                </p>
              </div>
            </div>

            {/* Feature 5 */}
            <div className="relative group h-full">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-amber-600 to-orange-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-200"></div>
              <div className="relative bg-white p-5 rounded-xl border border-gray-200 hover:border-transparent transition-all duration-200 h-full flex flex-col">
                <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center mb-3">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">PII Protection</h3>
                <p className="text-sm text-gray-600 flex-grow">
                  Role-based access control with automatic redaction of sensitive information like emails and phone numbers.
                </p>
              </div>
            </div>

            {/* Feature 6 */}
            <div className="relative group h-full">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-violet-600 to-purple-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-200"></div>
              <div className="relative bg-white p-5 rounded-xl border border-gray-200 hover:border-transparent transition-all duration-200 h-full flex flex-col">
                <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg flex items-center justify-center mb-3">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Lightning Fast</h3>
                <p className="text-sm text-gray-600 flex-grow">
                  Vector embeddings and pgvector enable sub-second search across thousands of resumes with high accuracy.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="py-12 sm:py-16 mt-12 sm:mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-gray-900 md:text-4xl">
              How It Works
            </h2>
            <p className="mt-3 sm:mt-4 text-base sm:text-lg text-gray-600 px-2">
              Get started in three simple steps
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-3 px-2">
            <div className="relative">
              <div className="flex flex-col items-center">
                <div className="flex items-center justify-center h-14 w-14 sm:h-16 sm:w-16 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 text-white text-xl sm:text-2xl font-bold mb-3 sm:mb-4 shadow-lg">
                  1
                </div>
                <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">Upload Resumes</h3>
                <p className="text-center text-sm sm:text-base text-gray-600 px-2">
                  Upload individual resumes or bulk ZIP files. Our system automatically parses and indexes them.
                </p>
              </div>
              <div className="hidden md:block absolute top-8 left-full w-full h-0.5 bg-gradient-to-r from-indigo-600 to-purple-600 opacity-30" style={{ width: 'calc(100% - 4rem)', left: 'calc(50% + 2rem)' }}></div>
            </div>

            <div className="relative">
              <div className="flex flex-col items-center">
                <div className="flex items-center justify-center h-14 w-14 sm:h-16 sm:w-16 rounded-full bg-gradient-to-br from-green-600 to-emerald-600 text-white text-xl sm:text-2xl font-bold mb-3 sm:mb-4 shadow-lg">
                  2
                </div>
                <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">Search or Match</h3>
                <p className="text-center text-sm sm:text-base text-gray-600 px-2">
                  Use natural language search or create job postings to find the best candidates instantly.
                </p>
              </div>
              <div className="hidden md:block absolute top-8 left-full w-full h-0.5 bg-gradient-to-r from-green-600 to-emerald-600 opacity-30" style={{ width: 'calc(100% - 4rem)', left: 'calc(50% + 2rem)' }}></div>
            </div>

            <div className="relative">
              <div className="flex flex-col items-center">
                <div className="flex items-center justify-center h-14 w-14 sm:h-16 sm:w-16 rounded-full bg-gradient-to-br from-pink-600 to-rose-600 text-white text-xl sm:text-2xl font-bold mb-3 sm:mb-4 shadow-lg">
                  3
                </div>
                <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">Review Results</h3>
                <p className="text-center text-sm sm:text-base text-gray-600 px-2">
                  Get ranked matches with highlighted evidence, match scores, and detailed candidate information.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl sm:rounded-3xl mx-3 sm:mx-6 lg:mx-8 shadow-2xl mt-12 sm:mt-16 mb-12 sm:mb-16">
        <div className="max-w-7xl mx-auto py-8 sm:py-12 px-4 sm:px-6 lg:py-16 lg:px-8 lg:flex lg:items-center lg:justify-between">
          <div className="text-center lg:text-left mb-6 lg:mb-0">
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white md:text-4xl">
              <span className="block">Ready to find top talent?</span>
              <span className="block text-indigo-200 mt-1">Start matching candidates today.</span>
            </h2>
          </div>
          <div className="flex flex-col sm:flex-row lg:flex-shrink-0 gap-3 sm:gap-4 justify-center lg:justify-start">
            <div className="inline-flex rounded-xl shadow w-full sm:w-auto">
              <Link
                to="/upload"
                className="w-full inline-flex items-center justify-center px-6 py-3 sm:px-8 sm:py-4 border border-transparent text-sm sm:text-base font-semibold rounded-xl text-indigo-600 bg-white hover:bg-indigo-50 transition-all duration-200 transform hover:scale-105"
              >
                Get Started
                <svg className="ml-2 w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home
