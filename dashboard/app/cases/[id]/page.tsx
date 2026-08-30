"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { 
  ArrowLeft, 
  Loader2, 
  AlertCircle, 
  CheckCircle2, 
  ShieldAlert, 
  CreditCard,
  User,
  Activity,
  Zap,
  ExternalLink,
  Clock,
  ThumbsUp,
  BrainCircuit,
  XCircle,
  Play
} from "lucide-react"
import { cn } from "@/lib/utils"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Action {
  id: string
  action_type: string
  execution_status: string
  razorpay_payment_link_id: string | null
  details: any
  created_at: string
}

interface AuditTrail {
  id: string
  component: string
  event_type: string
  message: string
  metadata: any
  created_at: string
}

interface CaseDetails {
  case: {
    id: string
    transaction_id: string
    customer_id: string
    amount_at_risk: number
    diagnosis: string
    ai_recommendation: string
    selected_action: string
    status: string
    recovered_amount: number
    created_at: string
    updated_at: string
  }
  transaction: {
    id: string
    amount: number
    currency: string
    payment_method: string
    status: string
    failure_reason: string
    retry_count: number
  }
  customer: {
    id: string
    name: string
    email: string
    phone: string
    previous_success_rate: number
  }
  actions: Action[]
  audit_trail: AuditTrail[]
}

const statusColors: Record<string, string> = {
  RECOVERED: "bg-green-500/10 text-green-500 border-green-500/20",
  OPEN: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  ANALYZING: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  ACTION_PENDING: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  IN_PROGRESS: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  STOPPED: "bg-slate-500/10 text-slate-500 border-slate-500/20",
  STOPPED_BY_POLICY: "bg-slate-500/10 text-slate-500 border-slate-500/20",
  REQUIRES_HUMAN_APPROVAL: "bg-orange-500/10 text-orange-500 border-orange-500/20",
  RECOVERY_FAILED: "bg-red-500/10 text-red-500 border-red-500/20",
  ESCALATED: "bg-purple-500/10 text-purple-500 border-purple-500/20",
}

const WORKFLOW_STEPS = [
  { id: 'DETECTED', label: 'Detected' },
  { id: 'ANALYZED', label: 'Analyzed' },
  { id: 'DECISION', label: 'Decision' },
  { id: 'POLICY', label: 'Policy' },
  { id: 'ACTION', label: 'Action' },
  { id: 'RESULT', label: 'Result' }
]

export default function CaseDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const caseId = params.id as string

  const [data, setData] = useState<CaseDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  const formatINR = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const fetchCase = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/cases/${caseId}`)
      if (!res.ok) throw new Error("Failed to fetch case details")
      const json = await res.json()
      setData(json)
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred")
    } finally {
      setLoading(false)
    }
  }, [caseId])

  useEffect(() => {
    if (caseId) {
      fetchCase()
    }
  }, [caseId, fetchCase])

  const handleAction = async (endpoint: string) => {
    setActionLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/cases/${caseId}/${endpoint}`, {
        method: 'POST'
      })
      if (!res.ok) throw new Error(`Failed to ${endpoint} case`)
      await fetchCase()
    } catch (err: any) {
      alert(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin mb-4 text-blue-500" />
        <p>Loading case details...</p>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <button onClick={() => router.back()} className="flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Cases
        </button>
        <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-start gap-4 text-red-500">
          <AlertCircle className="w-6 h-6 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-lg font-semibold mb-1">Error Loading Case</h3>
            <p className="text-sm opacity-90">{error || "Case not found"}</p>
          </div>
        </div>
      </div>
    )
  }

  const { case: caseInfo, transaction, customer, actions, audit_trail } = data
  const isRecovered = caseInfo.status === 'RECOVERED'
  const isFailed = caseInfo.status === 'RECOVERY_FAILED' || caseInfo.status === 'STOPPED' || caseInfo.status === 'STOPPED_BY_POLICY'
  
  // Determine workflow progress based on status and audit trail
  const getWorkflowProgress = () => {
    const s = caseInfo.status
    if (['OPEN'].includes(s)) return 0 // Detected
    if (['ANALYZING'].includes(s)) return 1 // Analyzed
    if (['REQUIRES_HUMAN_APPROVAL'].includes(s)) return 2 // Decision
    if (['ACTION_PENDING', 'IN_PROGRESS'].includes(s)) return 4 // Action
    if (isRecovered || isFailed) return 5 // Result
    return 3 // Policy
  }

  const currentStep = getWorkflowProgress()

  return (
    <div className="p-6 md:p-8 max-w-[1600px] mx-auto space-y-8 min-h-screen pb-24">
      {/* Header */}
      <div>
        <button 
          onClick={() => router.push('/cases')} 
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 mb-6 transition-colors font-medium group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" /> Back to Cases
        </button>
        
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-slate-100">Case {caseInfo.id.split('-')[0]}</h1>
              <span className={cn(
                "px-3 py-1 text-xs font-semibold rounded-full border uppercase tracking-wider",
                statusColors[caseInfo.status] || "bg-slate-500/10 text-slate-400 border-slate-500/20"
              )}>
                {caseInfo.status.replace(/_/g, ' ')}
              </span>
            </div>
            <p className="text-slate-400 text-sm flex items-center gap-2">
              <Clock className="w-4 h-4" /> Created on {formatDate(caseInfo.created_at)}
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-1">Amount at Risk</p>
              <p className="text-3xl font-bold text-slate-100">{formatINR(caseInfo.amount_at_risk)}</p>
            </div>
            
            {/* Action Buttons based on status */}
            {caseInfo.status === 'OPEN' && (
              <button 
                onClick={() => handleAction('analyze')}
                disabled={actionLoading}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors disabled:opacity-50 ml-4"
              >
                {actionLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <BrainCircuit className="w-5 h-5" />}
                Analyze Case
              </button>
            )}
            {caseInfo.status === 'ACTION_PENDING' && (
              <button 
                onClick={() => handleAction('execute')}
                disabled={actionLoading}
                className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-medium transition-colors disabled:opacity-50 ml-4"
              >
                {actionLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                Execute Recovery
              </button>
            )}
            {caseInfo.status === 'REQUIRES_HUMAN_APPROVAL' && (
              <button 
                onClick={() => handleAction('approve')}
                disabled={actionLoading}
                className="flex items-center gap-2 px-6 py-3 bg-orange-600 hover:bg-orange-700 text-white rounded-xl font-medium transition-colors disabled:opacity-50 ml-4"
              >
                {actionLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <ThumbsUp className="w-5 h-5" />}
                Approve Action
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Visual Workflow Progress */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-lg shadow-black/10">
        <div className="relative flex justify-between">
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-slate-800 rounded-full" />
          <div 
            className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-blue-500 rounded-full transition-all duration-1000"
            style={{ width: `${(Math.min(currentStep, WORKFLOW_STEPS.length - 1) / (WORKFLOW_STEPS.length - 1)) * 100}%` }}
          />
          
          {WORKFLOW_STEPS.map((step, idx) => {
            const isCompleted = idx < currentStep || (idx === currentStep && (isRecovered || isFailed))
            const isCurrent = idx === currentStep && !isRecovered && !isFailed
            const isErrorStep = idx === currentStep && isFailed
            
            return (
              <div key={step.id} className="relative z-10 flex flex-col items-center gap-3">
                <div className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center border-4 border-slate-900 transition-colors duration-500",
                  isCompleted ? "bg-blue-500 text-white" : 
                  isErrorStep ? "bg-red-500 text-white" :
                  isCurrent ? "bg-blue-500 text-white animate-pulse" : 
                  "bg-slate-800 text-slate-500"
                )}>
                  {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : 
                   isErrorStep ? <XCircle className="w-5 h-5" /> :
                   <div className="w-3 h-3 rounded-full bg-current" />}
                </div>
                <span className={cn(
                  "text-xs font-semibold uppercase tracking-wider",
                  isCompleted || isCurrent ? "text-slate-200" : "text-slate-500"
                )}>{step.label}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Transaction Details */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col hover:border-slate-700 transition-colors">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 bg-slate-800 rounded-xl">
              <CreditCard className="w-5 h-5 text-slate-300" />
            </div>
            <h3 className="font-semibold text-slate-200">Transaction Info</h3>
          </div>
          <div className="space-y-4 flex-1">
            <div className="flex justify-between items-center pb-4 border-b border-slate-800/50">
              <span className="text-sm text-slate-400">Method</span>
              <span className="text-sm font-medium text-slate-200">{transaction.payment_method}</span>
            </div>
            <div className="flex justify-between items-center pb-4 border-b border-slate-800/50">
              <span className="text-sm text-slate-400">Failure Reason</span>
              <span className="text-sm font-medium text-red-400 bg-red-500/10 px-2 py-0.5 rounded">
                {transaction.failure_reason.replace(/_/g, ' ')}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-400">Retry Count</span>
              <span className="text-sm font-medium text-slate-200">{transaction.retry_count}</span>
            </div>
          </div>
        </div>

        {/* Customer Summary */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col hover:border-slate-700 transition-colors">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2.5 bg-indigo-500/10 rounded-xl">
              <User className="w-5 h-5 text-indigo-400" />
            </div>
            <h3 className="font-semibold text-slate-200">Customer Profile</h3>
          </div>
          <div className="space-y-4 flex-1">
            <div>
              <p className="font-medium text-slate-200">{customer.name}</p>
              <p className="text-sm text-slate-400">{customer.email}</p>
              <p className="text-sm text-slate-400 mt-1">{customer.phone}</p>
            </div>
            <div className="pt-4 border-t border-slate-800/50">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-slate-400">Previous Success Rate</span>
                <span className="text-sm font-bold text-slate-200">{(customer.previous_success_rate * 100).toFixed(0)}%</span>
              </div>
              <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                <div 
                  className={cn(
                    "h-full rounded-full transition-all",
                    customer.previous_success_rate > 0.8 ? "bg-green-500" : 
                    customer.previous_success_rate > 0.5 ? "bg-amber-500" : "bg-red-500"
                  )} 
                  style={{ width: `${customer.previous_success_rate * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Recovery Result */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col hover:border-slate-700 transition-colors relative overflow-hidden">
          {isRecovered && <div className="absolute top-0 right-0 w-24 h-24 bg-green-500/10 rounded-bl-full -z-0" />}
          
          <div className="flex items-center gap-3 mb-6 relative z-10">
            <div className="p-2.5 bg-emerald-500/10 rounded-xl">
              <Activity className="w-5 h-5 text-emerald-400" />
            </div>
            <h3 className="font-semibold text-slate-200">Recovery Status</h3>
          </div>
          <div className="space-y-4 flex-1 relative z-10">
            <div className="flex justify-between items-center pb-4 border-b border-slate-800/50">
              <span className="text-sm text-slate-400">AI Recommendation</span>
              <span className="text-xs font-semibold px-2 py-1 bg-slate-800 rounded text-slate-300">
                {caseInfo.ai_recommendation.replace(/_/g, ' ')}
              </span>
            </div>
            <div className="flex justify-between items-center pb-4 border-b border-slate-800/50">
              <span className="text-sm text-slate-400">Recovered Amount</span>
              <span className={cn(
                "font-bold",
                isRecovered ? "text-green-500 text-lg" : "text-slate-400"
              )}>
                {caseInfo.recovered_amount > 0 ? formatINR(caseInfo.recovered_amount) : '—'}
              </span>
            </div>
            {isRecovered && (
              <div className="flex items-center gap-2 text-sm text-green-400 font-medium pt-2">
                <CheckCircle2 className="w-4 h-4" /> Recovery Successful
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Details & Actions */}
        <div className="lg:col-span-2 space-y-8">
          {/* AI Diagnosis */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-900/50 border border-indigo-500/20 rounded-2xl p-6 shadow-[0_0_30px_-10px_rgba(99,102,241,0.1)]">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-indigo-500/20 rounded-lg">
                <BrainCircuit className="w-6 h-6 text-indigo-400" />
              </div>
              <h2 className="text-xl font-semibold text-slate-100">AI Diagnosis</h2>
            </div>
            <p className="text-slate-300 leading-relaxed text-lg bg-slate-950/50 p-5 rounded-xl border border-slate-800/50">
              {caseInfo.diagnosis || "No diagnosis available yet. AI is analyzing..."}
            </p>
          </div>

          {/* Actions Taken */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-xl font-semibold text-slate-100 mb-6 flex items-center gap-3">
              <Zap className="w-6 h-6 text-amber-500" />
              Recovery Actions
            </h2>
            
            {actions.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <p>No actions have been executed yet.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {actions.map((act) => (
                  <div key={act.id} className="bg-slate-950 border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row justify-between sm:items-center gap-4 hover:border-slate-700 transition-colors">
                    <div>
                      <div className="flex items-center gap-3 mb-1">
                        <span className="font-semibold text-slate-200">
                          {act.action_type.replace(/_/g, ' ')}
                        </span>
                        <span className={cn(
                          "text-xs font-medium px-2 py-0.5 rounded-full border",
                          act.execution_status === 'COMPLETED' ? "bg-green-500/10 text-green-500 border-green-500/20" :
                          act.execution_status === 'FAILED' ? "bg-red-500/10 text-red-500 border-red-500/20" :
                          "bg-blue-500/10 text-blue-500 border-blue-500/20"
                        )}>
                          {act.execution_status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 flex items-center gap-1 mt-2">
                        <Clock className="w-3 h-3" /> {formatDate(act.created_at)}
                      </p>
                    </div>
                    
                    {act.razorpay_payment_link_id && act.details?.short_url && (
                      <a 
                        href={act.details.short_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center justify-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium transition-colors border border-slate-700"
                      >
                        <ExternalLink className="w-4 h-4" /> Open Link
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Audit Trail */}
        <div className="lg:col-span-1">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 h-full">
            <h2 className="text-xl font-semibold text-slate-100 mb-8 flex items-center gap-3">
              <Activity className="w-6 h-6 text-blue-500" />
              Timeline
            </h2>
            
            <div className="relative pl-3">
              {/* Vertical line */}
              <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-slate-800" />
              
              <div className="space-y-8">
                {audit_trail.map((audit, idx) => {
                  const isSuccess = audit.event_type.includes('SUCCESS') || audit.event_type.includes('COMPLETED')
                  const isError = audit.event_type.includes('FAILED') || audit.event_type.includes('ERROR')
                  
                  return (
                    <div key={audit.id} className="relative pl-8">
                      {/* Node */}
                      <div className={cn(
                        "absolute left-0 top-1 w-3 h-3 rounded-full border-2 border-slate-900 -ml-[5px] z-10",
                        isSuccess ? "bg-green-500" :
                        isError ? "bg-red-500" :
                        "bg-blue-500"
                      )} />
                      
                      <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-4 hover:border-slate-700 transition-colors">
                        <div className="text-[10px] font-bold tracking-wider text-slate-500 uppercase mb-1">
                          {formatDate(audit.created_at)}
                        </div>
                        <h4 className="font-semibold text-sm text-slate-200 mb-1">
                          {audit.event_type.replace(/_/g, ' ')}
                        </h4>
                        <p className="text-xs text-slate-400 mb-2 leading-relaxed">
                          {audit.message}
                        </p>
                        <div className="inline-flex items-center px-2 py-1 bg-slate-900 rounded text-[10px] text-slate-500 border border-slate-800">
                          {audit.component}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
