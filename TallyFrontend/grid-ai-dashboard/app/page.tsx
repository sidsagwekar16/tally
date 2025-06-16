"use client"
import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabaseClient"
import LoginForm from "@/components/login"
import SignupForm from "@/components/signup-form"
import { GridAIDashboard } from "@/components/grid-ai-dashboard"

export default function Home() {
  const [loggedIn, setLoggedIn] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showSignup, setShowSignup] = useState(false)

  useEffect(() => {
    const checkSession = async () => {
      const { data } = await supabase.auth.getSession()
      console.log("[checkSession] Session data:", data)
      setLoggedIn(!!data.session)
      setLoading(false)
    }
    checkSession()
    const { data: listener } = supabase.auth.onAuthStateChange((event, session) => {
      console.log("[onAuthStateChange] Event:", event, "Session:", session)
      setLoggedIn(!!session)
    })
    return () => {
      console.log("[CLEANUP] Unsubscribing auth state listener")
      listener?.subscription.unsubscribe()
    }
  }, [])

  useEffect(() => {
    console.log("[STATE] loggedIn:", loggedIn, "loading:", loading, "showSignup:", showSignup)
  }, [loggedIn, loading, showSignup])

  if (loading) {
    console.log("[RENDER] Loading...")
    return null
  }

  if (loggedIn) {
    console.log("[RENDER] Logged in, rendering dashboard")
    return <GridAIDashboard />
  }

  console.log("[RENDER] Showing login/signup form, showSignup:", showSignup)
  return (
    <div className="flex justify-center items-center min-h-screen">
      {showSignup ? (
        <SignupForm onSwitchToLogin={() => {
          console.log("[ACTION] Switching to login form")
          setShowSignup(false)
        }} />
      ) : (
        <LoginForm
          onLogin={async () => {
            console.log("[ACTION] LoginForm onLogin called, re-checking session...")
            const { data } = await supabase.auth.getSession()
            console.log("[ACTION] Fetched session after login:", data)
            setLoggedIn(!!data.session)
          }}
          onSwitchToSignup={() => {
            console.log("[ACTION] Switching to signup form")
            setShowSignup(true)
          }}
        />
      )}
    </div>
  )
}
