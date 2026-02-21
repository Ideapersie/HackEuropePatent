import { useEffect } from "react";
import { X, ExternalLink, AlertOctagon } from "lucide-react";
import type { Contradiction } from "@/types/analysis";

interface Props {
  company: string;
  items: Contradiction[];
  onClose: () => void;
}

export default function ContradictionModal({ company, items, onClose }: Props) {
  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="relative z-10 flex w-full max-w-2xl flex-col max-h-[85vh] overflow-hidden rounded-2xl border border-[#1f2937] bg-[#111827] shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#1f2937] px-6 py-4">
          <div className="flex items-center gap-2">
            <AlertOctagon className="h-5 w-5 text-red-500" />
            <div>
              <h2 className="text-sm font-bold text-white">{company}</h2>
              <p className="text-xs text-gray-500">
                {items.length} contradiction{items.length !== 1 ? "s" : ""} identified
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-500 transition hover:bg-[#1f2937] hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto px-6 py-4 space-y-4">
          {items.length === 0 ? (
            <p className="py-8 text-center text-sm text-gray-600">No contradictions found.</p>
          ) : (
            items.map((item, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-[#1f2937] bg-[#0d1220] p-4"
              >
                {/* Claim */}
                <div className="mb-3 flex items-start gap-3">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-500/20 text-[10px] font-bold text-red-400">
                    {idx + 1}
                  </span>
                  <p className="text-sm font-medium leading-snug text-red-300">
                    &ldquo;{item.claim}&rdquo;
                  </p>
                </div>

                <div className="ml-8 space-y-2.5">
                  {/* Evidence */}
                  <div>
                    <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-600">
                      Patent Evidence
                    </p>
                    <p className="text-xs leading-relaxed text-gray-300">{item.evidence}</p>
                  </div>

                  {/* Why it matters */}
                  <div>
                    <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-600">
                      Why It Matters
                    </p>
                    <p className="text-xs leading-relaxed text-amber-200/80">{item.why_it_matters}</p>
                  </div>

                  {/* Sources */}
                  {item.sources?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {item.sources.map((src, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1 rounded-md bg-[#1f2937] px-2 py-0.5 text-[11px] font-medium text-blue-400"
                        >
                          {src.startsWith("http") ? (
                            <a
                              href={src}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 hover:text-blue-300"
                            >
                              {src.length > 45 ? src.slice(0, 45) + "…" : src}
                              <ExternalLink className="h-2.5 w-2.5" />
                            </a>
                          ) : (
                            src
                          )}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
