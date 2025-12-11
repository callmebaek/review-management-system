import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'
import { Store, MessageSquare, Star, AlertCircle, CheckCircle, LogOut, Plus } from 'lucide-react'

export default function Dashboard() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [showAuthSuccess, setShowAuthSuccess] = useState(false)
  const [showNaverAuthSuccess, setShowNaverAuthSuccess] = useState(false)

  useEffect(() => {
    if (searchParams.get('auth') === 'success') {
      setShowAuthSuccess(true)
      setTimeout(() => setShowAuthSuccess(false), 3000)
    }
    if (searchParams.get('naver_auth') === 'success') {
      setShowNaverAuthSuccess(true)
      setTimeout(() => setShowNaverAuthSuccess(false), 3000)
    }
  }, [searchParams])

  // Check auth status (Mock 모드에서는 항상 통과)
  const { data: authStatus, isLoading: authLoading } = useQuery({
    queryKey: ['authStatus'],
    queryFn: async () => {
      // Mock 모드: localStorage에 로그인 정보가 있으면 바로 통과
      const isLoggedIn = localStorage.getItem('user_logged_in')
      if (!isLoggedIn) {
        navigate('/login')
        return { authenticated: false }
      }
      
      // Mock 모드에서는 API 호출 없이 바로 진행
      return { authenticated: true, mock: true }
    },
    retry: false  // Don't retry on failure
  })

  // Fetch accounts
  const { data: accounts, isLoading: accountsLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/gbp/accounts')
        return response.data
      } catch (err) {
        console.error('Failed to fetch accounts:', err)
        return []  // Return empty array on error (Mock mode)
      }
    },
    enabled: !!authStatus?.authenticated,
    retry: false
  })

  // Fetch locations
  const { data: locations, isLoading: locationsLoading } = useQuery({
    queryKey: ['locations'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/gbp/locations')
        return response.data
      } catch (err) {
        console.error('Failed to fetch locations:', err)
        return []  // Return empty array on error (Mock mode)
      }
    },
    enabled: !!authStatus?.authenticated,
    retry: false
  })

  // Check Naver login status
  const { data: naverStatus } = useQuery({
    queryKey: ['naverStatus'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/naver/status')
        return response.data
      } catch (err) {
        console.error('Failed to check Naver status:', err)
        return { logged_in: false, message: 'Not logged in' }
      }
    },
    retry: false
  })

  // Fetch Naver places if logged in
  const { data: naverPlaces, isLoading: naverPlacesLoading } = useQuery({
    queryKey: ['naverPlaces'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/naver/places')
        return response.data
      } catch (err) {
        console.error('Failed to fetch Naver places:', err)
        return []  // Return empty array on error
      }
    },
    enabled: !!naverStatus?.logged_in,
    retry: false,
    staleTime: 5 * 60 * 1000 // Cache for 5 minutes
  })

  const handleLogout = async () => {
    try {
      localStorage.removeItem('user_logged_in')
      await apiClient.post('/auth/logout')
      navigate('/login')
    } catch (err) {
      console.error('Logout error:', err)
      // Mock 모드: 에러가 나도 로그아웃
      localStorage.removeItem('user_logged_in')
      navigate('/login')
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">리뷰 관리 시스템</h1>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/settings')}
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                설정
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                <LogOut className="w-4 h-4" />
                <span>로그아웃</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Success Banners */}
      {showAuthSuccess && (
        <div className="bg-green-50 border-b border-green-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex items-center">
              <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
              <p className="text-sm text-green-800">Google 계정 연결이 완료되었습니다!</p>
            </div>
          </div>
        </div>
      )}
      
      {showNaverAuthSuccess && (
        <div className="bg-green-50 border-b border-green-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex items-center">
              <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
              <p className="text-sm text-green-800">네이버 플레이스 연결이 완료되었습니다!</p>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Platform Connection Status */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Google Business Profile */}
          {accounts && accounts.length > 0 ? (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start">
                  <CheckCircle className="w-5 h-5 text-blue-600 mr-3 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-medium text-blue-900">Google Business Profile</h3>
                    <p className="text-sm text-blue-700 mt-1">
                      {accounts[0].account_name} - 매장 {locations?.length || 0}개
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start">
                  <div className="w-5 h-5 mr-3 mt-0.5 flex items-center justify-center">
                    <span className="text-xl">🚀</span>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-blue-900">Google Business Profile</h3>
                    <p className="text-sm text-blue-700 mt-1 font-semibold">
                      구글 비즈니스 프로필 리뷰 관리 시스템 커밍순!! 기대해주세요! 🎉
                    </p>
                    <p className="text-xs text-blue-600 mt-2">
                      Google API 승인 심사 중입니다
                    </p>
                  </div>
                </div>
                <button
                  disabled
                  className="flex items-center space-x-2 bg-gray-300 text-gray-500 px-4 py-2 rounded-md text-sm font-medium cursor-not-allowed opacity-60"
                  title="Google API 승인 대기 중"
                >
                  <Plus className="w-4 h-4" />
                  <span>연결하기</span>
                </button>
              </div>
            </div>
          )}

          {/* Naver Place */}
          {naverStatus?.logged_in ? (
            naverPlacesLoading ? (
              // 🚀 Loading state with progress indicator
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-yellow-600 mr-3"></div>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-yellow-900">네이버 플레이스</h3>
                    <p className="text-sm text-yellow-700 mt-1">
                      매장 정보 불러오는 중...
                    </p>
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs text-yellow-600 mb-1">
                        <span>⏱️ 예상 대기 시간: 약 10초</span>
                      </div>
                      <div className="w-full bg-yellow-200 rounded-full h-1.5 overflow-hidden">
                        <div className="bg-yellow-600 h-1.5 rounded-full animate-pulse" style={{width: '100%'}}></div>
                      </div>
                    </div>
                    <p className="text-xs text-yellow-600 mt-2">
                      💡 첫 로딩 시 팝업 처리 및 세션 확인 중입니다...
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-600 mr-3 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-medium text-green-900">네이버 플레이스</h3>
                      <p className="text-sm text-green-700 mt-1">
                        연결됨 (세션 저장) - 매장 {naverPlaces?.length || 0}개
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={async () => {
                      try {
                        await apiClient.post('/api/naver/logout')
                        window.location.reload()
                      } catch (err) {
                        console.error('Logout error:', err)
                      }
                    }}
                    className="text-xs text-green-600 hover:text-green-700 underline"
                  >
                    연결 해제
                  </button>
                </div>
              </div>
            )
          ) : (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start">
                  <AlertCircle className="w-5 h-5 text-gray-400 mr-3 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">네이버 플레이스</h3>
                    <p className="text-sm text-gray-600 mt-1">연결되지 않음 (최초 1회 로그인 필요)</p>
                  </div>
                </div>
                <button
                  onClick={() => navigate('/naver-login')}
                  className="flex items-center text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  연결
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Locations Grid */}
        {((locations && locations.length > 0) || (naverPlaces && naverPlaces.length > 0)) ? (
          <>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">매장 목록</h2>
            
            {/* Google Business Profile Locations */}
            {locations && locations.length > 0 && (
              <>
                <h3 className="text-sm font-medium text-gray-600 mb-3">Google Business Profile</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                  {locations.map((location) => (
                    <div
                      key={location.name}
                      className="bg-white rounded-lg shadow-sm border border-blue-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => navigate(`/reviews?platform=gbp&location=${encodeURIComponent(location.name)}`)}
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center">
                          <Store className="w-6 h-6 text-blue-600 mr-3" />
                          <h3 className="text-lg font-semibold text-gray-900">{location.location_name}</h3>
                        </div>
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">GBP</span>
                      </div>

                      {location.address && (
                        <p className="text-sm text-gray-600 mb-2">{location.address}</p>
                      )}

                      {location.phone && (
                        <p className="text-sm text-gray-600 mb-4">{location.phone}</p>
                      )}

                      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                        <button className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center">
                          <MessageSquare className="w-4 h-4 mr-1" />
                          리뷰 관리
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* Naver Place Locations */}
            {naverStatus?.logged_in && (
              naverPlacesLoading ? (
                // 🚀 Loading skeleton for Naver places
                <>
                  <h3 className="text-sm font-medium text-gray-600 mb-3">네이버 플레이스</h3>
                  <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-8 text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600 mx-auto mb-4"></div>
                    <h4 className="text-lg font-medium text-yellow-900 mb-2">매장 정보 불러오는 중...</h4>
                    <p className="text-sm text-yellow-700">
                      스마트플레이스에서 매장 데이터를 가져오고 있습니다.
                    </p>
                    <p className="text-xs text-yellow-600 mt-2">
                      ⏱️ 약 10초 정도 소요됩니다
                    </p>
                  </div>
                </>
              ) : naverPlaces && naverPlaces.length > 0 ? (
                <>
                  <h3 className="text-sm font-medium text-gray-600 mb-3">네이버 플레이스</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {naverPlaces.map((place) => (
                      <div
                        key={place.place_id}
                        className="bg-white rounded-lg shadow-sm border border-green-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => navigate(`/reviews?platform=naver&place_id=${encodeURIComponent(place.place_id)}`)}
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center">
                            <Store className="w-6 h-6 text-green-600 mr-3" />
                            <h3 className="text-lg font-semibold text-gray-900">{place.name}</h3>
                          </div>
                          <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">네이버</span>
                        </div>

                        {place.address && (
                          <p className="text-sm text-gray-600 mb-2">{place.address}</p>
                        )}

                        {place.category && (
                          <p className="text-sm text-gray-500 mb-4">{place.category}</p>
                        )}

                        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                          <button className="text-green-600 hover:text-green-700 text-sm font-medium flex items-center">
                            <MessageSquare className="w-4 h-4 mr-1" />
                            리뷰 관리
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : null
            )}
          </>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">매장이 없습니다</h3>
            <p className="text-gray-600 mb-6">
              Google Business Profile 또는 네이버 플레이스에<br />
              등록된 매장이 없거나 계정에 접근 권한이 없습니다.
            </p>
            <div className="flex items-center justify-center space-x-4">
              <button
                onClick={() => window.open('https://business.google.com', '_blank')}
                className="inline-flex items-center px-4 py-2 border border-blue-600 text-blue-600 rounded-md hover:bg-blue-50"
              >
                GBP 관리
              </button>
              <button
                onClick={() => navigate('/naver-login')}
                className="inline-flex items-center px-4 py-2 border border-green-600 text-green-600 rounded-md hover:bg-green-50"
              >
                네이버 연결
              </button>
            </div>
          </div>
        )}

        {/* Quick Stats */}
        {locations && locations.length > 0 && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Store className="w-6 h-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">총 매장</p>
                  <p className="text-2xl font-semibold text-gray-900">{locations.length}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-3 bg-green-100 rounded-lg">
                  <MessageSquare className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">총 리뷰</p>
                  <p className="text-2xl font-semibold text-gray-900">-</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-3 bg-yellow-100 rounded-lg">
                  <Star className="w-6 h-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">평균 평점</p>
                  <p className="text-2xl font-semibold text-gray-900">-</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

