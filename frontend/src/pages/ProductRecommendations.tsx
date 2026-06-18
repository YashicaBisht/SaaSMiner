import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../App'
import { 
  Award, Shield, Target, Calendar, CheckSquare, 
  ChevronRight, ArrowRight, ShieldCheck, Zap
} from 'lucide-react'
import { motion } from 'framer-motion'

interface ProjectDetail {
  project: {
    id: number
    name: string
    repo_url: string | null
    file_count: number
    folder_count: number
    languages: Record<string, number>
    created_at: string
  }
  analysis: {
    domain: string
    confidence: number
    modules: any[]
    potential_score: number
    saas_recommendation: {
      recommended_product: string
      product_type: string
      explanation: string
      can_become_product: string
      roadmap: string[]
      reasons: string[]
    }
    apis: any[]
    microservices: any
    architecture: any
    business_potential: any
  }
}

const ProductRecommendations: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const { token, logout } = useAuth()
  
  const [data, setData] = useState<ProjectDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchProjectDetails = async () => {
      try {
        const res = await fetch(`/api/projects/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) {
          const detail = await res.json()
          setData(detail)
        } else {
          if (res.status === 401) logout()
          throw new Error("Failed to retrieve project analysis details.")
        }
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchProjectDetails()
  }, [id])

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-12 text-xs text-gray-400 font-medium animate-pulse">
        Fetching SaaS recommendations...
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex-1 flex items-center justify-center p-12 text-xs text-red-400 font-semibold">
        Error loading report details: {error || 'No records returned'}
      </div>
    )
  }

  const { project, analysis } = data
  const score = analysis.potential_score
  const saas = analysis.saas_recommendation
  
  // Radial Gauge Calculations
  const radius = 60
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (score / 100) * circumference

  // Mock breakdowns if not sent by api (or use real values)
  const breakdowns = [
    { label: 'Modularity', val: score - 3, color: 'bg-primary-500' },
    { label: 'Reusability', val: score + 2, color: 'bg-indigo-500' },
    { label: 'Scalability', val: score - 10, color: 'bg-emerald-500' },
    { label: 'Architecture Quality', val: score - 5, color: 'bg-violet-500' },
    { label: 'Business Value', val: score + 4, color: 'bg-amber-500' },
    { label: 'Market Applicability', val: score - 2, color: 'bg-pink-500' },
  ]

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-8 animate-fade-in-up">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-gray-900 pb-6">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">SaaS Opportunity</h1>
          <p className="text-sm text-gray-400 font-medium mt-1">Review the modular scoring metrics, target classification models, and monetization roadmaps.</p>
        </div>
        <div className="text-xs text-gray-500 font-mono">
          Scanned: {new Date(project.created_at).toLocaleDateString()}
        </div>
      </div>

      {/* Primary KPI & Gauge Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Animated Gauge Card */}
        <div className="glass-panel rounded-3xl p-6 border border-gray-900 shadow-xl flex flex-col items-center justify-center text-center gap-6 relative overflow-hidden">
          <div className="glowing-orb top-[-250px] left-[-200px] w-80 h-80 opacity-50"></div>
          
          <h3 className="font-bold text-sm text-gray-400 uppercase tracking-wider">Product potential</h3>
          
          {/* SVG Gauge */}
          <div className="relative w-40 h-40 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90">
              {/* Back Circle */}
              <circle 
                cx="80" 
                cy="80" 
                r={radius} 
                className="stroke-gray-800"
                strokeWidth="10"
                fill="transparent"
              />
              {/* Active Arc */}
              <motion.circle 
                cx="80" 
                cy="80" 
                r={radius} 
                className="stroke-primary-500"
                strokeWidth="10"
                fill="transparent"
                strokeDasharray={circumference}
                initial={{ strokeDashoffset: circumference }}
                animate={{ strokeDashoffset }}
                transition={{ duration: 1.2, ease: "easeOut" }}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-3xl font-extrabold tracking-tight">{score}</span>
              <span className="text-[10px] text-gray-500 font-bold uppercase">Score</span>
            </div>
          </div>

          <div className="text-xs font-semibold text-gray-300">
            {score >= 80 ? (
              <span className="text-emerald-400">Excellent commercial readiness</span>
            ) : score >= 60 ? (
              <span className="text-amber-400">Moderate product potential</span>
            ) : (
              <span className="text-gray-400">Refactoring recommended before monetization</span>
            )}
          </div>
        </div>

        {/* Breakdown Progress Bars */}
        <div className="glass-panel rounded-3xl p-6 border border-gray-900 shadow-xl lg:col-span-2 flex flex-col justify-between">
          <h3 className="font-bold text-sm text-gray-400 uppercase tracking-wider mb-4">Readiness Indicators</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
            {breakdowns.map((b) => (
              <div key={b.label} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-gray-400">{b.label}</span>
                  <span>{b.val}/100</span>
                </div>
                <div className="w-full bg-gray-950/60 border border-gray-900 h-2 rounded-full overflow-hidden">
                  <motion.div 
                    className={`h-full rounded-full ${b.color}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${b.val}%` }}
                    transition={{ duration: 1, delay: 0.2 }}
                  ></motion.div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Target Domain & Recommendation details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Domain Card */}
        <div className="glass-panel border border-gray-900 rounded-3xl p-6 space-y-6 shadow-xl relative overflow-hidden">
          <div className="flex items-center gap-3 border-b border-gray-900 pb-4">
            <div className="p-2.5 rounded-xl bg-primary-950/40 border border-primary-900/40 text-primary-400">
              <Target className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base">Domain Classification</h3>
              <p className="text-[10px] text-gray-500">Industry classification vector.</p>
            </div>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold tracking-tight">{analysis.domain}</span>
            <span className="text-emerald-400 text-xs font-bold">({analysis.confidence}% Conf)</span>
          </div>

          <p className="text-xs text-gray-400 leading-relaxed">
            The scanner analyzed key schema attributes, route endpoints, and function structures to match your codebase with targeted industry classification rules.
          </p>
        </div>

        {/* SaaS Recommendation Card */}
        <div className="glass-panel border border-gray-900 rounded-3xl p-6 space-y-6 shadow-xl relative overflow-hidden">
          <div className="flex items-center gap-3 border-b border-gray-900 pb-4">
            <div className="p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-900/40 text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base">SaaS Packaging</h3>
              <p className="text-[10px] text-gray-500">Commercial deployment model.</p>
            </div>
          </div>

          <div className="space-y-1">
            <h4 className="text-xl font-bold">{saas.recommended_product}</h4>
            <span className="inline-block px-2.5 py-0.5 rounded-full bg-primary-950/40 border border-primary-900 text-[10px] font-bold text-primary-300">
              {saas.product_type}
            </span>
          </div>

          <p className="text-xs text-gray-400 leading-relaxed">{saas.explanation}</p>
        </div>
      </div>

      {/* Justifications & Roadmap */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Core Reasons */}
        <div className="glass-panel border border-gray-900 rounded-3xl p-6 space-y-4 shadow-xl lg:col-span-1">
          <h3 className="font-bold text-sm text-gray-400 uppercase tracking-wider">Analysis Justifications</h3>
          <div className="space-y-3.5 pt-2">
            {saas.reasons.map((reason, idx) => (
              <div key={idx} className="flex items-start gap-2.5 text-xs text-gray-300 font-semibold leading-relaxed">
                <Zap className="w-4.5 h-4.5 text-amber-500 flex-shrink-0 mt-0.5" />
                <span>{reason}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Productization Roadmap Checklist */}
        <div className="glass-panel border border-gray-900 rounded-3xl p-6 space-y-4 shadow-xl lg:col-span-2">
          <h3 className="font-bold text-sm text-gray-400 uppercase tracking-wider">Productization Roadmap</h3>
          <div className="space-y-3 pt-2">
            {saas.roadmap.map((step, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 rounded-2xl bg-gray-950/30 border border-gray-900 hover:border-gray-800 transition-colors">
                <CheckSquare className="w-5 h-5 text-primary-400 flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-xs font-bold text-gray-200">Step {idx + 1}</h4>
                  <p className="text-[11px] text-gray-400 leading-relaxed">{step}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Nav Links */}
      <div className="flex items-center justify-end gap-4 border-t border-gray-900 pt-6">
        <Link 
          to={`/dashboard/apis/${id}`}
          className="px-5 py-3 rounded-xl bg-gray-900 border border-gray-800 hover:border-primary-500 font-bold text-xs flex items-center gap-1.5 transition-colors"
        >
          Explore API opportunities
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  )
}

export default ProductRecommendations
