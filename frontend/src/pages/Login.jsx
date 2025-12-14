import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import apiClient from '../api/client'
import { LogIn, AlertCircle } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    // 🚀 실제 인증 확인 (Google OAuth)
    const googleEmail = localStorage.getItem('google_email')
    const isLoggedIn = localStorage.getItem('user_logged_in')
    
    // 🔐 'default'는 로그인 실패로 간주
    if (googleEmail && googleEmail !== 'default' && isLoggedIn === 'true') {
      // Google 로그인되어 있으면 Dashboard로
      console.log(`✅ Already logged in as: ${googleEmail}`)
      navigate('/dashboard')
      return
    }

    // Handle error from callback
    const errorParam = searchParams.get('error')
    if (errorParam) {
      // 🔐 에러 메시지를 사용자 친화적으로 변환
      const errorMessages = {
        'google_auth_failed': 'Google 계정 정보를 가져올 수 없습니다. 다시 시도해주세요.',
        'no_email': 'Google 계정의 이메일 정보가 없습니다.',
        'access_denied': '접근이 거부되었습니다.'
      }
      setError(errorMessages[errorParam] || errorParam)
    }
  }, [navigate, searchParams])

  const handleLogin = async () => {
    try {
      setLoading(true)
      setError(null)

      // 🚀 실제 Google OAuth 사용
      const response = await apiClient.get('/auth/google/login')
      
      // Google 로그인 페이지로 리디렉션
      window.location.href = response.data.authorization_url
      
    } catch (err) {
      setError(err.response?.data?.detail || '로그인에 실패했습니다')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">리뷰 관리 시스템</h1>
          <p className="text-gray-600">Google Business Profile 리뷰를 쉽게 관리하세요</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start">
            <AlertCircle className="w-5 h-5 text-red-500 mr-3 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-800">오류가 발생했습니다</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}

        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>로그인 중...</span>
            </>
          ) : (
            <>
              <LogIn className="w-5 h-5" />
              <span>로그인</span>
            </>
          )}
        </button>

        <div className="mt-6 text-center text-sm text-gray-500">
          <p>리뷰 관리 시스템에 접속합니다.</p>
          <p>GBP와 네이버 플레이스 리뷰를 한 곳에서 관리하세요.</p>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-900 mb-3">안내</h3>
          <ul className="text-sm text-gray-600 space-y-2">
            <li>• 로그인 후 대시보드에서 GBP를 연결할 수 있습니다</li>
            <li>• 네이버 플레이스는 별도 로그인이 필요합니다</li>
            <li>• AI 답글 자동 생성 기능을 제공합니다</li>
          </ul>
        </div>
      </div>
    </div>
  )
}





