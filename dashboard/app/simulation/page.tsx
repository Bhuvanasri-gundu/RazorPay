"use client";

import React, { useState } from "react";
import { 
  Play, TrendingUp, AlertTriangle, CheckCircle, MinusCircle, 
  IndianRupee, ChevronRight, Download, BarChart2, Zap, RefreshCw, Link2
} from "lucide-react";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from "recharts";
import { cn } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Case {
  transaction_id: string;
  amount: number;
  failure_reason: string;
  recommended_action: string;
  final_status: string;
  recovered_amount: number;
}

interface SimulationResults {
  total_processed: number;
  total_revenue_at_risk: number;
  total_recovered: number;
  recovery_rate: number;
  cases_stopped: number;
  payment_links_created: number;
  retries_performed: number;
  baseline_recovery_rate: number;
  reva_recovery_rate: number;
  cases: Case[];
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

export default function SimulationPage() {
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<SimulationResults | null>(null);
  const [progress, setProgress] = useState(0);

  const runSimulation = async () => {
    setIsRunning(true);
    setResults(null);
    setProgress(0);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) return 90;
        return prev + 10;
      });
    }, 300);

    try {
      const res = await fetch(`${API_BASE}/api/simulation/run-batch`, {
        method: "POST",
      });

      if (!res.ok) throw new Error("Failed to run simulation");

      const data = await res.json();
      
      clearInterval(progressInterval);
      setProgress(100);
      
      setTimeout(() => {
        setResults(data);
        setIsRunning(false);
      }, 500);

    } catch (err) {
      console.error(err);
      clearInterval(progressInterval);
    } finally {
      setIsRunning(false);
    }
  };

  const exportReport = () => {
    if (!results) return;
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reva_simulation_report_${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportCSV = () => {
    if (!results || !results.cases || results.cases.length === 0) return;

    const headers = [
      "Transaction ID",
      "Amount",
      "Failure Reason",
      "REVA Action",
      "Outcome",
      "Recovered Amount",
    ];

    const rows = results.cases.map((c) => [
      `"${c.transaction_id || ""}"`,
      c.amount ?? 0,
      `"${c.failure_reason || ""}"`,
      `"${c.recommended_action || ""}"`,
      `"${c.final_status || ""}"`,
      c.recovered_amount ?? 0,
    ]);

    const csvContent = [
      headers.join(","),
      ...rows.map((row) => row.join(",")),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `reva_simulation_cases_${new Date().toISOString().split("T")[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const chartData = results ? [
    {
      name: "Recovery Rate",
      Baseline: results.baseline_recovery_rate,
      REVA: results.reva_recovery_rate,
    }
  ] : [];

  return (
    <div className="container mx-auto p-6 max-w-7xl space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight text-zinc-100 flex items-center gap-3">
            <Zap className="w-8 h-8 text-indigo-500" />
            Batch Simulation
          </h1>
          <p className="text-zinc-400 text-lg">
            Test REVA's AI against historical failed transactions
          </p>
        </div>
        <div className="flex items-center gap-3">
          {results && (
            <button
              onClick={exportReport}
              className="flex items-center gap-2 px-4 py-3 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-sm font-medium rounded-xl transition-all shadow-sm"
            >
              <Download className="w-4 h-4 text-indigo-400" />
              Export JSON Report
            </button>
          )}
          <button
            onClick={runSimulation}
            disabled={isRunning}
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl transition-all shadow-[0_0_20px_-5px_rgba(99,102,241,0.5)] disabled:opacity-50 disabled:shadow-none hover:shadow-[0_0_30px_-5px_rgba(99,102,241,0.6)]"
          >
            {isRunning ? (
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Simulating... {progress}%
              </div>
            ) : (
              <>
                <Play className="w-5 h-5 fill-current" />
                Run Simulation (10,000 txns)
              </>
            )}
          </button>
        </div>
      </div>

      {!results && !isRunning && (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-8 text-center max-w-3xl mx-auto mt-12">
          <BarChart2 className="w-16 h-16 text-zinc-600 mx-auto mb-6" />
          <h2 className="text-2xl font-semibold text-zinc-200 mb-4">Ready to test REVA at scale?</h2>
          <p className="text-zinc-400 mb-8 text-lg">
            This simulation runs REVA's decision engine against a historical dataset of 10,000 failed transactions. 
            It compares standard retry strategies (baseline) against REVA's AI-driven contextual recovery.
          </p>
        </div>
      )}

      {isRunning && (
        <div className="mt-12 max-w-3xl mx-auto space-y-4">
          <div className="flex justify-between text-sm font-medium text-zinc-400">
            <span>Processing batch...</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-indigo-500 transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {results && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
          {/* Top Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="col-span-1 md:col-span-3 lg:col-span-1 rounded-2xl border border-zinc-800 bg-zinc-950 p-6 flex flex-col justify-center">
              <h3 className="text-zinc-400 font-medium mb-6">Recovery Rate Comparison</h3>
              <div className="flex items-end gap-6 justify-center">
                <div className="text-center space-y-2">
                  <div className="text-4xl font-bold text-zinc-500">{results.baseline_recovery_rate}%</div>
                  <div className="text-sm font-medium text-zinc-500 uppercase tracking-wider">Baseline</div>
                </div>
                <div className="text-center space-y-2 relative">
                  <div className="absolute -top-6 -right-6 text-green-400 text-sm font-bold flex items-center bg-green-500/10 px-2 py-1 rounded-full">
                    <TrendingUp className="w-4 h-4 mr-1" />
                    +{((results.reva_recovery_rate - results.baseline_recovery_rate) / results.baseline_recovery_rate * 100).toFixed(0)}%
                  </div>
                  <div className="text-6xl font-bold text-indigo-400 drop-shadow-[0_0_15px_rgba(99,102,241,0.5)]">
                    {results.reva_recovery_rate}%
                  </div>
                  <div className="text-sm font-bold text-indigo-400 uppercase tracking-wider">REVA AI</div>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6">
              <div className="flex items-center gap-3 text-zinc-400 mb-4">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <h3 className="font-medium">Total Revenue at Risk</h3>
              </div>
              <div className="text-4xl font-bold text-zinc-200">
                {formatCurrency(results.total_revenue_at_risk)}
              </div>
              <p className="text-sm text-zinc-500 mt-2">Across {results.total_processed.toLocaleString()} failed transactions</p>
            </div>

            <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-6 relative overflow-hidden">
              <div className="absolute inset-0 bg-green-500/5" />
              <div className="relative">
                <div className="flex items-center gap-3 text-zinc-400 mb-4">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <h3 className="font-medium">Total Recovered</h3>
                </div>
                <div className="text-4xl font-bold text-green-400">
                  {formatCurrency(results.total_recovered)}
                </div>
                <p className="text-sm text-green-500/70 mt-2">Added to top line revenue</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 rounded-2xl border border-zinc-800 bg-zinc-950 p-6 h-[400px]">
              <h3 className="font-semibold text-zinc-200 mb-6">Performance Visualization</h3>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                  <XAxis dataKey="name" stroke="#a1a1aa" />
                  <YAxis stroke="#a1a1aa" tickFormatter={(value) => `${value}%`} />
                  <Tooltip 
                    cursor={{fill: '#27272a', opacity: 0.4}}
                    contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
                  />
                  <Legend />
                  <Bar dataKey="Baseline" fill="#52525b" radius={[4, 4, 0, 0]} maxBarSize={100} />
                  <Bar dataKey="REVA" fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={100} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-4">
              <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5 flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-400">Smart Retries</p>
                  <p className="text-2xl font-bold text-zinc-200">{results.retries_performed}</p>
                </div>
                <RefreshCw className="w-8 h-8 text-zinc-700" />
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5 flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-400">Payment Links Sent</p>
                  <p className="text-2xl font-bold text-zinc-200">{results.payment_links_created}</p>
                </div>
                <Link2 className="w-8 h-8 text-zinc-700" />
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5 flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-400">Avoided Costs (Stopped)</p>
                  <p className="text-2xl font-bold text-zinc-200">{results.cases_stopped}</p>
                </div>
                <MinusCircle className="w-8 h-8 text-zinc-700" />
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-950 overflow-hidden">
            <div className="p-6 border-b border-zinc-800 flex justify-between items-center">
              <h3 className="font-semibold text-zinc-200">Sample Processed Cases</h3>
              <button 
                onClick={exportCSV}
                className="text-sm text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors cursor-pointer"
              >
                <Download className="w-4 h-4" /> Export CSV
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-zinc-400 uppercase bg-zinc-900/50">
                  <tr>
                    <th className="px-6 py-4 font-medium">Transaction ID</th>
                    <th className="px-6 py-4 font-medium">Amount</th>
                    <th className="px-6 py-4 font-medium">Failure Reason</th>
                    <th className="px-6 py-4 font-medium">REVA Action</th>
                    <th className="px-6 py-4 font-medium text-right">Outcome</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {results.cases.map((c, i) => (
                    <tr key={i} className="hover:bg-zinc-900/30 transition-colors">
                      <td className="px-6 py-4 font-mono text-zinc-500">
                        {c.transaction_id.substring(0, 12)}...
                      </td>
                      <td className="px-6 py-4 text-zinc-300">
                        {formatCurrency(c.amount)}
                      </td>
                      <td className="px-6 py-4 text-zinc-400 text-xs">
                        {c.failure_reason}
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 rounded-md bg-zinc-800 text-zinc-300 text-xs border border-zinc-700">
                          {c.recommended_action}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className={cn(
                          "inline-flex items-center gap-1.5 font-medium",
                          c.final_status === "RECOVERED" ? "text-green-400" :
                          c.final_status === "STOPPED" ? "text-zinc-500" :
                          "text-blue-400"
                        )}>
                          {c.final_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
