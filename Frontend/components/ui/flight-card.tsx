import React from 'react';
import { cn } from '@/lib/utils';

export interface Flight {
  time: string;
  airline: string;
  duration: string;
  airports: string;
  tripType: string;
  price: number;
}

interface FlightCardProps {
  flight: Flight;
  onSelect?: () => void;
}

export const FlightCard = ({ flight, onSelect }: FlightCardProps) => {
  return (
    <button
      onClick={onSelect}
      className={cn(
        "flex w-full items-center justify-between rounded-lg border bg-card p-4 text-card-foreground transition-all hover:bg-muted/50",
        "text-left"
      )}
    >
      <div className="flex flex-col gap-0.5">
        <p className="font-semibold">{flight.time}</p>
        <p className="text-sm text-muted-foreground">{flight.airline}</p>
      </div>
      <div className="flex flex-col items-center gap-0.5">
        <p className="text-sm font-medium">{flight.duration}</p>
        <p className="text-xs text-muted-foreground">{flight.airports}</p>
      </div>
      <div className="flex flex-col items-end gap-0.5">
        <p className="font-semibold text-green-500">${flight.price}</p>
        <p className="text-xs text-muted-foreground">{flight.tripType}</p>
      </div>
    </button>
  );
}; 