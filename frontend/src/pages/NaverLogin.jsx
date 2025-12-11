import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../api/client'
import { Download, CheckCircle, XCircle, AlertCircle, Info, RefreshCw, Trash2, HelpCircle } from 'lucide-react'

export default function NaverLogin() {
  const navigate = useNavigate()
  const [sessionStatus, setSessionStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showGuide, setShowGuide] = useState(false)

  // Check session status
  useEffect(() => {
    checkSessionStatus()
  }, [])

  const checkSessionStatus = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/naver/session/status', { timeout: 5000 })
      setSessionStatus(response.data)
      setError(null)
    } catch (err) {
      setSessionStatus({ exists: false })
      console.log('No session found')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteSession = async () => {
    if (!confirm('세션을 삭제하시겠습니까? 다시 로그인해야 합니다.')) {
      return
    }
    
    try {
      setLoading(true)
      await apiClient.delete('/api/naver/session')
      setSessionStatus({ exists: false })
      setError(null)
    } catch (err) {
      setError('세션 삭제 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadTool = () => {
    // TODO: EXE 파일 다운로드 링크
    window.open('/downloads/NaverSessionCreator.exe', '_blank')
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    const now = new Date()
    const diff = Math.floor((now - date) / 1000)
    
    if (diff < 60) return '방금 전'
    if (diff < 3600) return `${Math.floor(diff / 60)}분 전`
    if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`
    return `${Math.floor(diff / 86400)}일 전`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="text-center mt-4 text-gray-600">세션 상태 확인 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-2xl w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📱 네이버 플레이스 연결</h1>
          <p className="text-gray-600">세션 생성 도구로 간편하게 연결하세요</p>
        </div>

        {/* Session Status Card */}
        {sessionStatus?.exists ? (
          <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6 mb-6">
            <div className="flex items-start justify-between">
              <div className="flex items-start">
                <CheckCircle className="w-6 h-6 text-green-600 mr-3 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="text-lg font-semibold text-green-900">✅ 연결됨</h3>
                  <div className="mt-3 space-y-2 text-sm text-green-800">
                    {sessionStatus.username && (
                      <p><span className="font-medium">계정:</span> {sessionStatus.username}</p>
                    )}
                    {sessionStatus.created_at && (
                      <p><span className="font-medium">연결 일시:</span> {formatDate(sessionStatus.created_at)}</p>
                    )}
                    {sessionStatus.remaining_days !== undefined && (
                      <p>
                        <span className="font-medium">유효 기간:</span>{' '}
                        {sessionStatus.is_expired ? (
                          <span className="text-red-600 font-semibold">만료됨</span>
                        ) : sessionStatus.remaining_days === 0 ? (
                          <span className="text-orange-600 font-semibold">오늘 만료</span>
                        ) : (
                          <span>{sessionStatus.remaining_days}일 남음</span>
                        )}
                      </p>
                    )}
                    <p><span className="font-medium">쿠키:</span> {sessionStatus.cookie_count || 0}개</p>
                  </div>
                </div>
              </div>
              <button
                onClick={handleDeleteSession}
                disabled={loading}
                className="text-red-600 hover:text-red-700 hover:bg-red-50 p-2 rounded-lg transition-colors"
                title="세션 삭제"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
            
            {sessionStatus.is_expired && (
              <div className="mt-4 p-3 bg-orange-100 border border-orange-200 rounded-md">
                <p className="text-sm text-orange-800">
                  ⚠️ 세션이 만료되었습니다. 아래에서 세션을 다시 생성해주세요.
                </p>
              </div>
            )}
            
            <div className="mt-4 flex space-x-2">
              <button
                onClick={() => navigate('/dashboard')}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
              >
                📋 네이버 리뷰 보기
              </button>
              <button
                onClick={checkSessionStatus}
                disabled={loading}
                className="bg-white hover:bg-gray-50 text-green-600 border border-green-600 font-medium py-2 px-4 rounded-lg transition-colors flex items-center"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 border-2 border-gray-200 rounded-lg p-6 mb-6">
            <div className="flex items-start">
              <XCircle className="w-6 h-6 text-gray-400 mr-3 mt-1 flex-shrink-0" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">세션 없음</h3>
                <p className="text-sm text-gray-600 mt-1">
                  네이버 스마트플레이스와 연결하려면 세션을 생성해야 합니다.
                </p>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start">
            <AlertCircle className="w-5 h-5 text-red-500 mr-3 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-800">오류</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Download Tool Section */}
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">💻 세션 생성 도구</h3>
          <p className="text-sm text-gray-700 mb-4">
            Windows PC에서 실행하는 간단한 프로그램입니다. 자동으로 네이버 로그인 후 세션을 생성합니다.
          </p>
          
          <div className="bg-white rounded-lg p-4 mb-4 space-y-2 text-sm text-gray-600">
            <div className="flex items-start">
              <span className="font-bold text-indigo-600 mr-2">1.</span>
              <span>도구를 다운로드합니다</span>
            </div>
            <div className="flex items-start">
              <span className="font-bold text-indigo-600 mr-2">2.</span>
              <span>실행 후 네이버 계정 정보를 입력합니다</span>
            </div>
            <div className="flex items-start">
              <span className="font-bold text-indigo-600 mr-2">3.</span>
              <span>브라우저가 자동으로 열리고 2단계 인증을 완료합니다</span>
            </div>
            <div className="flex items-start">
              <span className="font-bold text-indigo-600 mr-2">4.</span>
              <span>세션이 자동으로 서버에 업로드됩니다 (완료!)</span>
            </div>
          </div>
          
          <button
            onClick={handleDownloadTool}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors"
          >
            <Download className="w-5 h-5" />
            <span>세션 생성 도구 다운로드 (Windows)</span>
          </button>
          
          <p className="text-xs text-gray-500 mt-3 text-center">
            파일 크기: 약 25MB | Windows 10 이상 | Chrome 자동 설치
          </p>
        </div>

        {/* Help Guide Button */}
        <button
          onClick={() => setShowGuide(!showGuide)}
          className="w-full bg-white hover:bg-gray-50 border-2 border-gray-200 text-gray-700 font-medium py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors mb-6"
        >
          <HelpCircle className="w-5 h-5" />
          <span>{showGuide ? '가이드 닫기' : '자세한 사용 가이드 보기'}</span>
        </button>

        {/* Detailed Guide */}
        {showGuide && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">📚 상세 가이드</h3>
            
            <div className="space-y-4 text-sm text-blue-900">
              <div>
                <h4 className="font-semibold mb-2">🔐 보안</h4>
                <ul className="list-disc list-inside space-y-1 text-blue-800">
                  <li>비밀번호는 로그인 시에만 사용되고 저장되지 않습니다</li>
                  <li>세션 데이터는 암호화되어 MongoDB에 안전하게 저장됩니다</li>
                  <li>HTTPS로 모든 통신이 암호화됩니다</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">⏰ 세션 유효 기간</h4>
                <ul className="list-disc list-inside space-y-1 text-blue-800">
                  <li>생성된 세션은 약 7일간 유효합니다</li>
                  <li>만료 1일 전에 알림을 받게 됩니다</li>
                  <li>만료 시 도구를 다시 실행하여 갱신하세요</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">❓ 문제 해결</h4>
                <ul className="list-disc list-inside space-y-1 text-blue-800">
                  <li>Windows Defender 경고: "추가 정보" → "실행" 클릭</li>
                  <li>2단계 인증: 2분 내에 휴대폰에서 인증 완료</li>
                  <li>실패 시: 프로그램을 다시 실행해보세요</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Warning */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <Info className="w-5 h-5 text-yellow-600 mr-3 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-yellow-900">⚠️ 주의사항</h3>
              <p className="text-xs text-yellow-800 mt-1">
                네이버는 공식 리뷰 관리 API를 제공하지 않습니다. 
                이 기능은 웹 자동화를 사용하며, <strong>개인 사용 목적으로만</strong> 사용하시기 바랍니다.
              </p>
            </div>
          </div>
        </div>

        {/* Back Button */}
        <div className="text-center">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← 대시보드로 돌아가기
          </button>
        </div>
      </div>
    </div>
  )
}




