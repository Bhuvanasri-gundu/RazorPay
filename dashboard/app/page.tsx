'use client';

import React, { useEffect, useState } from 'react';
import { AlertTriangle, TrendingUp, Target, Activity, ShieldCheck, Database, Loader2, RefreshCw } from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  BarChart, Bar, PieChart, Pie, Cell, Legend 
} from 'recharts';
import { cn } from '@/lib/utils'; // Assuming shadcn/ui setup

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(value);
};

const formatPercent = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'percent',
    maximumFractionDigits: 1
  }).format(value);
};

const CHART_COLORS = {
  green: '#22c55e',
  amber: '#f59e0b',
  blue: '#3b82f6',
  purple: '#8b5cf6',
  red: '#ef4444',
  slate: '#64748b'
};

const PIE_COLORS = [
  CHART_COLORS.amber,
  CHART_COLORS.red,
  CHART_COLORS.purple,
  CHART_COLORS.blue,
  CHART_COLORS.slate,
];

interface DashboardMetrics {
  total_revenue_at_risk: number;
  total_revenue_recovered: number;
  recovery_rate: number;
  active_recovery_cases: number;
  cases_stopped_by_policy: number;
  total_cases: number;
  total_transactions: number;
  total_failed: number;
}

interface DashboardAnalytics {
  cases_by_status: { status: string; count: number }[];
  failure_reason_distribution: { reason: string; count: number }[];
  recovery_action_distribution: { action: string; count: number }[];
  recovery_timeline: { date: string; at_risk: number; recovered: number }[];
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [metricsRes, analyticsRes] = await Promise.all([
        fetch(`${API_BASE}/api/dashboard/metrics`),
        fetch(`${API_BASE}/api/dashboard/analytics`)
      ]);

      if (!metricsRes.ok || !analyticsRes.ok) {
        throw new Error('Failed to fetch dashboard data');
      }

      const metricsData = await metricsRes.json();
      const analyticsData = await analyticsRes.json();

      setMetrics(metricsData);
      setAnalytics(analyticsData);
    } catch (err: any) {
      setError(err.message || 'An error occurred while fetching data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const res = await fetch(`${API_BASE}/api/seed`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to seed database');
      await fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to seed');
    } finally {
      setSeeding(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 space-y-6 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
            <p className="text-muted-foreground">Revenue recovery overview</p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5 animate-pulse">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="rounded-xl border bg-card text-card-foreground shadow h-28"></div>
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2 animate-pulse">
          <div className="rounded-xl border bg-card shadow h-80"></div>
          <div className="rounded-xl border bg-card shadow h-80"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 p-8 pt-6 flex flex-col items-center justify-center min-h-[50vh]">
        <AlertTriangle className="h-10 w-10 text-destructive mb-4" />
        <h2 className="text-xl font-semibold mb-2">Error loading dashboard</h2>
        <p className="text-muted-foreground mb-4">{error}</p>
        <button 
          onClick={fetchData}
          className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 px-4 py-2"
        >
          <RefreshCw className="mr-2 h-4 w-4" /> Try again
        </button>
      </div>
    );
  }

  const isEmpty = !metrics || metrics.total_cases === 0;

  if (isEmpty) {
    return (
      <div className="flex-1 p-8 pt-6 flex flex-col items-center justify-center min-h-[60vh] text-center">
        <Database className="h-16 w-16 text-muted-foreground/50 mb-6" />
        <h2 className="text-2xl font-bold tracking-tight mb-2">No Data Available</h2>
        <p className="text-muted-foreground max-w-md mb-8">
          Your dashboard is currently empty. Seed the database with sample transactions and recovery cases to see the analytics in action.
        </p>
        <button 
          onClick={handleSeed}
          disabled={seeding}
          className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 px-8"
        >
          {seeding ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Database className="mr-2 h-4 w-4" />}
          {seeding ? 'Seeding...' : 'Seed Database'}
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground">Revenue recovery overview</p>
        </div>
      </div>

      {/* Top metrics row */}
      <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-5">
        <MetricCard
          title="Total Revenue at Risk"
          value={formatCurrency(metrics.total_revenue_at_risk)}
          icon={<AlertTriangle className="h-4 w-4 text-amber-500" />}
          iconBg="bg-amber-500/10"
        />
        <MetricCard
          title="Revenue Recovered"
          value={formatCurrency(metrics.total_revenue_recovered)}
          icon={<TrendingUp className="h-4 w-4 text-green-500" />}
          iconBg="bg-green-500/10"
        />
        <MetricCard
          title="Recovery Rate"
          value={`${metrics.recovery_rate}%`}
          icon={<Target className="h-4 w-4 text-blue-500" />}
          iconBg="bg-blue-500/10"
        />
        <MetricCard
          title="Active Cases"
          value={metrics.active_recovery_cases.toLocaleString()}
          icon={<Activity className="h-4 w-4 text-purple-500" />}
          iconBg="bg-purple-500/10"
        />
        <MetricCard
          title="Stopped by Policy"
          value={metrics.cases_stopped_by_policy.toLocaleString()}
          icon={<ShieldCheck className="h-4 w-4 text-slate-500" />}
          iconBg="bg-slate-500/10"
        />
      </div>

      {/* Charts row 1 */}
      <div className="grid gap-4 md:grid-cols-2">
        <ChartCard title="Recovery Timeline">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={analytics?.recovery_timeline || []} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorAtRisk" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_COLORS.amber} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={CHART_COLORS.amber} stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorRecovered" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART_COLORS.green} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={CHART_COLORS.green} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
              <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `₹${value / 1000}k`} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'hsl(var(--popover))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                itemStyle={{ color: 'hsl(var(--popover-foreground))' }}
                formatter={(value: any) => formatCurrency(Number(value))}
              />
              <Legend />
              <Area type="monotone" dataKey="at_risk" name="At Risk" stroke={CHART_COLORS.amber} fillOpacity={1} fill="url(#colorAtRisk)" />
              <Area type="monotone" dataKey="recovered" name="Recovered" stroke={CHART_COLORS.green} fillOpacity={1} fill="url(#colorRecovered)" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Cases by Status">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics?.cases_by_status || []} layout="vertical" margin={{ top: 10, right: 30, left: 40, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(var(--border))" />
              <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis dataKey="status" type="category" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                cursor={{ fill: 'hsl(var(--muted))', opacity: 0.2 }}
                contentStyle={{ backgroundColor: 'hsl(var(--popover))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
              />
              <Bar dataKey="count" name="Cases" fill={CHART_COLORS.blue} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Charts row 2 */}
      <div className="grid gap-4 md:grid-cols-2">
        <ChartCard title="Failure Reason Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analytics?.failure_reason_distribution || []}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="count"
                nameKey="reason"
                label={({ name, percent }: any) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {(analytics?.failure_reason_distribution || []).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: 'hsl(var(--popover))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Recovery Action Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics?.recovery_action_distribution || []} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
              <XAxis dataKey="action" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                cursor={{ fill: 'hsl(var(--muted))', opacity: 0.2 }}
                contentStyle={{ backgroundColor: 'hsl(var(--popover))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
              />
              <Bar dataKey="count" name="Actions" fill={CHART_COLORS.purple} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon, iconBg }: { title: string, value: string | number, icon: React.ReactNode, iconBg: string }) {
  return (
    <div className="rounded-xl border bg-card text-card-foreground shadow">
      <div className="p-6 flex flex-row items-center justify-between space-y-0 pb-2">
        <h3 className="tracking-tight text-sm font-medium">{title}</h3>
        <div className={cn("h-8 w-8 rounded-full flex items-center justify-center", iconBg)}>
          {icon}
        </div>
      </div>
      <div className="p-6 pt-0">
        <div className="text-2xl font-bold">{value}</div>
      </div>
    </div>
  );
}

function ChartCard({ title, children }: { title: string, children: React.ReactNode }) {
  return (
    <div className="rounded-xl border bg-card text-card-foreground shadow col-span-1">
      <div className="p-6 flex flex-col space-y-1.5 pb-2">
        <h3 className="font-semibold leading-none tracking-tight">{title}</h3>
      </div>
      <div className="p-6 pt-0">
        {children}
      </div>
    </div>
  );
}
