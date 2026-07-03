import { X, FileText, Image as ImageIcon, FileAudio, File } from "lucide-react";

export default function FileChip({ file, onRemove }) {
  const isImage = file.type && file.type.startsWith("image/");
  const isAudio = file.type && file.type.startsWith("audio/");
  const isPdf = file.type && file.type === "application/pdf";
  const previewUrl = isImage ? URL.createObjectURL(file) : null;

  let Icon = File;
  if (isImage) Icon = ImageIcon;
  else if (isAudio) Icon = FileAudio;
  else if (isPdf) Icon = FileText;

  return (
    <div className="flex items-center gap-3 bg-[var(--brand-tan-bg)] border border-[var(--border-light)] px-3 py-2.5 rounded-xl shrink-0 shadow-sm relative group max-w-[200px]">
      {/* File type thumbnail or image preview */}
      {previewUrl ? (
        <img
          src={previewUrl}
          alt={file.name}
          className="w-8 h-8 object-cover rounded-md border border-[var(--border-light)]"
        />
      ) : (
        <div className="w-8 h-8 bg-white border border-[var(--border-light)] rounded-md flex items-center justify-center text-[var(--brand-terracotta)]">
          <Icon size={16} strokeWidth={2} />
        </div>
      )}

      {/* File name details */}
      <div className="flex flex-col min-w-0 pr-4">
        <span
          className="text-xs font-semibold text-[var(--foreground)] truncate"
          style={{ fontFamily: '"Inter", sans-serif' }}
        >
          {file.name}
        </span>
        <span
          className="text-[10px] text-[var(--muted-foreground)]"
          style={{ fontFamily: '"JetBrains Mono", monospace' }}
        >
          {(file.size / 1024).toFixed(1)} KB
        </span>
      </div>

      {/* Hover or clean X button */}
      <button
        onClick={() => onRemove(file)}
        className="absolute top-1 right-1 p-1 bg-white/80 hover:bg-white text-[var(--muted-foreground)] hover:text-[var(--brand-terracotta)] rounded-full border border-[var(--border-light)] cursor-pointer transition-colors duration-100"
        aria-label={`Remove ${file.name}`}
      >
        <X size={10} strokeWidth={2.5} />
      </button>
    </div>
  );
}
