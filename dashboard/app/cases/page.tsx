"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Loader2, AlertCircle, ChevronLeft, ChevronRight, ShieldAlert, Search } from "lucide-react"
import { cn } from "@/lib/utils"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Case {
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
  transactions: {
    amount: number
    payment_method: string
    failure_reason: string
    status: string
    retry_count: number
  }
  customers: {
    name: string
    email: string
    previous_success_rate: number
  }
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

const failureReasonColors: Record<string, string> = {
  BANK_TIMEOUT: "bg-amber-500/10 text-amber-500",
  UPI_TIMEOUT: "bg-orange-500/10 text-orange-500",
  CARD_DECLINED: "bg-red-500/10 text-red-500",
  INSUFFICIENT_BALANCE: "bg-purple-500/10 text-purple-500",
  TECHNICAL_FAILURE: "bg-slate-500/10 text-slate-400",
}

export default function CasesPage() {
  const router = useRouter()
  const [cases, setCases] = useState<Case[]>([])
  const [count, setCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const [searchQuery, setSearchQuery] = useState("")
  const [status, setStatus] = useState("All")
  const [failureReason, setFailureReason] = useState("All")
  const [action, setAction] = useState("All")
  
  const [page, setPage] = useState(0)
  const limit = 50

  const formatINR = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount)
  }

  const fetchCases = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: (page * limit).toString()
      })
      if (status !== "All") params.append("status", status)
      if (failureReason !== "All") params.append("failure_reason", failureReason)
      if (action !== "All") params.append("action", action)

      const res = await fetch(`${API_BASE}/api/cases?${params.toString()}`)
      if (!res.ok) throw new Error("Failed to fetch cases")
      
      const data = await res.json()
      setCases(data.cases || [])
      setCount(data.count || 0)
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred")
    } finally {
      setLoading(false)
    }
  }, [status, failureReason, action, page, limit])

  useEffect(() => {
    fetchCases()
  }, [fetchCases])

  const displayedCases = cases.filter((c) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      c.customers?.name?.toLowerCase().includes(q) ||
      c.customers?.email?.toLowerCase().includes(q) ||
      c.id?.toLowerCase().includes(q) ||
      c.transactions?.failure_reason?.toLowerCase().includes(q) ||
      c.ai_recommendation?.toLowerCase().includes(q)
    )
  })

  return (
    <div className="p-6 md:p-8 max-w-[1600px] mx-auto space-y-8 min-h-screen">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-500/10 rounded-xl">
            <ShieldAlert className="w-6 h-6 text-blue-500" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-slate-100">Recovery Cases</h1>
            <p className="text-sm text-slate-400">Manage and monitor revenue recovery efforts</p>
          </div>
          <span className="ml-2 px-2.5 py-1 text-xs font-medium bg-slate-800 text-slate-300 rounded-full border border-slate-700">
            {count} Total
          </span>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl shadow-black/20">
        <div className="p-4 border-b border-slate-800 flex flex-wrap gap-4 items-center justify-between bg-slate-900/50">
          <div className="relative flex-1 min-w-[280px] max-w-md">
            <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search customer, email, failure reason..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-lg pl-10 pr-4 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 transition-all placeholder:text-slate-500"
            />
          </div>

          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-slate-400">Status</span>
              <select 
                value={status}
                onChange={(e) => { setStatus(e.target.value); setPage(0); }}
                className="bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 transition-all cursor-pointer hover:bg-slate-900"
              >
                <option value="All">All Statuses</option>
                <option value="OPEN">OPEN</option>
                <option value="ANALYZING">ANALYZING</option>
                <option value="ACTION_PENDING">ACTION_PENDING</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="RECOVERED">RECOVERED</option>
                <option value="RECOVERY_FAILED">RECOVERY_FAILED</option>
                <option value="STOPPED">STOPPED</option>
                <option value="STOPPED_BY_POLICY">STOPPED_BY_POLICY</option>
                <option value="REQUIRES_HUMAN_APPROVAL">REQUIRES_HUMAN_APPROVAL</option>
                <option value="ESCALATED">ESCALATED</option>
              </select>
            </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-400">Failure Reason</span>
            <select 
              value={failureReason}
              onChange={(e) => { setFailureReason(e.target.value); setPage(0); }}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 transition-all cursor-pointer hover:bg-slate-900"
            >
              <option value="All">All Reasons</option>
              <option value="BANK_TIMEOUT">BANK_TIMEOUT</option>
              <option value="UPI_TIMEOUT">UPI_TIMEOUT</option>
              <option value="CARD_DECLINED">CARD_DECLINED</option>
              <option value="INSUFFICIENT_BALANCE">INSUFFICIENT_BALANCE</option>
              <option value="TECHNICAL_FAILURE">TECHNICAL_FAILURE</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-400">Action</span>
            <select 
              value={action}
              onChange={(e) => { setAction(e.target.value); setPage(0); }}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 transition-all cursor-pointer hover:bg-slate-900"
            >
              <option value="All">All Actions</option>
              <option value="RETRY_LATER">RETRY_LATER</option>
              <option value="CREATE_PAYMENT_LINK">CREATE_PAYMENT_LINK</option>
              <option value="RECOMMEND_ALTERNATIVE_METHOD">RECOMMEND_ALTERNATIVE_METHOD</option>
              <option value="STOP_RECOVERY">STOP_RECOVERY</option>
              <option value="ESCALATE">ESCALATE</option>
            </select>
          </div>
        </div>
      </div>

        {error && (
          <div className="m-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-3 text-red-500">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-400 bg-slate-900/50">
                <th className="px-6 py-4 font-medium">Customer</th>
                <th className="px-6 py-4 font-medium">Amount Risk</th>
                <th className="px-6 py-4 font-medium">Failure Reason</th>
                <th className="px-6 py-4 font-medium max-w-[200px]">AI Diagnosis</th>
                <th className="px-6 py-4 font-medium">Recommendation</th>
                <th className="px-6 py-4 font-medium">Policy Status</th>
                <th className="px-6 py-4 font-medium text-right">Recovered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <Loader2 className="w-6 h-6 text-blue-500 animate-spin mx-auto mb-2" />
                    <p className="text-sm text-slate-400">Loading cases...</p>
                  </td>
                </tr>
              ) : displayedCases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    <ShieldAlert className="w-8 h-8 mx-auto mb-3 opacity-20" />
                    <p>No recovery cases match your search criteria.</p>
                  </td>
                </tr>
              ) : (
                displayedCases.map((c) => (
                  <tr 
                    key={c.id} 
                    onClick={() => router.push(`/cases/${c.id}`)}
                    className="hover:bg-slate-800/30 transition-colors cursor-pointer group"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-slate-200">{c.customers.name}</div>
                      <div className="text-xs text-slate-500">{c.customers.email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-medium text-slate-200">{formatINR(c.amount_at_risk)}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={cn(
                        "px-2.5 py-1 text-xs font-medium rounded-md",
                        failureReasonColors[c.transactions.failure_reason] || "bg-slate-500/10 text-slate-400"
                      )}>
                        {c.transactions.failure_reason.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400 max-w-[200px] truncate group-hover:text-slate-300 transition-colors">
                      {c.diagnosis}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2.5 py-1 text-xs font-medium rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                        {c.ai_recommendation.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={cn(
                        "px-2.5 py-1 text-xs font-medium rounded-full border",
                        statusColors[c.status] || "bg-slate-500/10 text-slate-400 border-slate-500/20"
                      )}>
                        {c.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      {c.recovered_amount > 0 ? (
                        <span className="font-medium text-green-500">{formatINR(c.recovered_amount)}</span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex items-center justify-between">
          <p className="text-sm text-slate-400">
            Showing <span className="font-medium text-slate-200">{cases.length}</span> of <span className="font-medium text-slate-200">{count}</span> results
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0 || loading}
              className="p-2 rounded-lg border border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={(page + 1) * limit >= count || loading}
              className="p-2 rounded-lg border border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
