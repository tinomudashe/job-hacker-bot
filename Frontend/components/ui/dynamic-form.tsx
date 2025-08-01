"use client";

import * as React from "react";
import { Label } from "./label";
import { Textarea } from "./textarea";
import { Select } from "./select";
import { Input } from "./input";
import { Button } from "./button";

export type FormFieldType =
  | "text"
  | "email"
  | "password"
  | "number"
  | "tel"
  | "url"
  | "date"
  | "file"
  | "textarea"
  | "select"
  | "checkbox";

export interface FormField {
  name: string;
  label: string;
  type: FormFieldType;
  required?: boolean;
  placeholder?: string;
  helperText?: string;
  options?: { value: string; label: string }[];
  rows?: number;
  accept?: string;
  min?: number;
  max?: number;
  defaultValue?: boolean;
}

type FormValue = string | number | File | boolean | null;

interface DynamicFormProps {
  fields: FormField[];
  onSubmit: (data: Record<string, FormValue>) => void;
  defaultValues?: Record<string, FormValue>;
  submitLabel?: string;
}

export function DynamicForm({
  fields,
  onSubmit,
  defaultValues = {},
  submitLabel = "Submit",
}: DynamicFormProps) {
  const [formData, setFormData] = React.useState<Record<string, FormValue>>(defaultValues);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type, checked } = e.target as HTMLInputElement;
    let finalValue: FormValue = value;

    if (type === "file") {
      const fileInput = e.target as HTMLInputElement;
      finalValue = fileInput.files?.[0] || null;
    } else if (type === "number") {
      finalValue = value === "" ? null : Number(value);
    } else if (type === "checkbox") {
      finalValue = checked;
    }

    setFormData((prev) => ({
      ...prev,
      [name]: finalValue,
    }));
  };

  const renderField = (field: FormField) => {
    const commonProps = {
      id: field.name,
      name: field.name,
      required: field.required,
      placeholder: field.placeholder,
      onChange: handleChange,
      className: "w-full",
    };

    const value = formData[field.name];
    const stringValue = 
      value instanceof File ? value.name :
      value === null ? "" :
      String(value);
    
    // Initialize checkbox values with defaultValue
    if (field.type === "checkbox" && formData[field.name] === undefined) {
      setFormData(prev => ({
        ...prev,
        [field.name]: field.defaultValue || false
      }));
    }

    switch (field.type) {
      case "textarea":
        return (
          <Textarea
            {...commonProps}
            value={stringValue}
            rows={field.rows || 3}
          />
        );

      case "select":
        return (
          <Select {...commonProps} value={stringValue}>
            <option value="">Select an option</option>
            {field.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        );

      case "file":
        return (
          <Input
            {...commonProps}
            type="file"
            accept={field.accept}
            value={undefined}
          />
        );

      case "checkbox":
        return (
          <div className="flex items-center space-x-2">
            <Input
              {...commonProps}
              type="checkbox"
              checked={Boolean(value)}
              className="w-4 h-4"
            />
            <Label htmlFor={field.name} className="text-sm font-normal">
              {field.label}
            </Label>
          </div>
        );

      default:
        return (
          <Input
            {...commonProps}
            type={field.type}
            value={stringValue}
            min={field.min}
            max={field.max}
          />
        );
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {fields.map((field) => (
        <div key={field.name} className="space-y-2">
          {field.type !== "checkbox" && (
            <Label htmlFor={field.name}>
              {field.label}
              {field.required && <span className="text-destructive">*</span>}
            </Label>
          )}
          {renderField(field)}
          {field.helperText && (
            <p className="text-sm text-muted-foreground">{field.helperText}</p>
          )}
        </div>
      ))}
      <Button type="submit" className="w-full">
        {submitLabel}
      </Button>
    </form>
  );
} 