import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Welcome from './pages/Welcome'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Reviews from './pages/Reviews'
import Settings from './pages/Settings'
import NaverLogin from './pages/NaverLogin'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            <Route path="/" element={<Welcome />} />
            <Route path="/login" element={<Login />} />
            <Route path="/naver-login" element={<NaverLogin />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/reviews" element={<Reviews />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  )
}

export default App

