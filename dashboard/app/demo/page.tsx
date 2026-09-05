"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  RefreshCw, Smartphone, XCircle, Shield, 
  CheckCircle, X, Lock, Link2, Loader2, Play, ChevronRight, Activity, Cpu, ArrowRight, IndianRupee, Sparkles, Sliders, Settings2, RotateCcw, ExternalLink
} from "lucide-react";
import { cn } from "@/lib/utils";
import NextLink from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Scenario {
  name: string;
  description: string;
  amount: number;
  payment_method: string;
  failure_reason: string;
}

interface StepData {
  diagnosis?: string;
  confidence?: string;
  recommended_action?: string;
  [key: string]: any;
}

interface Step {
  step: string;
  status: "PROCESSING" | "COMPLETED" | "FAILED" | "BLOCKED";
  message: string;
  data?: StepData;
}

interface RunScenarioResponse {
  success: boolean;
  scenario: Scenario;
  case_id: string;
  steps: Step[];
  final_status: string;
  error?: string;
}

type StageStatus = "WAITING" | "PROCESSING" | "COMPLETED" | "BLOCKED" | "FAILED";

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
};

const SCENARIO_DEFS = [
  {
    id: 1,
    icon: RefreshCw,
    title: "Temporary Bank Failure",
    description: "A bank timeout that can be recovered via bounded retry",
    expectedOutcome: "RECOVERED",
    outcomeColor: "text-green-400 bg-green-500/10 border-green-500/20",
    amount: 2499,
  },
  {
    id: 2,
    icon: Smartphone,
    title: "Repeated UPI Failure",
    description: "Multiple UPI failures, switch to alternative method & payment link",
    expectedOutcome: "PAYMENT LINK",
    outcomeColor: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    amount: 4999,
  },
  {
    id: 3,
    icon: XCircle,
    title: "Low Recovery Opportunity",
    description: "Max retries / insufficient balance — AI safely stops friction",
    expectedOutcome: "STOPPED",
    outcomeColor: "text-zinc-400 bg-zinc-500/10 border-zinc-500/20",
    amount: 199,
  },
  {
    id: 4,
    icon: Shield,
    title: "High Value Transaction",
    description: "Amount >= ₹50,000 policy rule mandates human approval",
    expectedOutcome: "REQUIRES APPROVAL",
    outcomeColor: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    amount: 74999,
  },
];

export default function DemoPage() {
  const [activeTab, setActiveTab] = useState<"preset" | "sandbox">("preset");
  const [selectedScenario, setSelectedScenario] = useState<number | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [allSteps, setAllSteps] = useState<Step[]>([]);
  const [displayedSteps, setDisplayedSteps] = useState<Step[]>([]);
  const [caseId, setCaseId] = useState<string | null>(null);
  const [finalStatus, setFinalStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Custom Sandbox States
  const [customAmount, setCustomAmount] = useState<number>(4999);
  const [customMethod, setCustomMethod] = useState<string>("UPI");
  const [customReason, setCustomReason] = useState<string>("UPI_TIMEOUT");
  const [customSuccessRate, setCustomSuccessRate] = useState<number>(0.75);
  const [customRetries, setCustomRetries] = useState<number>(1);
  const [customName, setCustomName] = useState<string>("Judge Demo");

  const stepsEndRef = useRef<HTMLDivElement>(null);

  const runScenario = async (id: number) => {
    setSelectedScenario(id);
    setIsRunning(true);
    setAllSteps([]);
    setDisplayedSteps([]);
    setCaseId(null);
    setFinalStatus(null);
    setError(null);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      const res = await fetch(`${API_BASE}/api/demo/run-scenario`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ scenario: id }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data: RunScenarioResponse = await res.json();
      if (data.steps && data.steps.length > 0) {
        setAllSteps(data.steps);
        setDisplayedSteps([data.steps[0]]);
        setCaseId(data.case_id);
        setFinalStatus(data.final_status || "COMPLETED");
      } else {
        throw new Error(data.error || "No execution steps returned");
      }
    } catch (err: any) {
      console.error("Scenario execution error:", err);
      setError(err?.name === "AbortError" ? "Request timed out. Please retry." : (err?.message || "An error occurred while running the scenario."));
      setIsRunning(false);
    }
  };

  const runCustomScenario = async () => {
    setSelectedScenario(null);
    setIsRunning(true);
    setAllSteps([]);
    setDisplayedSteps([]);
    setCaseId(null);
    setFinalStatus(null);
    setError(null);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      const res = await fetch(`${API_BASE}/api/demo/run-custom-scenario`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          amount: Number(customAmount) || 2499,
          payment_method: customMethod,
          failure_reason: customReason,
          customer_success_rate: Number(customSuccessRate),
          retry_count: Number(customRetries),
          customer_name: customName || "Custom Demo",
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data: RunScenarioResponse = await res.json();
      if (data.steps && data.steps.length > 0) {
        setAllSteps(data.steps);
        setDisplayedSteps([data.steps[0]]);
        setCaseId(data.case_id);
        setFinalStatus(data.final_status || "COMPLETED");
      } else {
        throw new Error(data.error || "No execution steps returned");
      }
    } catch (err: any) {
      console.error("Custom scenario error:", err);
      setError(err?.name === "AbortError" ? "Request timed out. Please retry." : (err?.message || "An error occurred while running custom scenario."));
      setIsRunning(false);
    }
  };

  useEffect(() => {
    if (allSteps.length > 0 && displayedSteps.length < allSteps.length) {
      const timer = setTimeout(() => {
        setDisplayedSteps((prev) => [...prev, allSteps[prev.length]]);
      }, 250);
      return () => clearTimeout(timer);
    } else if (allSteps.length > 0 && displayedSteps.length >= allSteps.length) {
      setIsRunning(false);
    }
  }, [allSteps, displayedSteps]);

  useEffect(() => {
    stepsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [displayedSteps]);

  // Compute live visual stage statuses
  const getStageStatuses = (): Record<string, StageStatus> => {
    const stepNames = displayedSteps.map((s) => s.step);

    // 1. Detection
    let detection: StageStatus = "WAITING";
    if (stepNames.includes("CASE_CREATED") || stepNames.includes("AI_ANALYZING") || stepNames.includes("AI_COMPLETE")) {
      detection = "COMPLETED";
    } else if (stepNames.includes("INIT") || stepNames.includes("CUSTOMER_FOUND") || stepNames.includes("PAYMENT_FAILED") || isRunning) {
      detection = "PROCESSING";
    }

    // 2. Gemini AI
    let ai: StageStatus = "WAITING";
    if (stepNames.includes("AI_COMPLETE") || stepNames.includes("POLICY_CHECK") || stepNames.includes("POLICY_APPROVED") || stepNames.includes("ALTERNATIVE") || stepNames.includes("RECOVERED")) {
      ai = "COMPLETED";
    } else if (stepNames.includes("AI_ANALYZING") || stepNames.includes("CASE_CREATED")) {
      ai = "PROCESSING";
    }

    // 3. Policy Engine
    let policy: StageStatus = "WAITING";
    if (stepNames.includes("POLICY_BLOCKED") || stepNames.includes("REQUIRES_APPROVAL")) {
      policy = "BLOCKED";
    } else if (stepNames.includes("POLICY_APPROVED") || stepNames.includes("ACTION_EXECUTED") || stepNames.includes("RECOVERED") || stepNames.includes("ALTERNATIVE") || stepNames.includes("STOPPED")) {
      policy = "COMPLETED";
    } else if (stepNames.includes("POLICY_CHECK") || stepNames.includes("AI_COMPLETE")) {
      policy = "PROCESSING";
    }

    // 4. Action Execution
    let execution: StageStatus = "WAITING";
    if (stepNames.includes("POLICY_BLOCKED") || stepNames.includes("REQUIRES_APPROVAL")) {
      execution = "BLOCKED";
    } else if (stepNames.includes("RECOVERED") || stepNames.includes("PAYMENT_LINK") || stepNames.includes("ALTERNATIVE") || stepNames.includes("STOPPED")) {
      execution = "COMPLETED";
    } else if (stepNames.includes("RECOVERY_FAILED")) {
      execution = "FAILED";
    } else if (stepNames.includes("ACTION_EXECUTED") || stepNames.includes("POLICY_APPROVED")) {
      execution = "PROCESSING";
    }

    // 5. Result
    let result: StageStatus = "WAITING";
    if (stepNames.includes("POLICY_BLOCKED") || stepNames.includes("REQUIRES_APPROVAL")) {
      result = "BLOCKED";
    } else if (stepNames.includes("RECOVERED") || stepNames.includes("PAYMENT_LINK") || stepNames.includes("ALTERNATIVE") || stepNames.includes("STOPPED")) {
      result = "COMPLETED";
    } else if (stepNames.includes("RECOVERY_FAILED")) {
      result = "FAILED";
    } else if (stepNames.includes("ACTION_EXECUTED")) {
      result = "PROCESSING";
    }

    return { detection, ai, policy, execution, result };
  };

  const stageStatuses = getStageStatuses();

  const getStatusIcon = (status: Step["status"]) => {
    switch (status) {
      case "PROCESSING":
        return <Loader2 className="h-5 w-5 text-indigo-400 animate-spin" />;
      case "COMPLETED":
        return <CheckCircle className="h-5 w-5 text-green-400" />;
      case "FAILED":
        return <X className="h-5 w-5 text-red-400" />;
      case "BLOCKED":
        return <Lock className="h-5 w-5 text-amber-400" />;
      default:
        return <Activity className="h-5 w-5 text-zinc-400" />;
    }
  };

  const renderStageBadge = (label: string, status: StageStatus) => {
    const colorMap: Record<StageStatus, string> = {
      WAITING: "border-zinc-800 bg-zinc-900/40 text-zinc-500",
      PROCESSING: "border-indigo-500/50 bg-indigo-500/10 text-indigo-400 animate-pulse",
      COMPLETED: "border-green-500/40 bg-green-500/10 text-green-400 shadow-[0_0_12px_-2px_rgba(34,197,94,0.3)]",
      BLOCKED: "border-amber-500/40 bg-amber-500/10 text-amber-400 shadow-[0_0_12px_-2px_rgba(245,158,11,0.3)]",
      FAILED: "border-red-500/40 bg-red-500/10 text-red-400",
    };

    return (
      <div className="flex flex-col items-center flex-1 min-w-[120px]">
        <div className="text-[11px] font-semibold text-zinc-400 mb-1.5 uppercase tracking-wider">{label}</div>
        <span className={cn("text-xs font-bold px-3 py-1 rounded-md border tracking-wider transition-all duration-300", colorMap[status])}>
          {status === "PROCESSING" && <Loader2 className="inline-block w-3 h-3 mr-1 animate-spin" />}
          {status}
        </span>
      </div>
    );
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-indigo-400" />
            <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
              Live Demo & Sandbox
            </h1>
          </div>
          <p className="text-zinc-400 text-sm md:text-base">
            Watch REVA detect, diagnose with Gemini AI, validate via Policy Engine, and execute recovery in real-time.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="inline-flex p-1 bg-zinc-900 border border-zinc-800 rounded-xl self-start md:self-auto">
          <button
            onClick={() => setActiveTab("preset")}
            className={cn(
              "px-4 py-2 text-xs font-semibold rounded-lg transition-all",
              activeTab === "preset"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/20"
                : "text-zinc-400 hover:text-zinc-200"
            )}
          >
            4 Core Scenarios
          </button>
          <button
            onClick={() => setActiveTab("sandbox")}
            className={cn(
              "flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg transition-all",
              activeTab === "sandbox"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/20"
                : "text-zinc-400 hover:text-zinc-200"
            )}
          >
            <Sliders className="w-3.5 h-3.5" /> Interactive Sandbox
          </button>
        </div>
      </div>

      {/* Mode 1: 4 Predefined Scenario Cards */}
      {activeTab === "preset" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in duration-300">
          {SCENARIO_DEFS.map((s) => (
            <div
              key={s.id}
              className={cn(
                "group relative overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950/50 p-6 transition-all duration-300 hover:border-indigo-500/50 hover:bg-zinc-900/80",
                selectedScenario === s.id && "border-indigo-500 bg-indigo-500/10 shadow-[0_0_30px_-5px_rgba(99,102,241,0.3)]",
                isRunning && selectedScenario !== s.id && "opacity-50 pointer-events-none grayscale"
              )}
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-lg bg-zinc-900 border border-zinc-800 text-indigo-400 group-hover:scale-110 transition-transform">
                    <s.icon className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-0.5">Scenario {s.id}</div>
                    <h3 className="font-semibold text-zinc-100 text-base">{s.title}</h3>
                    <p className="text-sm text-zinc-400 mt-1">{s.description}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xl font-bold text-zinc-100">{formatCurrency(s.amount)}</div>
                </div>
              </div>

              <div className="flex items-center justify-between mt-6 pt-4 border-t border-zinc-800/80">
                <span className={cn("text-xs font-semibold px-2.5 py-1 rounded-md border uppercase tracking-wider", s.outcomeColor)}>
                  {s.expectedOutcome}
                </span>
                <button
                  id={`run-scenario-btn-${s.id}`}
                  data-testid={`run-scenario-btn-${s.id}`}
                  onClick={() => runScenario(s.id)}
                  disabled={isRunning}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 shadow-md shadow-indigo-500/20"
                >
                  {isRunning && selectedScenario === s.id ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Run Scenario
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Mode 2: Interactive Sandbox */}
      {activeTab === "sandbox" && (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-6 md:p-8 space-y-6 shadow-xl animate-in fade-in duration-300">
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-4">
            <div>
              <h2 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
                <Settings2 className="w-5 h-5 text-indigo-400" /> Interactive Transaction Sandbox
              </h2>
              <p className="text-xs text-zinc-400 mt-0.5">Customize payment conditions and observe how REVA's AI and Policy Engine react.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Amount */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">Transaction Amount (INR)</label>
              <div className="relative">
                <input
                  type="number"
                  value={customAmount}
                  onChange={(e) => setCustomAmount(Number(e.target.value))}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-100 text-sm outline-none focus:border-indigo-500"
                />
              </div>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {[199, 2499, 4999, 49999, 75000].map((amt) => (
                  <button
                    key={amt}
                    type="button"
                    onClick={() => setCustomAmount(amt)}
                    className="text-[11px] px-2 py-0.5 rounded bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800"
                  >
                    {amt >= 50000 ? `₹${amt / 1000}k (Policy Flag)` : `₹${amt}`}
                  </button>
                ))}
              </div>
            </div>

            {/* Payment Method */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">Payment Method</label>
              <select
                value={customMethod}
                onChange={(e) => setCustomMethod(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-100 text-sm outline-none focus:border-indigo-500 cursor-pointer"
              >
                <option value="UPI">UPI</option>
                <option value="CARD">Credit / Debit Card</option>
                <option value="NETBANKING">Netbanking</option>
                <option value="WALLET">Wallet</option>
              </select>
            </div>

            {/* Failure Reason */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">Failure Reason</label>
              <select
                value={customReason}
                onChange={(e) => setCustomReason(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-100 text-sm outline-none focus:border-indigo-500 cursor-pointer"
              >
                <option value="BANK_TIMEOUT">BANK_TIMEOUT (Transient)</option>
                <option value="UPI_TIMEOUT">UPI_TIMEOUT (PSP Glitch)</option>
                <option value="CARD_DECLINED">CARD_DECLINED (Issuing Bank)</option>
                <option value="INSUFFICIENT_BALANCE">INSUFFICIENT_BALANCE (Low Funds)</option>
                <option value="TECHNICAL_FAILURE">TECHNICAL_FAILURE (Gateway Error)</option>
              </select>
            </div>

            {/* Past Customer Success Rate */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">Customer Success History</label>
                <span className="text-xs font-bold text-indigo-400">{(customSuccessRate * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="1.0"
                step="0.05"
                value={customSuccessRate}
                onChange={(e) => setCustomSuccessRate(Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-zinc-500">
                <span>Unreliable (5%)</span>
                <span>Average (50%)</span>
                <span>VIP (100%)</span>
              </div>
            </div>

            {/* Previous Retries */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">Previous Retry Count</label>
                <span className={cn("text-xs font-bold", customRetries >= 3 ? "text-red-400" : "text-zinc-300")}>
                  {customRetries} {customRetries >= 3 ? "(Max Reached)" : ""}
                </span>
              </div>
              <div className="flex gap-2">
                {[0, 1, 2, 3, 4].map((cnt) => (
                  <button
                    key={cnt}
                    type="button"
                    onClick={() => setCustomRetries(cnt)}
                    className={cn(
                      "flex-1 py-1.5 rounded-lg border text-xs font-semibold transition-colors",
                      customRetries === cnt
                        ? "bg-indigo-600 border-indigo-500 text-white"
                        : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-zinc-200"
                    )}
                  >
                    {cnt}
                  </button>
                ))}
              </div>
            </div>

            {/* Customer Name */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">Customer Reference</label>
              <input
                type="text"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                placeholder="e.g. Acme Corp / Rohan Sharma"
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-100 text-sm outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-zinc-800/80 flex items-center justify-between">
            <div className="text-xs text-zinc-500">
              Expected behavior: Amounts $\ge$ ₹50,000 trigger approval; Retries $\ge$ 3 trigger policy stop.
            </div>
            <button
              onClick={runCustomScenario}
              disabled={isRunning}
              className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-xl transition-all shadow-lg shadow-indigo-500/25 disabled:opacity-50"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing with REVA...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Custom Analysis
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-red-400 flex items-center gap-3">
          <XCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* Execution Engine Panel */}
      {(displayedSteps.length > 0 || isRunning) && (
        <div className="mt-12 rounded-xl border border-zinc-800 bg-zinc-950 overflow-hidden shadow-2xl relative">
          <div className="border-b border-zinc-800 bg-zinc-900/50 p-4 flex items-center gap-3">
            <Cpu className="w-5 h-5 text-indigo-400" />
            <h2 className="font-semibold text-zinc-100">REVA Autonomous Execution Engine</h2>
            {isRunning && (
              <span className="ml-auto flex items-center gap-2 text-xs font-medium text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-full border border-indigo-500/20 animate-pulse">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                </span>
                PROCESSING STAGE
              </span>
            )}
          </div>

          {/* Real-time Stage Pipeline */}
          <div className="p-5 border-b border-zinc-800 bg-zinc-900/30">
            <div className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" /> Workflow Stage Progression
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 bg-zinc-950/80 p-4 rounded-lg border border-zinc-800/80">
              {renderStageBadge("1. Detection", stageStatuses.detection)}
              <ChevronRight className="w-4 h-4 text-zinc-600 hidden sm:block" />
              {renderStageBadge("2. Gemini AI", stageStatuses.ai)}
              <ChevronRight className="w-4 h-4 text-zinc-600 hidden sm:block" />
              {renderStageBadge("3. Policy Engine", stageStatuses.policy)}
              <ChevronRight className="w-4 h-4 text-zinc-600 hidden sm:block" />
              {renderStageBadge("4. Action Execution", stageStatuses.execution)}
              <ChevronRight className="w-4 h-4 text-zinc-600 hidden sm:block" />
              {renderStageBadge("5. Outcome", stageStatuses.result)}
            </div>
          </div>

          {/* Chronological Step Logs */}
          <div className="p-6 space-y-4 max-h-[600px] overflow-y-auto font-mono text-sm">
            {displayedSteps.map((step, index) => (
              <div 
                key={index}
                className="flex flex-col gap-2 animate-in fade-in slide-in-from-left-4 duration-500"
              >
                <div className="flex items-start gap-4">
                  <div className="mt-0.5 relative z-10 bg-zinc-950">
                    {getStatusIcon(step.status)}
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-zinc-500 text-xs">[{new Date().toLocaleTimeString()}]</span>
                      <span className={cn(
                        "font-medium",
                        step.status === "PROCESSING" ? "text-indigo-300" :
                        step.status === "FAILED" ? "text-red-300" :
                        step.status === "BLOCKED" ? "text-amber-300" :
                        "text-zinc-200"
                      )}>
                        {step.step}:
                      </span>
                      <span className="text-zinc-300">{step.message}</span>
                    </div>

                    {step.data && Object.keys(step.data).length > 0 && (
                      <div className="mt-2 p-4 rounded-lg bg-zinc-900/80 border border-zinc-800 text-zinc-400 space-y-2 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                          <Cpu className="w-16 h-16" />
                        </div>
                        {step.data.diagnosis && (
                          <div className="flex items-start gap-2">
                            <span className="text-indigo-400 font-semibold min-w-32">Diagnosis:</span>
                            <span className="text-zinc-200">{step.data.diagnosis}</span>
                          </div>
                        )}
                        {step.data.confidence && (
                          <div className="flex items-center gap-2">
                            <span className="text-indigo-400 font-semibold min-w-32">Confidence:</span>
                            <div className="flex items-center gap-2">
                              <span className="text-zinc-200 uppercase font-semibold text-xs">{step.data.confidence}</span>
                              <div className="h-1.5 w-24 bg-zinc-800 rounded-full overflow-hidden">
                                <div className="h-full bg-green-500 w-[95%]" />
                              </div>
                            </div>
                          </div>
                        )}
                        {step.data.recommended_action && (
                          <div className="flex items-center gap-2">
                            <span className="text-indigo-400 font-semibold min-w-32">Action:</span>
                            <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-200 text-xs font-semibold border border-zinc-700">
                              {step.data.recommended_action}
                            </span>
                          </div>
                        )}
                        {step.data.reason && (
                          <div className="flex items-start gap-2">
                            <span className="text-indigo-400 font-semibold min-w-32">Reason:</span>
                            <span className="text-zinc-300 text-xs">{step.data.reason}</span>
                          </div>
                        )}
                        {step.data.customer_message && (
                          <div className="flex items-start gap-2 pt-1 border-t border-zinc-800/60 mt-1">
                            <span className="text-cyan-400 font-semibold min-w-32 text-xs">Customer Msg:</span>
                            <span className="text-zinc-300 text-xs italic">"{step.data.customer_message}"</span>
                          </div>
                        )}
                        {step.data.payment_link_url && (
                          <div className="pt-2 border-t border-zinc-800/60 mt-2">
                            <a
                              href={step.data.payment_link_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-all shadow-lg shadow-blue-500/20"
                            >
                              <ExternalLink className="w-4 h-4" /> Open Razorpay Test Checkout ({step.data.payment_link_url})
                            </a>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                {index < displayedSteps.length - 1 && (
                  <div className="ml-2.5 w-px h-6 bg-zinc-800 -mt-2 -mb-2" />
                )}
              </div>
            ))}
            <div ref={stepsEndRef} />
            
            {/* Final Scenario Summary Box */}
            {!isRunning && displayedSteps.length === allSteps.length && finalStatus && (
              <div className="mt-8 pt-6 border-t border-zinc-800 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300">
                <div className={cn(
                  "p-6 rounded-xl border flex flex-col items-center text-center gap-4 relative overflow-hidden",
                  finalStatus === "RECOVERED" ? "bg-green-500/10 border-green-500/30" :
                  finalStatus === "PAYMENT_LINK_CREATED" ? "bg-blue-500/10 border-blue-500/30" :
                  finalStatus === "REQUIRES_HUMAN_APPROVAL" ? "bg-amber-500/10 border-amber-500/30" :
                  "bg-zinc-800/50 border-zinc-700"
                )}>
                  {finalStatus === "RECOVERED" && <div className="absolute -right-4 -top-4 w-32 h-32 bg-green-500/20 blur-3xl rounded-full" />}
                  
                  {finalStatus === "RECOVERED" && <CheckCircle className="w-12 h-12 text-green-400" />}
                  {finalStatus === "PAYMENT_LINK_CREATED" && <Link2 className="w-12 h-12 text-blue-400" />}
                  {finalStatus === "REQUIRES_HUMAN_APPROVAL" && <Lock className="w-12 h-12 text-amber-400" />}
                  {finalStatus === "STOPPED" && <XCircle className="w-12 h-12 text-zinc-400" />}

                  <div>
                    <h3 className={cn(
                      "text-2xl font-bold tracking-tight mb-2",
                      finalStatus === "RECOVERED" ? "text-green-400" :
                      finalStatus === "PAYMENT_LINK_CREATED" ? "text-blue-400" :
                      finalStatus === "REQUIRES_HUMAN_APPROVAL" ? "text-amber-400" :
                      "text-zinc-300"
                    )}>
                      {finalStatus === "RECOVERED" ? "Successfully Recovered" :
                       finalStatus.replace(/_/g, " ")}
                    </h3>

                    {displayedSteps.find((s) => s.data?.payment_link_url)?.data?.payment_link_url && (
                      <div className="mt-4 p-4 rounded-xl bg-blue-500/10 border border-blue-500/30 flex flex-col sm:flex-row items-center justify-between gap-3 w-full max-w-lg">
                        <div className="text-left">
                          <span className="text-xs uppercase tracking-wider font-semibold text-blue-400">Live Razorpay Test Link</span>
                          <p className="text-xs text-zinc-300 font-mono truncate max-w-xs">
                            {displayedSteps.find((s) => s.data?.payment_link_url)?.data?.payment_link_url}
                          </p>
                        </div>
                        <a
                          href={displayedSteps.find((s) => s.data?.payment_link_url)?.data?.payment_link_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-lg transition-all shadow-md shrink-0"
                        >
                          <ExternalLink className="w-4 h-4" /> Open Checkout Link
                        </a>
                      </div>
                    )}

                    {caseId && (
                      <NextLink 
                        href={`/cases/${caseId}`}
                        className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 transition-colors mt-2 text-sm font-medium"
                      >
                        View Case Details <ArrowRight className="w-4 h-4" />
                      </NextLink>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
