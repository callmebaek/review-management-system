import React, { useState, useEffect } from 'react'
import { X, Save, RotateCcw } from 'lucide-react'
import apiClient from '../api/client'

export default function AISettingsModal({ isOpen, onClose, placeId, placeName }) {
  const [activeTab, setActiveTab] = useState('basic')
  const [settings, setSettings] = useState({
    friendliness: 7,
    formality: 7,
    reply_length_min: 100,
    reply_length_max: 450,
    diversity: 0.9,
    use_text_emoticons: true,
    mention_specifics: true,
    brand_voice: 'warm',
    response_style: 'quick_thanks',
    custom_instructions: '',
    custom_instructions_negative: ''
  })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [isDefault, setIsDefault] = useState(true)

  // Load settings when modal opens
  useEffect(() => {
    if (isOpen && placeId) {
      loadSettings()
    }
  }, [isOpen, placeId])

  const loadSettings = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get(`/api/naver/places/${placeId}/ai-settings`)
      setSettings(response.data.settings)
      setIsDefault(response.data.is_default || false)
    } catch (error) {
      console.error('Failed to load AI settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      
      // Validate required fields
      const minLength = typeof settings.reply_length_min === 'number' ? settings.reply_length_min : parseInt(settings.reply_length_min) || 50
      const maxLength = typeof settings.reply_length_max === 'number' ? settings.reply_length_max : parseInt(settings.reply_length_max) || 1200
      
      if (minLength > maxLength) {
        alert('❌ 최소 길이가 최대 길이보다 클 수 없습니다.')
        return
      }
      
      if (minLength < 50 || minLength > 1200) {
        alert('❌ 최소 길이는 50~1200자 사이여야 합니다.')
        return
      }
      
      if (maxLength < 50 || maxLength > 1200) {
        alert('❌ 최대 길이는 50~1200자 사이여야 합니다.')
        return
      }
      
      // 실제 숫자 값으로 변환하여 저장
      const validatedSettings = {
        ...settings,
        reply_length_min: minLength,
        reply_length_max: maxLength
      }
      
      console.log('💾 Saving settings:', validatedSettings)
      const response = await apiClient.put(`/api/naver/places/${placeId}/ai-settings`, validatedSettings)
      console.log('✅ Save response:', response.data)
      
      alert('✅ AI 답글 설정이 저장되었습니다!')
      setIsDefault(false)
      onClose()
    } catch (error) {
      console.error('Failed to save AI settings:', error)
      
      // 더 자세한 에러 메시지 표시
      let errorMessage = '❌ 설정 저장에 실패했습니다.\n\n'
      
      if (error.response?.data?.detail) {
        errorMessage += `원인: ${error.response.data.detail}\n\n`
      } else if (error.response?.status === 401) {
        errorMessage += '로그인이 필요합니다.\n\n'
      } else if (error.response?.status === 500) {
        errorMessage += '서버 오류가 발생했습니다.\nMongoDB 연결을 확인해주세요.\n\n'
      } else {
        errorMessage += `오류: ${error.message}\n\n`
      }
      
      errorMessage += '다시 시도해주세요.'
      alert(errorMessage)
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    if (confirm('기본 설정으로 되돌리시겠습니까?')) {
      setSettings({
        friendliness: 7,
        formality: 7,
        reply_length_min: 100,
        reply_length_max: 450,
        diversity: 0.9,
        use_text_emoticons: true,
        mention_specifics: true,
        brand_voice: 'warm',
        response_style: 'quick_thanks',
        custom_instructions: '',
        custom_instructions_negative: ''
      })
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl my-4 sm:my-8 flex flex-col" style={{ maxHeight: 'calc(100vh - 2rem)' }}>
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between flex-shrink-0">
          <div className="flex-1 min-w-0">
            <h2 className="text-lg sm:text-xl font-bold text-white truncate">AI 답글 생성 설정</h2>
            <p className="text-purple-100 text-xs sm:text-sm mt-1">
              {placeName ? (
                <>
                  <span className="font-semibold">{placeName}</span>
                  <span className="text-purple-200 ml-1 sm:ml-2 hidden sm:inline">(ID: {placeId})</span>
                </>
              ) : (
                <span>매장 ID: {placeId}</span>
              )}
            </p>
            {isDefault && (
              <span className="inline-block mt-1 sm:mt-2 px-2 py-1 bg-yellow-400 text-yellow-900 text-xs rounded font-medium">
                기본값 사용 중
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 p-1.5 sm:p-2 rounded-lg transition flex-shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 px-2 sm:px-6 flex-shrink-0 overflow-x-auto">
          <div className="flex space-x-1 min-w-max">
            <button
              onClick={() => setActiveTab('basic')}
              className={`px-3 sm:px-4 py-2 sm:py-3 font-medium text-xs sm:text-sm border-b-2 transition whitespace-nowrap ${
                activeTab === 'basic'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              기본 설정
            </button>
            <button
              onClick={() => setActiveTab('advanced')}
              className={`px-3 sm:px-4 py-2 sm:py-3 font-medium text-xs sm:text-sm border-b-2 transition whitespace-nowrap ${
                activeTab === 'advanced'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              고급 설정
            </button>
            <button
              onClick={() => setActiveTab('custom')}
              className={`px-3 sm:px-4 py-2 sm:py-3 font-medium text-xs sm:text-sm border-b-2 transition whitespace-nowrap ${
                activeTab === 'custom'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              일반 요청사항
            </button>
            <button
              onClick={() => setActiveTab('negative')}
              className={`px-3 sm:px-4 py-2 sm:py-3 font-medium text-xs sm:text-sm border-b-2 transition whitespace-nowrap ${
                activeTab === 'negative'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              부정 리뷰 대응
            </button>
          </div>
        </div>

        {/* Content - 스크롤 가능 영역 */}
        <div className="px-4 sm:px-6 py-4 sm:py-6 overflow-y-auto flex-1">
          {loading ? (
            <div className="flex items-center justify-center py-8 sm:py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
          ) : (
            <>
              {/* Basic Settings Tab */}
              {activeTab === 'basic' && (
                <div className="space-y-4 sm:space-y-6">
                  {/* Friendliness */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      친절함 정도 <span className="text-purple-600 font-bold">{settings.friendliness}</span>/10
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={settings.friendliness}
                      onChange={(e) => setSettings({ ...settings, friendliness: parseInt(e.target.value) })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>정중하게</span>
                      <span>친절하게</span>
                      <span>매우 따뜻하게</span>
                    </div>
                  </div>

                  {/* Formality */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      격식 수준 <span className="text-purple-600 font-bold">{settings.formality}</span>/10
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={settings.formality}
                      onChange={(e) => setSettings({ ...settings, formality: parseInt(e.target.value) })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>반말</span>
                      <span>자연스러운 존댓말</span>
                      <span>격식있는 존댓말</span>
                    </div>
                  </div>

                  {/* Reply Length */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      답글 길이 <span className="text-red-500">*</span>
                    </label>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          최소 <span className="text-gray-400">(50-1200자)</span>
                        </label>
                        <input
                          type="number"
                          min="50"
                          max="1200"
                          step="10"
                          required
                          value={settings.reply_length_min}
                          onChange={(e) => {
                            // onChange에서는 범위 제한 없이 자유롭게 입력 가능
                            const value = e.target.value
                            if (value === '' || !isNaN(parseInt(value))) {
                              setSettings({ ...settings, reply_length_min: value === '' ? '' : parseInt(value) })
                            }
                          }}
                          onBlur={(e) => {
                            // 포커스 아웃 시에만 범위 제한 적용
                            let value = parseInt(e.target.value)
                            if (isNaN(value) || value < 50) {
                              value = 50
                            } else if (value > 1200) {
                              value = 1200
                            }
                            setSettings({ ...settings, reply_length_min: value })
                          }}
                          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent ${
                            (parseInt(settings.reply_length_min) || 0) > (parseInt(settings.reply_length_max) || 9999) ? 'border-red-500' : 'border-gray-300'
                          }`}
                          placeholder="50"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">
                          최대 <span className="text-gray-400">(50-1200자)</span>
                        </label>
                        <input
                          type="number"
                          min="50"
                          max="1200"
                          step="10"
                          required
                          value={settings.reply_length_max}
                          onChange={(e) => {
                            // onChange에서는 범위 제한 없이 자유롭게 입력 가능
                            const value = e.target.value
                            if (value === '' || !isNaN(parseInt(value))) {
                              setSettings({ ...settings, reply_length_max: value === '' ? '' : parseInt(value) })
                            }
                          }}
                          onBlur={(e) => {
                            // 포커스 아웃 시에만 범위 제한 적용
                            let value = parseInt(e.target.value)
                            if (isNaN(value) || value < 50) {
                              value = 50
                            } else if (value > 1200) {
                              value = 1200
                            }
                            setSettings({ ...settings, reply_length_max: value })
                          }}
                          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent ${
                            (parseInt(settings.reply_length_min) || 0) > (parseInt(settings.reply_length_max) || 9999) ? 'border-red-500' : 'border-gray-300'
                          }`}
                          placeholder="1200"
                        />
                      </div>
                    </div>
                    {(() => {
                      const min = parseInt(settings.reply_length_min) || 0
                      const max = parseInt(settings.reply_length_max) || 0
                      if (min > 0 && max > 0 && min > max) {
                        return (
                          <p className="text-xs text-red-600 mt-1 font-medium">
                            ⚠️ 최소 길이가 최대 길이보다 클 수 없습니다
                          </p>
                        )
                      }
                      return (
                        <p className="text-xs text-gray-500 mt-1">
                          {settings.reply_length_min || 50}~{settings.reply_length_max || 1200}자 범위로 답글이 생성됩니다
                        </p>
                      )
                    })()}
                  </div>

                  {/* Text Emoticons Toggle */}
                  <div className="flex items-center justify-between p-3 sm:p-4 bg-gray-50 rounded-lg">
                    <div className="flex-1 min-w-0 mr-3">
                      <label className="block text-sm font-medium text-gray-700">
                        텍스트 이모티콘 사용
                      </label>
                      <p className="text-xs text-gray-500 mt-1">^^, ㅎㅎ, :) 등</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                      <input
                        type="checkbox"
                        checked={settings.use_text_emoticons}
                        onChange={(e) => setSettings({ ...settings, use_text_emoticons: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                    </label>
                  </div>

                  {/* Mention Specifics Toggle */}
                  <div className="flex items-center justify-between p-3 sm:p-4 bg-gray-50 rounded-lg">
                    <div className="flex-1 min-w-0 mr-3">
                      <label className="block text-sm font-medium text-gray-700">
                        리뷰 구체 내용 언급
                      </label>
                      <p className="text-xs text-gray-500 mt-1">맛, 분위기, 서비스 등</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                      <input
                        type="checkbox"
                        checked={settings.mention_specifics}
                        onChange={(e) => setSettings({ ...settings, mention_specifics: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                    </label>
                  </div>
                </div>
              )}

              {/* Advanced Settings Tab */}
              {activeTab === 'advanced' && (
                <div className="space-y-4 sm:space-y-6">
                  {/* Diversity */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      다양성 강도 <span className="text-purple-600 font-bold">{settings.diversity.toFixed(1)}</span>
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="1.0"
                      step="0.1"
                      value={settings.diversity}
                      onChange={(e) => setSettings({ ...settings, diversity: parseFloat(e.target.value) })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>일관적</span>
                      <span>균형</span>
                      <span>창의적</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-2 bg-blue-50 p-2 rounded">
                      💡 높을수록 매번 다른 스타일의 답글이 생성됩니다
                    </p>
                  </div>

                  {/* Brand Voice */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      브랜드 톤
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-2 gap-2 sm:gap-3">
                      {[
                        { value: 'warm', label: '따뜻한', emoji: '🤗' },
                        { value: 'professional', label: '전문적인', emoji: '💼' },
                        { value: 'casual', label: '캐주얼한', emoji: '😎' },
                        { value: 'friendly', label: '친근한', emoji: '😊' }
                      ].map((option) => (
                        <button
                          key={option.value}
                          onClick={() => setSettings({ ...settings, brand_voice: option.value })}
                          className={`p-2 sm:p-3 border-2 rounded-lg transition ${
                            settings.brand_voice === option.value
                              ? 'border-purple-600 bg-purple-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <div className="text-xl sm:text-2xl mb-1">{option.emoji}</div>
                          <div className="text-xs sm:text-sm font-medium">{option.label}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Response Style */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      응답 스타일
                    </label>
                    <div className="space-y-2">
                      {[
                        { value: 'quick_thanks', label: '신속한 감사', desc: '빠르게 감사 표현' },
                        { value: 'empathy', label: '공감 중심', desc: '고객의 경험에 공감' },
                        { value: 'solution', label: '해결책 제시', desc: '개선 의지 표현' }
                      ].map((option) => (
                        <label
                          key={option.value}
                          className={`flex items-start sm:items-center p-2.5 sm:p-3 border-2 rounded-lg cursor-pointer transition ${
                            settings.response_style === option.value
                              ? 'border-purple-600 bg-purple-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <input
                            type="radio"
                            name="response_style"
                            value={option.value}
                            checked={settings.response_style === option.value}
                            onChange={(e) => setSettings({ ...settings, response_style: e.target.value })}
                            className="mr-2 sm:mr-3 mt-0.5 sm:mt-0 text-purple-600 focus:ring-purple-500 flex-shrink-0"
                          />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-xs sm:text-sm">{option.label}</div>
                            <div className="text-xs text-gray-500 mt-0.5">{option.desc}</div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Custom Instructions Tab - 일반 */}
              {activeTab === 'custom' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    일반 리뷰 답글 추가 요청사항
                  </label>
                  <textarea
                    value={settings.custom_instructions}
                    onChange={(e) => setSettings({ ...settings, custom_instructions: e.target.value })}
                    placeholder="예시:&#10;- 우리 매장은 사진관이므로 '추억', '순간' 같은 감성적인 단어를 사용해주세요&#10;- 가족 단위 고객이 많으므로 따뜻한 톤을 유지해주세요&#10;- 재방문 시 할인 쿠폰이 있다고 안내해주세요"
                    rows="8"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none text-sm"
                    style={{ minHeight: '200px' }}
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    💡 일반적인 리뷰(긍정/중립)에 대한 답글 작성 시 반영할 내용을 작성하세요.
                  </p>
                </div>
              )}

              {/* Custom Instructions Tab - 부정 리뷰 */}
              {activeTab === 'negative' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    부정 리뷰 답글 추가 요청사항
                  </label>
                  <textarea
                    value={settings.custom_instructions_negative}
                    onChange={(e) => setSettings({ ...settings, custom_instructions_negative: e.target.value })}
                    placeholder="예시:&#10;- 구체적인 불편 사항에 대해 진심으로 사과하고 개선 의지를 표현해주세요&#10;- 직접 연락 가능한 채널(전화번호, 카카오톡)을 안내해주세요&#10;- 보상이나 재방문 혜택을 제안해주세요&#10;- 과도한 변명보다는 공감과 해결 의지를 우선해주세요"
                    rows="8"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none text-sm"
                    style={{ minHeight: '200px' }}
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    🔥 부정적인 리뷰(1-2점)에 대한 답글 작성 시 반영할 내용을 작성하세요. 더 신중하고 진정성 있는 대응이 필요합니다.
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer - 항상 보이는 버튼 영역 */}
        <div className="border-t border-gray-200 px-4 sm:px-6 py-3 sm:py-4 bg-gray-50 flex-shrink-0">
          <div className="flex flex-col-reverse sm:flex-row items-stretch sm:items-center justify-between gap-2 sm:gap-0">
            {/* 기본값으로 되돌리기 - 모바일에서는 작게 */}
            <button
              onClick={handleReset}
              className="flex items-center justify-center space-x-2 px-3 sm:px-4 py-2 text-gray-600 hover:text-gray-800 transition text-sm"
            >
              <RotateCcw className="w-4 h-4" />
              <span className="hidden sm:inline">기본값으로 되돌리기</span>
              <span className="sm:hidden">기본값</span>
            </button>
            
            {/* 취소/저장 버튼 */}
            <div className="flex items-center gap-2 sm:gap-3">
              <button
                onClick={onClose}
                className="flex-1 sm:flex-none px-4 py-2 text-gray-600 hover:text-gray-800 transition font-medium text-sm"
              >
                취소
              </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 sm:flex-none flex items-center justify-center space-x-2 px-4 sm:px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? '저장 중...' : '저장'}</span>
            </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

