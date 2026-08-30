'use client';

import React from 'react';
import { Inter } from 'next/font/google';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Zap, LayoutDashboard, FileSearch, Play, BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  const navItems = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Recovery Cases', href: '/cases', icon: FileSearch },
    { name: 'Live Demo', href: '/demo', icon: Play },
    { name: 'Simulation', href: '/simulation', icon: BarChart3 },
  ];

  return (
    <html lang="en" className="dark">
      <body className={cn(inter.className, "bg-[hsl(var(--background))] text-[hsl(var(--foreground))] min-h-screen flex")}>
        <aside className="w-64 border-r border-[hsl(var(--border))] bg-[hsl(var(--card))] flex-shrink-0 fixed h-full flex flex-col justify-between z-30">
          <div>
            <div className="flex items-center px-6 h-20 border-b border-[hsl(var(--border))]">
              <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 mr-3">
                <Zap className="h-6 w-6 text-emerald-400" />
              </div>
              <div>
                <span className="text-xl font-bold tracking-tight text-zinc-100">REVA</span>
                <span className="block text-[10px] uppercase font-semibold text-emerald-400 tracking-wider">AI Recovery Agent</span>
              </div>
            </div>
            
            <nav className="p-4 space-y-1.5">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center px-3.5 py-3 rounded-lg text-sm font-medium transition-all duration-200",
                      isActive
                        ? "bg-emerald-500/15 text-emerald-400 font-semibold shadow-sm border border-emerald-500/20"
                        : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60"
                    )}
                  >
                    <Icon className={cn("h-5 w-5 mr-3 flex-shrink-0", isActive ? "text-emerald-400" : "text-zinc-500")} />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
        </aside>

        <main className="flex-1 ml-64 overflow-y-auto min-h-screen p-8 bg-[hsl(var(--background))]">
          {children}
        </main>
      </body>
    </html>
  );
}
