"use client";

import { Button } from "@/components/ui/button";
import { Logo } from "@/components/ui/logo";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useUser } from "@clerk/nextjs";
import {
  Home,
  LayoutDashboard,
  Loader2,
  Mail,
  ShieldAlert,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import * as React from "react";
import { cn } from "../../lib/utils";

// --- Admin Sidebar Navigation Component ---
const AdminSidebarNav = () => {
  const pathname = usePathname();
  const navItems = [
    {
      href: "/admin",
      label: "Dashboard",
      icon: <LayoutDashboard className="h-4 w-4" />,
    },
    {
      href: "/admin/marketing",
      label: "Marketing",
      icon: <Mail className="h-4 w-4" />,
    },
  ];

  return (
    <nav className="grid items-start px-2 text-sm font-medium lg:px-4">
      {navItems.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            "flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary",
            pathname === item.href && "bg-muted text-primary"
          )}
        >
          {item.icon}
          {item.label}
        </Link>
      ))}
    </nav>
  );
};

// --- Main Admin Layout Component ---
export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoaded } = useUser();
  const isAdmin = user?.publicMetadata?.isAdmin === true;

  if (!isLoaded) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-muted/40 text-center p-4">
        <ShieldAlert className="h-12 w-12 text-destructive" />
        <h1 className="mt-4 text-2xl font-bold">Access Denied</h1>
        <p className="mt-2 text-muted-foreground">
          You do not have permission to view this page.
        </p>
        <Button asChild className="mt-6">
          <Link href="/">
            <Home className="mr-2 h-4 w-4" />
            Return to App
          </Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
      {/* Sidebar */}
      <aside className="hidden border-r bg-background md:block sticky top-0 h-screen">
        <div className="flex h-full max-h-screen flex-col gap-2">
          <header className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
            <Link
              href="/admin"
              className="flex items-center gap-3 text-lg font-semibold text-foreground"
            >
              <Logo className="h-6 w-6" />
              <span>Admin</span>
            </Link>
          </header>
          <div className="flex-1 overflow-auto py-4">
            <AdminSidebarNav />
          </div>
          <footer className="mt-auto p-4 border-t">
            <Button variant="outline" size="sm" asChild className="w-full">
              <Link href="/">Return to App</Link>
            </Button>
          </footer>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex flex-col">
        <header className="flex h-14 items-center gap-4 border-b bg-background/95 px-4 backdrop-blur-sm lg:h-[60px] lg:px-6 sticky top-0 z-30">
          <div className="w-full flex-1">{/* Mobile Nav could go here */}</div>
          <ThemeToggle />
        </header>
        <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
