"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@clerk/nextjs";
import { format, formatDistanceToNow, parseISO } from "date-fns";
import {
  Activity,
  AlertTriangle,
  ChevronDown,
  CreditCard,
  Filter,
  Loader2,
  UserCheck,
} from "lucide-react";
import * as React from "react";
import { CartesianGrid, Legend, Line, LineChart, XAxis, YAxis } from "recharts";

// --- Type Definitions ---
interface AppStats {
  totalUsers: number;
  weeklyActiveUsers: number;
  activeSubscriptions: number;
  subscriptionConversionRate: number;
  usersMissingEmail: number;
  subscriptionBreakdown?: {
    trialing?: number;
  };
}

interface UserChartData {
  date: string;
  "New Users": number;
  "New Subscriptions": number;
}

interface UsageEvent {
  user_email: string | null;
  action_type: string;
  log_level: "INFO" | "WARNING" | "ERROR";
  success: boolean;
  context: { [key: string]: any } | null;
  created_at: string;
}

interface LogFilters {
  level: "ALL" | "ERROR";
  email: string;
  startDate: string;
  endDate: string;
}

// --- API Fetching Hook ---
const useAdminData = () => {
  const { getToken } = useAuth();
  const [stats, setStats] = React.useState<AppStats | null>(null);
  const [chartData, setChartData] = React.useState<UserChartData[]>([]);
  const [activityLog, setActivityLog] = React.useState<UsageEvent[]>([]);
  const [filters, setFilters] = React.useState<LogFilters>({
    level: "ALL",
    email: "",
    startDate: "",
    endDate: "",
  });
  const [loading, setLoading] = React.useState(true);
  const [isLogLoading, setIsLogLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const fetchLogs = React.useCallback(
    async (currentFilters: LogFilters) => {
      setIsLogLoading(true);
      const token = await getToken();
      if (!token) return;

      const params = new URLSearchParams();
      if (currentFilters.level !== "ALL")
        params.append("level", currentFilters.level);
      if (currentFilters.email)
        params.append("user_email", currentFilters.email);
      if (currentFilters.startDate)
        params.append("start_date", currentFilters.startDate);
      if (currentFilters.endDate)
        params.append("end_date", currentFilters.endDate);

      const logUrl = `/api/admin/activity/activity-log?${params.toString()}`;

      try {
        const logRes = await fetch(logUrl, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!logRes.ok) throw new Error("Failed to fetch activity log.");
        setActivityLog(await logRes.json());
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "An unknown error occurred."
        );
      } finally {
        setIsLogLoading(false);
      }
    },
    [getToken]
  );

  React.useEffect(() => {
    const fetchInitialData = async () => {
      setLoading(true);
      setError(null);
      const token = await getToken();
      if (!token) {
        setLoading(false);
        setError("Authentication token not available.");
        return;
      }
      try {
        const [statsRes, chartRes] = await Promise.all([
          fetch("/api/admin/stats", {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch("/api/admin/stats/users-over-time", {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

        if (!statsRes.ok) throw new Error("Failed to fetch main stats.");
        if (!chartRes.ok) throw new Error("Failed to fetch chart data.");

        setStats(await statsRes.json());
        setChartData(await chartRes.json());
        fetchLogs(filters); // Fetch initial logs
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "An unknown error occurred."
        );
      } finally {
        setLoading(false);
      }
    };
    fetchInitialData();
  }, [getToken]); // Only run on initial load

  return {
    stats,
    chartData,
    activityLog,
    loading,
    error,
    filters,
    setFilters,
    fetchLogs,
    isLogLoading,
  };
};

// --- Main Dashboard Component ---
export default function AdminDashboardPage() {
  const {
    stats,
    chartData,
    activityLog,
    loading,
    error,
    filters,
    setFilters,
    fetchLogs,
    isLogLoading,
  } = useAdminData();

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleApplyFilters = () => {
    fetchLogs(filters);
  };

  const handleClearFilters = () => {
    const clearedFilters: LogFilters = {
      level: "ALL",
      email: "",
      startDate: "",
      endDate: "",
    };
    setFilters(clearedFilters);
    fetchLogs(clearedFilters);
  };

  const chartConfig = {
    "New Users": { label: "New Users", color: "hsl(var(--chart-1))" },
    "New Subscriptions": {
      label: "New Subscriptions",
      color: "hsl(var(--chart-2))",
    },
  } satisfies ChartConfig;

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center h-full">
        <AlertTriangle className="h-10 w-10 text-destructive" />
        <h2 className="mt-4 text-xl font-semibold">
          Failed to Load Dashboard Data
        </h2>
        <p className="mt-2 text-muted-foreground">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Weekly Active Users"
          value={stats?.weeklyActiveUsers}
          icon={<UserCheck />}
          description="Users active in last 7 days"
        />
        <StatCard
          title="Active Subs"
          value={stats?.activeSubscriptions}
          icon={<CreditCard />}
          description={`${
            stats?.subscriptionBreakdown?.trialing || 0
          } on trial`}
        />
        <StatCard
          title="Conversion Rate"
          value={`${stats?.subscriptionConversionRate}%`}
          icon={<Activity />}
          description="From signup to active sub"
        />
        <StatCard
          title="Data Health"
          value={`${stats?.usersMissingEmail} users`}
          icon={<AlertTriangle />}
          description="with missing emails"
          isWarning={stats && stats.usersMissingEmail > 0}
        />
      </div>

      {/* Charts and Recent Signups */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-7 lg:gap-8">
        <Card className="col-span-1 lg:col-span-7">
          <CardHeader>
            <CardTitle>Growth Overview</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <ChartContainer
              config={chartConfig}
              className="min-h-[300px] w-full"
            >
              <LineChart
                data={chartData}
                margin={{ left: 12, right: 12, top: 5, bottom: 5 }}
              >
                <CartesianGrid vertical={false} />
                <XAxis
                  dataKey="date"
                  tickLine={false}
                  axisLine={false}
                  tickMargin={8}
                  tickFormatter={(value) => format(parseISO(value), "MMM d")}
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  tickMargin={8}
                  allowDecimals={false}
                />
                <ChartTooltip
                  cursor={false}
                  content={<ChartTooltipContent />}
                />
                <Legend />
                <Line
                  dataKey="New Users"
                  type="natural"
                  stroke="var(--color-chart-1)"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  dataKey="New Subscriptions"
                  type="natural"
                  stroke="var(--color-chart-2)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* Activity Log */}
      <Card>
        <CardHeader>
          <CardTitle>Activity Log</CardTitle>
          <CardDescription>
            An immutable log of all user and system events.
          </CardDescription>
          <div className="mt-4 flex flex-wrap items-end gap-2">
            <div className="grid gap-1.5">
              <Label htmlFor="emailFilter">User Email</Label>
              <Input
                id="emailFilter"
                name="email"
                value={filters.email}
                onChange={handleFilterChange}
                placeholder="user@example.com"
                className="w-auto"
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="startDate">Start Date</Label>
              <Input
                id="startDate"
                name="startDate"
                type="date"
                value={filters.startDate}
                onChange={handleFilterChange}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="endDate">End Date</Label>
              <Input
                id="endDate"
                name="endDate"
                type="date"
                value={filters.endDate}
                onChange={handleFilterChange}
              />
            </div>
            <Button onClick={handleApplyFilters}>
              <Filter className="mr-2 h-4 w-4" />
              Apply Filters
            </Button>
            <Button variant="ghost" onClick={handleClearFilters}>
              Clear
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLogLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : activityLog.length > 0 ? (
            <div className="space-y-4">
              {activityLog.map((event, index) => (
                <ActivityLogItem key={index} event={event} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-8">
              No events to show for the selected filters.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// --- Reusable Components ---
// (StatCard component is unchanged)
const StatCard: React.FC<any> = ({
  title,
  value,
  icon,
  description,
  isWarning,
}) => (
  <Card>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      <div
        className={`h-4 w-4 ${
          isWarning ? "text-destructive" : "text-muted-foreground"
        }`}
      >
        {icon}
      </div>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value ?? "0"}</div>
      <p className="text-xs text-muted-foreground">{description}</p>
    </CardContent>
  </Card>
);

const ActivityLogItem: React.FC<{ event: UsageEvent }> = ({ event }) => {
  const getLogLevelClass = (level: string) => {
    switch (level) {
      case "ERROR":
        return "bg-destructive";
      case "WARNING":
        return "bg-yellow-500";
      default:
        return "bg-green-500";
    }
  };

  return (
    <Collapsible>
      <div className="flex items-center gap-4">
        <span
          className={`h-2.5 w-2.5 rounded-full ${getLogLevelClass(
            event.log_level
          )} flex-shrink-0`}
        />
        <div className="grid gap-1 flex-1 min-w-0">
          <p className="text-sm font-medium leading-none truncate">
            {event.action_type.replace(/_/g, " ")}
          </p>
          <p className="text-xs text-muted-foreground truncate">
            {event.user_email || "System Event"}
          </p>
        </div>
        <div className="ml-auto font-medium text-xs text-muted-foreground">
          {formatDistanceToNow(parseISO(event.created_at), { addSuffix: true })}
        </div>
        {event.context && (
          <CollapsibleTrigger asChild>
            <Button variant="ghost" size="icon" className="h-6 w-6">
              <ChevronDown className="h-4 w-4" />
            </Button>
          </CollapsibleTrigger>
        )}
      </div>
      {event.context && (
        <CollapsibleContent>
          <pre className="mt-2 text-xs bg-muted/50 p-2 rounded-md overflow-x-auto">
            {JSON.stringify(event.context, null, 2)}
          </pre>
        </CollapsibleContent>
      )}
    </Collapsible>
  );
};
