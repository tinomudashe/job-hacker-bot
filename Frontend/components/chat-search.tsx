"use client";
import * as React from "react";
import { cn } from "@/lib/utils";
import { Search } from "lucide-react";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
}

interface ChatSearchProps {
  messages?: Message[];
}

export function ChatSearch({ messages = [] }: ChatSearchProps) {
  const [term, setTerm] = React.useState("");
  const [open, setOpen] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const filtered = React.useMemo(() => {
    if (!term) return [];
    return messages.filter(
      (m) => typeof m.content === "string" && m.content.toLowerCase().includes(term.toLowerCase())
    );
  }, [term, messages]);

  function highlight(text: string, term: string) {
    if (!term) return text;
    const re = new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
    return text.split(re).map((part, i) =>
      re.test(part) ? <mark key={i} className="bg-yellow-200 text-black px-0.5 rounded">{part}</mark> : part
    );
  }

  return (
    <div className="relative w-full max-w-[220px]">
      <form
        className="flex items-center gap-2"
        onSubmit={e => { e.preventDefault(); setOpen(true); }}
        autoComplete="off"
      >
        <input
          ref={inputRef}
          type="search"
          placeholder="Search chat..."
          className="h-9 w-full rounded-lg border border-white/20 bg-background/30 px-3 py-1 text-sm shadow-inner focus-visible:ring-2 focus-visible:ring-primary/50"
          value={term}
          onChange={e => { setTerm(e.target.value); setOpen(!!e.target.value); }}
          onFocus={() => setOpen(!!term)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          disabled={messages.length === 0}
        />
        <button type="submit" className="text-muted-foreground hover:text-primary" tabIndex={-1} disabled>
          <Search className="h-4 w-4" />
        </button>
      </form>
      {open && filtered.length > 0 && (
        <div className="absolute left-0 mt-1 w-full max-h-60 overflow-y-auto rounded-lg border bg-popover shadow-lg z-50 animate-fade-in">
          {filtered.slice(0, 10).map((msg) => (
            <div
              key={msg.id}
              className={cn(
                "px-3 py-2 text-sm cursor-pointer hover:bg-accent/40 border-b last:border-b-0",
                msg.isUser ? "text-primary" : "text-foreground"
              )}
              title={typeof msg.content === "string" ? msg.content : undefined}
            >
              {highlight(typeof msg.content === "string" ? msg.content : "", term)}
            </div>
          ))}
          {filtered.length > 10 && (
            <div className="px-3 py-2 text-xs text-muted-foreground">...and {filtered.length - 10} more</div>
          )}
        </div>
      )}
    </div>
  );
} 