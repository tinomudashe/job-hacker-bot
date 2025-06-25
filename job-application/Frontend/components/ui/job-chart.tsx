"use client";

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

interface JobChartProps {
  type: 'bar' | 'line' | 'pie';
  data: any[];
  config: {
    xKey: string;
    yKey: string;
    title?: string;
    dataKey?: string;
  };
}

export function JobChart({ type, data, config }: JobChartProps) {
  const renderChart = () => {
    switch (type) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={config.xKey} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey={config.yKey} fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={config.xKey} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey={config.yKey} stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={100}
                fill="#8884d8"
                dataKey={config.dataKey || config.yKey}
                nameKey={config.xKey}
                label={({ name, percent }) => 
                  `${name}: ${(percent * 100).toFixed(0)}%`
                }
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  return (
    <div className="w-full p-4 bg-card rounded-lg border">
      {config.title && (
        <h3 className="text-lg font-semibold mb-4 text-center">{config.title}</h3>
      )}
      {renderChart()}
    </div>
  );
} 