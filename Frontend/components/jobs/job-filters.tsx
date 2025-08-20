"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { X, RotateCcw } from "lucide-react";

interface JobFiltersProps {
  filters: {
    type: string[];
    level: string[];
    location: string[];
    salaryMin: number;
    salaryMax: number;
  };
  onChange: (filters: JobFiltersProps["filters"]) => void;
  availableLocations?: string[];
  className?: string;
}

const jobTypes = [
  "Full-time",
  "Part-time",
  "Contract",
  "Internship",
  "Remote",
  "Hybrid",
];

const jobLevels = ["Entry", "Mid", "Senior", "Lead", "Manager"];

export function JobFilters({
  filters,
  onChange,
  availableLocations = [],
  className,
}: JobFiltersProps) {
  const handleTypeChange = (type: string, checked: boolean) => {
    const newTypes = checked
      ? [...filters.type, type]
      : filters.type.filter((t) => t !== type);
    onChange({ ...filters, type: newTypes });
  };

  const handleLevelChange = (level: string, checked: boolean) => {
    const newLevels = checked
      ? [...filters.level, level]
      : filters.level.filter((l) => l !== level);
    onChange({ ...filters, level: newLevels });
  };

  const handleLocationChange = (location: string, checked: boolean) => {
    const newLocations = checked
      ? [...filters.location, location]
      : filters.location.filter((l) => l !== location);
    onChange({ ...filters, location: newLocations });
  };

  const handleSalaryChange = (values: number[]) => {
    onChange({
      ...filters,
      salaryMin: values[0],
      salaryMax: values[1],
    });
  };

  const resetFilters = () => {
    onChange({
      type: [],
      level: [],
      location: [],
      salaryMin: 0,
      salaryMax: 500000,
    });
  };

  const activeFilterCount =
    filters.type.length +
    filters.level.length +
    filters.location.length +
    (filters.salaryMin > 0 || filters.salaryMax < 500000 ? 1 : 0);

  return (
    <div
      className={cn(
        "p-6 bg-card border rounded-lg space-y-6",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold">Filters</h3>
          {activeFilterCount > 0 && (
            <Badge variant="secondary">{activeFilterCount} active</Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={resetFilters}
          className="gap-1"
        >
          <RotateCcw className="h-3 w-3" />
          Reset
        </Button>
      </div>

      {/* Active Filters */}
      {activeFilterCount > 0 && (
        <div className="flex flex-wrap gap-2">
          {filters.type.map((type) => (
            <Badge
              key={type}
              variant="secondary"
              className="gap-1 pr-1"
            >
              {type}
              <button
                onClick={() => handleTypeChange(type, false)}
                className="ml-1 hover:bg-background rounded p-0.5"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          {filters.level.map((level) => (
            <Badge
              key={level}
              variant="secondary"
              className="gap-1 pr-1"
            >
              {level}
              <button
                onClick={() => handleLevelChange(level, false)}
                className="ml-1 hover:bg-background rounded p-0.5"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          {filters.location.map((location) => (
            <Badge
              key={location}
              variant="secondary"
              className="gap-1 pr-1"
            >
              {location}
              <button
                onClick={() => handleLocationChange(location, false)}
                className="ml-1 hover:bg-background rounded p-0.5"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          {(filters.salaryMin > 0 || filters.salaryMax < 500000) && (
            <Badge variant="secondary" className="gap-1 pr-1">
              ${filters.salaryMin.toLocaleString()} - $
              {filters.salaryMax.toLocaleString()}
              <button
                onClick={() =>
                  onChange({ ...filters, salaryMin: 0, salaryMax: 500000 })
                }
                className="ml-1 hover:bg-background rounded p-0.5"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Job Type */}
        <div className="space-y-3">
          <Label className="text-sm font-medium">Job Type</Label>
          <div className="space-y-2">
            {jobTypes.map((type) => (
              <div key={type} className="flex items-center space-x-2">
                <Checkbox
                  id={`type-${type}`}
                  checked={filters.type.includes(type)}
                  onCheckedChange={(checked) =>
                    handleTypeChange(type, checked as boolean)
                  }
                />
                <Label
                  htmlFor={`type-${type}`}
                  className="text-sm font-normal cursor-pointer"
                >
                  {type}
                </Label>
              </div>
            ))}
          </div>
        </div>

        {/* Experience Level */}
        <div className="space-y-3">
          <Label className="text-sm font-medium">Experience Level</Label>
          <div className="space-y-2">
            {jobLevels.map((level) => (
              <div key={level} className="flex items-center space-x-2">
                <Checkbox
                  id={`level-${level}`}
                  checked={filters.level.includes(level)}
                  onCheckedChange={(checked) =>
                    handleLevelChange(level, checked as boolean)
                  }
                />
                <Label
                  htmlFor={`level-${level}`}
                  className="text-sm font-normal cursor-pointer"
                >
                  {level}
                </Label>
              </div>
            ))}
          </div>
        </div>

        {/* Location */}
        {availableLocations.length > 0 && (
          <div className="space-y-3">
            <Label className="text-sm font-medium">Location</Label>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {availableLocations.slice(0, 10).map((location) => (
                <div key={location} className="flex items-center space-x-2">
                  <Checkbox
                    id={`location-${location}`}
                    checked={filters.location.includes(location)}
                    onCheckedChange={(checked) =>
                      handleLocationChange(location, checked as boolean)
                    }
                  />
                  <Label
                    htmlFor={`location-${location}`}
                    className="text-sm font-normal cursor-pointer truncate"
                  >
                    {location}
                  </Label>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Salary Range */}
        <div className="space-y-3">
          <Label className="text-sm font-medium">Salary Range</Label>
          <div className="space-y-4">
            <Slider
              value={[filters.salaryMin, filters.salaryMax]}
              onValueChange={handleSalaryChange}
              min={0}
              max={500000}
              step={10000}
              className="w-full"
            />
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>${filters.salaryMin.toLocaleString()}</span>
              <span>${filters.salaryMax.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}