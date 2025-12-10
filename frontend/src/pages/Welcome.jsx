import React from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, Settings, Key, FileText } from 'lucide-react'

export default function Welcome() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="max-w-6xl mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            리뷰 관리 시스템
          </h1>
          <p className="text-xl text-gray-600">
            Google Business Profile & 네이버 플레이스 리뷰 통합 관리
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          <div className="bg-white rounded-xl shadow-md p-8 border-2 border-blue-100 hover:border-blue-300 transition-colors">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                <CheckCircle className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900">Google Business Profile</h3>
            </div>
            <ul className="space-y-2 text-gray-600">
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">✓</span>
                OAuth 2.0 인증으로 안전한 연결
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">✓</span>
                리뷰 조회 및 필터링 (미답변/답변완료)
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">✓</span>
                AI 답글 자동 생성 (GPT-4)
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">✓</span>
                답글 게시 및 관리
              </li>
            </ul>
          </div>

          <div className="bg-white rounded-xl shadow-md p-8 border-2 border-green-100 hover:border-green-300 transition-colors">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mr-4">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900">네이버 플레이스</h3>
            </div>
            <ul className="space-y-2 text-gray-600">
              <li className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                스마트플레이스 센터 연동
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                리뷰 자동 크롤링
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                AI 답글 자동 생성
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                답글 자동 게시
              </li>
            </ul>
          </div>
        </div>

        {/* Setup Steps */}
        <div className="bg-white rounded-xl shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <Settings className="w-6 h-6 mr-2 text-blue-600" />
            시작하기
          </h2>
          
          <div className="space-y-6">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                1
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-2">환경 변수 설정</h3>
                <p className="text-gray-600 mb-2">
                  프로젝트 루트에 <code className="bg-gray-100 px-2 py-1 rounded text-sm">.env</code> 파일을 생성하고 API 키를 입력하세요.
                </p>
                <pre className="bg-gray-50 p-3 rounded text-xs overflow-x-auto">
{`GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
OPENAI_API_KEY=your_openai_api_key`}
                </pre>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                2
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-2">Google Cloud Console 설정</h3>
                <p className="text-gray-600">
                  Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하세요.
                </p>
                <a 
                  href="https://console.cloud.google.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center mt-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  Google Cloud Console 열기 →
                </a>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                3
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-2">OpenAI API 키 발급</h3>
                <p className="text-gray-600">
                  OpenAI Platform에서 API 키를 생성하세요.
                </p>
                <a 
                  href="https://platform.openai.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center mt-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  OpenAI Platform 열기 →
                </a>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                4
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-2">백엔드 서버 재시작</h3>
                <p className="text-gray-600">
                  환경 변수 설정 후 백엔드 서버를 재시작하세요.
                </p>
                <pre className="bg-gray-50 p-3 rounded text-xs overflow-x-auto mt-2">
{`cd backend
python -m backend.main`}
                </pre>
              </div>
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="text-center">
          <button
            onClick={() => navigate('/login')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-4 rounded-lg text-lg shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
          >
            로그인 페이지로 이동
          </button>
          
          <div className="mt-6 flex items-center justify-center space-x-4 text-sm text-gray-600">
            <a href="https://github.com" className="hover:text-blue-600 flex items-center">
              <FileText className="w-4 h-4 mr-1" />
              SETUP_GUIDE.md
            </a>
            <span>•</span>
            <a href="https://github.com" className="hover:text-blue-600 flex items-center">
              <FileText className="w-4 h-4 mr-1" />
              WINDOWS_SETUP.md
            </a>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-16 text-center text-sm text-gray-500">
          <p>🎉 모든 설정이 완료되면 Google 또는 네이버 계정으로 로그인하세요</p>
        </div>
      </div>
    </div>
  )
}







