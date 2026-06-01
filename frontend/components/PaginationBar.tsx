"use client";
import { Button } from "@/components/ui/button";

interface Props {
  page: number;
  pages: number;
  onPageChange: (p: number) => void;
}

export default function PaginationBar({ page, pages, onPageChange }: Props) {
  if (pages <= 1) return null;

  const start = Math.max(1, page - 2);
  const end = Math.min(pages, page + 2);
  const nums: number[] = [];
  for (let i = start; i <= end; i++) nums.push(i);

  return (
    <div className="flex items-center justify-center gap-1 mt-6">
      <Button
        variant="outline"
        size="sm"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
        className="h-8 px-3 text-xs"
      >
        ← 이전
      </Button>
      {start > 1 && (
        <>
          <Button variant="outline" size="sm" className="h-8 w-8 text-xs" onClick={() => onPageChange(1)}>1</Button>
          {start > 2 && <span className="text-zinc-400 text-xs px-1">…</span>}
        </>
      )}
      {nums.map((n) => (
        <Button
          key={n}
          variant={n === page ? "default" : "outline"}
          size="sm"
          className={`h-8 w-8 text-xs ${n === page ? "bg-blue-700 hover:bg-blue-800" : ""}`}
          onClick={() => onPageChange(n)}
        >
          {n}
        </Button>
      ))}
      {end < pages && (
        <>
          {end < pages - 1 && <span className="text-zinc-400 text-xs px-1">…</span>}
          <Button variant="outline" size="sm" className="h-8 w-8 text-xs" onClick={() => onPageChange(pages)}>{pages}</Button>
        </>
      )}
      <Button
        variant="outline"
        size="sm"
        disabled={page >= pages}
        onClick={() => onPageChange(page + 1)}
        className="h-8 px-3 text-xs"
      >
        다음 →
      </Button>
    </div>
  );
}
