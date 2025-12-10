import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../api/client'
import { LogIn, AlertCircle, Info } from 'lucide-react'

export default function NaverLogin() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Check if already logged in (without blocking render)
  useEffect(() => {
    // Force clear any previous errors
    setError(null)
    setLoading(false)
    
    const checkStatus = async () => {
      try {
        const response = await apiClient.get('/api/naver/status', { timeout: 5000 })
        if (response.data?.logged_in) {
          navigate('/dashboard?naver_auth=success')
        }
      } catch (err) {
        // Silently fail - just show login form
        console.log('Not logged in to Naver')
      }
    }
    checkStatus()
  }, [navigate])

  const handleLogin = async (e) => {
    e.preventDefault()
    
    try {
      setLoading(true)
      setError(null)

      const response = await apiClient.post('/api/naver/login', {
        username,
        password
      })

      if (response.data.success) {
        navigate('/dashboard?naver_auth=success')
      } else {
        setError(response.data.message)
      }
    } catch (err) {
      setError(err.response?.data?.detail || '로그인 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">네이버 플레이스 연결</h1>
          <p className="text-gray-600">스마트플레이스 센터 계정으로 로그인하세요</p>
        </div>

        {/* Info Banners */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <div className="flex items-start">
            <Info className="w-5 h-5 text-blue-600 mr-3 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-blue-900">2차 인증 안내</h3>
              <p className="text-xs text-blue-800 mt-1">
                로그인 시 Chrome 브라우저가 자동으로 열립니다.<br />
                2차 인증(OTP, SMS)이 필요한 경우 <strong>60초 내에 직접 인증</strong>을 완료해주세요.<br />
                인증 완료 후 자동으로 세션이 저장되며, 다음부터는 로그인이 필요하지 않습니다.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <Info className="w-5 h-5 text-yellow-600 mr-3 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-yellow-900">주의사항</h3>
              <p className="text-xs text-yellow-800 mt-1">
                네이버는 공식 리뷰 관리 API를 제공하지 않습니다. 
                이 기능은 웹 자동화를 사용하며, 개인 사용 목적으로만 사용하시기 바랍니다.
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start">
            <AlertCircle className="w-5 h-5 text-red-500 mr-3 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-800">로그인 실패</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              네이버 아이디
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="아이디를 입력하세요"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              비밀번호
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호를 입력하세요"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-semibold py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>브라우저 창에서 2차 인증을 완료해주세요...</span>
              </>
            ) : (
              <>
                <LogIn className="w-5 h-5" />
                <span>로그인 (브라우저 자동 실행)</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            대시보드로 돌아가기
          </button>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-900 mb-3">로그인 절차</h3>
          <ul className="text-sm text-gray-600 space-y-2 list-disc list-inside">
            <li>네이버 계정 정보를 입력하고 <strong>로그인</strong> 버튼을 클릭하세요</li>
            <li>Chrome 브라우저가 자동으로 실행됩니다</li>
            <li><strong>2차 인증(OTP, SMS)</strong>이 필요한 경우 브라우저 창에서 직접 완료해주세요</li>
            <li>인증 완료 후 세션이 저장되며, <strong>다음부터는 로그인이 필요하지 않습니다</strong></li>
            <li>세션 만료 시에만 다시 로그인하면 됩니다</li>
          </ul>
        </div>
      </div>
    </div>
  )
}




