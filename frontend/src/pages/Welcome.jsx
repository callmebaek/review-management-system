import React from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle } from 'lucide-react'

export default function Welcome() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 w-full">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-title font-black text-gray-900 mb-3 sm:mb-4 tracking-tight">
            리뷰 관리 시스템
          </h1>
          <p className="text-lg sm:text-xl lg:text-2xl text-gray-600 font-medium">
            Google Business Profile & 네이버 플레이스 리뷰 통합 관리
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid sm:grid-cols-2 gap-4 sm:gap-6 lg:gap-8 mb-8 sm:mb-12">
          <div className="bg-white rounded-xl shadow-md p-6 sm:p-8 border-2 border-blue-100 hover:border-blue-300 transition-all duration-300 hover:shadow-lg">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-blue-100 rounded-lg flex items-center justify-center mr-3 sm:mr-4 flex-shrink-0">
                <CheckCircle className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" />
              </div>
              <h3 className="text-lg sm:text-xl font-heading font-extrabold text-gray-900">Google Business Profile</h3>
            </div>
            <ul className="space-y-2 text-sm sm:text-base text-gray-600">
              <li className="flex items-start">
                <span className="text-blue-600 mr-2 flex-shrink-0">✓</span>
                <span>OAuth 2.0 인증으로 안전한 연결</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2 flex-shrink-0">✓</span>
                <span>리뷰 조회 및 필터링 (미답변/답변완료)</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2 flex-shrink-0">✓</span>
                <span>AI 답글 자동 생성 (GPT-4)</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2 flex-shrink-0">✓</span>
                <span>답글 게시 및 관리</span>
              </li>
            </ul>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 sm:p-8 border-2 border-green-100 hover:border-green-300 transition-all duration-300 hover:shadow-lg">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-green-100 rounded-lg flex items-center justify-center mr-3 sm:mr-4 flex-shrink-0">
                <CheckCircle className="w-5 h-5 sm:w-6 sm:h-6 text-green-600" />
              </div>
              <h3 className="text-lg sm:text-xl font-heading font-extrabold text-gray-900">네이버 플레이스</h3>
            </div>
            <ul className="space-y-2 text-sm sm:text-base text-gray-600">
              <li className="flex items-start">
                <span className="text-green-600 mr-2 flex-shrink-0">✓</span>
                <span>스마트플레이스 센터 연동</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-2 flex-shrink-0">✓</span>
                <span>리뷰 자동 크롤링</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-2 flex-shrink-0">✓</span>
                <span>AI 답글 자동 생성</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-2 flex-shrink-0">✓</span>
                <span>답글 자동 게시</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Action Button */}
        <div className="text-center">
          <button
            onClick={() => navigate('/login')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-8 sm:px-12 py-4 sm:py-5 rounded-xl text-lg sm:text-xl shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:scale-105 active:scale-95"
          >
            로그인 페이지로 이동
          </button>
          
          {/* Quote */}
          <div className="mt-8 sm:mt-10">
            <p className="text-base sm:text-lg lg:text-xl font-medium text-gray-600 italic">
              "시작은 동기, 완주(실행)는 습관이다."
            </p>
            <p className="text-xs sm:text-sm text-gray-400 mt-2">
              Motivation is what gets you started. Habit is what keeps you going.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}







