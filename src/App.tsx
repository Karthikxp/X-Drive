import { BarChart2, Check, ChevronLeft, ChevronRight, Columns2, Download, Folder, Image as ImageIcon, Plus, Trash2, Upload, X } from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import React, { useEffect, useRef, useState } from 'react';
import { cn } from './lib/utils';

// --- Types ---
type Screen = 'login' | 'home' | 'upload' | 'view';
type UploadStage = 'idle' | 'uploading' | 'done' | 'processing';

interface ImageData {
  id: string;
  url: string;
  title: string;
  size?: number;
  originalSize?: number;
  ratio?: number;
  originalUrl?: string;
}

// --- Bento grid: 5-item repeating cycle, 2-col base / 3-col on sm+ ---
const BENTO = [
  { cols: 'col-span-2',                 aspect: 'aspect-[16/9]'  },
  { cols: 'col-span-1',                 aspect: 'aspect-square'  },
  { cols: 'col-span-1',                 aspect: 'aspect-[3/4]'   },
  { cols: 'col-span-1',                 aspect: 'aspect-[3/4]'   },
  { cols: 'col-span-1',                 aspect: 'aspect-square'  },
] as const;

const getBento = (i: number) => BENTO[i % BENTO.length];

const ratioBadge = (ratio: number) => {
  const pct = (1 - 1 / ratio) * 100;
  if (pct >= 68) return 'bg-emerald-500/80 text-white';
  if (pct >= 42) return 'bg-amber-400/85 text-black';
  return 'bg-black/55 text-white';
};

// --- Shared components ---

const Logo = ({ className, dark = false }: { className?: string; dark?: boolean }) => (
  <div className={cn('flex items-center gap-2 font-bold text-3xl tracking-tighter select-none', dark ? 'text-white' : 'text-black', className)}>
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="rotate-45">
      <line x1="5" y1="12" x2="19" y2="12" />
      <line x1="12" y1="5" x2="12" y2="19" />
    </svg>
    Drive
  </div>
);

const Spinner = ({ className }: { className?: string }) => (
  <svg className={cn('animate-spin', className)} viewBox="0 0 24 24" fill="none">
    <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
    <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
  </svg>
);

const formatSize = (bytes: number) => {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024).toFixed(0)} KB`;
};

// --- Main App ---

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>(() =>
    localStorage.getItem('xdrive_logged_in') ? 'home' : 'login'
  );
  const [images, setImages] = useState<ImageData[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [slideDirection, setSlideDirection] = useState<number>(0);
  const [uploadStage, setUploadStage] = useState<UploadStage>('idle');
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [uploadedCount, setUploadedCount] = useState(0);
  const [folders, setFolders] = useState<string[]>([]);
  const [activeFolder, setActiveFolder] = useState<string>(
    () => localStorage.getItem('xdrive_active_folder') ?? ''
  );
  const [creatingFolder, setCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [showingSummary, setShowingSummary] = useState(false);
  const [showingSlider, setShowingSlider] = useState(false);
  const [sliderPos, setSliderPos] = useState(50);
  const isDraggingRef = useRef(false);
  const [pendingQueue, setPendingQueue] = useState(0);
  const [preset, setPreset] = useState<'storage' | 'balanced' | 'quality'>('balanced');
  const [compressionDone, setCompressionDone] = useState(0);
  const uploadTotalRef = useRef(0);
  const sliderContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const newFolderInputRef = useRef<HTMLInputElement>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollCountRef = useRef(0);

  const selectedImage = images[selectedIndex] ?? null;

  useEffect(() => {
    fetch('/api/folders')
      .then((r) => r.json())
      .then((data: string[]) => {
        setFolders(data);
        const saved = localStorage.getItem('xdrive_active_folder');
        if (saved && data.includes(saved)) {
          setActiveFolder(saved);
        } else if (data.length > 0) {
          setActiveFolder(data[0]);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (activeFolder) localStorage.setItem('xdrive_active_folder', activeFolder);
  }, [activeFolder]);

  useEffect(() => {
    if (!activeFolder) return;
    fetch(`/api/photos?folder=${encodeURIComponent(activeFolder)}`)
      .then((r) => r.json())
      .then((data: ImageData[]) => setImages(data))
      .catch(() => {});
  }, [activeFolder]);

  useEffect(() => {
    const id = setInterval(() => {
      fetch('/api/queue')
        .then((r) => r.json())
        .then((d: { pending: number }) => setPendingQueue(d.pending))
        .catch(() => {});
    }, 3000);
    return () => clearInterval(id);
  }, []);

  const handleLogin = () => { localStorage.setItem('xdrive_logged_in', '1'); setCurrentScreen('home'); };
  const handleLogout = () => { localStorage.removeItem('xdrive_logged_in'); localStorage.removeItem('xdrive_active_folder'); setCurrentScreen('login'); };

  const handleImageClick = (img: ImageData) => {
    const idx = images.findIndex((i) => i.id === img.id);
    setSelectedIndex(idx >= 0 ? idx : 0);
    setSlideDirection(0);
    setCurrentScreen('view');
  };

  const closeImageView = () => { setConfirmingDelete(false); setShowingSummary(false); setShowingSlider(false); setCurrentScreen('home'); };

  const goNext = () => {
    if (selectedIndex < images.length - 1) {
      setConfirmingDelete(false); setShowingSummary(false); setShowingSlider(false);
      setSlideDirection(1);
      setSelectedIndex((i) => i + 1);
    }
  };

  const goPrev = () => {
    if (selectedIndex > 0) {
      setConfirmingDelete(false); setShowingSummary(false); setShowingSlider(false);
      setSlideDirection(-1);
      setSelectedIndex((i) => i - 1);
    }
  };

  useEffect(() => {
    if (currentScreen !== 'view') return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') goNext();
      else if (e.key === 'ArrowLeft') goPrev();
      else if (e.key === 'Escape') closeImageView();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentScreen, selectedIndex]);

  const stopPolling = () => {
    if (pollTimerRef.current) { clearInterval(pollTimerRef.current); pollTimerRef.current = null; }
    pollCountRef.current = 0;
  };

  const clearUpload = () => {
    stopPolling();
    previewUrls.forEach((u) => URL.revokeObjectURL(u));
    setPendingFiles([]); setPreviewUrls([]); setUploadedCount(0);
    setCompressionDone(0); uploadTotalRef.current = 0;
    setUploadStage('idle'); setCurrentScreen('home');
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const picked = Array.from(event.target.files ?? []) as File[];
    if (picked.length === 0) return;
    const newPreviews = picked.map((f) => URL.createObjectURL(f));
    setPendingFiles((prev) => [...prev, ...picked]);
    setPreviewUrls((prev) => [...prev, ...newPreviews]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleRemoveFile = (index: number) => {
    URL.revokeObjectURL(previewUrls[index]);
    setPendingFiles((prev) => prev.filter((_, i) => i !== index));
    setPreviewUrls((prev) => prev.filter((_, i) => i !== index));
  };

  const handleCreateFolder = async () => {
    const name = newFolderName.trim();
    if (!name) return;
    try {
      await fetch('/api/folders', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) });
      setFolders((prev) => [...prev, name]);
      setActiveFolder(name);
    } catch (err) { console.error(err); }
    setNewFolderName('');
    setCreatingFolder(false);
  };

  const handleDeleteImage = async () => {
    if (!selectedImage) return;
    const parts = selectedImage.url.split('/');
    const folder = decodeURIComponent(parts[2] ?? '');
    const filename = parts[3] ?? '';
    if (!folder || !filename) return;
    try {
      await fetch(`/api/photos?folder=${encodeURIComponent(folder)}&filename=${encodeURIComponent(filename)}`, { method: 'DELETE' });
    } catch (err) { console.error(err); }
    const remaining = images.filter((img) => img.id !== selectedImage.id);
    setImages(remaining);
    setConfirmingDelete(false);
    if (remaining.length === 0) { setCurrentScreen('home'); }
    else { setSelectedIndex(Math.min(selectedIndex, remaining.length - 1)); }
  };

  const startPollingForResults = (knownCount: number, folder: string, expectedCount: number) => {
    stopPolling();
    pollCountRef.current = 0;
    const MAX_POLLS = 120; // 10 min at 5s intervals
    pollTimerRef.current = setInterval(async () => {
      pollCountRef.current += 1;
      try {
        const r = await fetch(`/api/photos?folder=${encodeURIComponent(folder)}`);
        const data: ImageData[] = await r.json();
        const newlyDone = Math.max(0, data.length - knownCount);
        setCompressionDone(newlyDone);

        if (newlyDone >= expectedCount) {
          // Preload every new image so the gallery appears instantly with real content
          const newPhotos = data.slice(0, newlyDone);
          await Promise.all(
            newPhotos.map(
              (img) =>
                new Promise<void>((res) => {
                  const el = new Image();
                  el.onload = () => res();
                  el.onerror = () => res();
                  el.src = img.url;
                })
            )
          );
          setImages(data);
          stopPolling();
          setUploadStage('done');
          setTimeout(clearUpload, 1000);
        }
      } catch { /* ignore transient errors */ }
      if (pollCountRef.current >= MAX_POLLS) { stopPolling(); clearUpload(); }
    }, 5000);
  };

  const handleUpload = async () => {
    if (pendingFiles.length === 0) return;
    const total = pendingFiles.length;
    uploadTotalRef.current = total;
    setCompressionDone(0);
    setUploadStage('uploading');
    try {
      for (let i = 0; i < total; i++) {
        setUploadedCount(i + 1);
        const file = pendingFiles[i];
        const formData = new FormData();
        formData.append('image', file, file.name);
        formData.append('originalName', file.name.replace(/\.[^/.]+$/, ''));
        formData.append('folder', activeFolder);
        formData.append('preset', preset);
        const response = await fetch('/api/upload', { method: 'POST', body: formData });
        if (!response.ok) throw new Error(`Upload failed for ${file.name}`);
      }
      setUploadStage('processing');
      startPollingForResults(images.length, activeFolder, total);
    } catch (err) { console.error(err); setUploadStage('idle'); }
  };

  // ─────────────────────────────────────────────────────────────
  // LOGIN SCREEN
  // ─────────────────────────────────────────────────────────────
  if (currentScreen === 'login') {
    return (
      <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-6 font-sans relative overflow-hidden">
        {/* Ambient glows */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[800px] h-[800px] rounded-full bg-white/[0.025] blur-3xl" />
          <div className="absolute bottom-0 left-0 w-80 h-80 rounded-full bg-indigo-600/10 blur-3xl" />
          <div className="absolute bottom-0 right-0 w-80 h-80 rounded-full bg-violet-600/8 blur-3xl" />
          {/* Dot grid */}
          <svg width="100%" height="100%" className="absolute inset-0 opacity-[0.35]" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="dot-grid" x="0" y="0" width="32" height="32" patternUnits="userSpaceOnUse">
                <circle cx="1" cy="1" r="1" fill="white" fillOpacity="0.18" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#dot-grid)" />
          </svg>
        </div>

        <div className="relative z-10 flex flex-col items-center w-full max-w-sm">
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, y: -16, scale: 0.92 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
            className="mb-10"
          >
            <Logo dark />
          </motion.div>

          {/* Headline */}
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
            className="text-center mb-10"
          >
            <h1 className="text-[2.5rem] font-bold text-white tracking-tight leading-[1.15]">
              Affordable cloud<br />storage for everyone
            </h1>
            <p className="mt-3 text-white/40 text-sm leading-relaxed">
              AI-powered compression. Up to 15× smaller files.
            </p>
          </motion.div>

          {/* Auth buttons */}
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
            className="w-full space-y-3"
          >
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleLogin}
              className="w-full py-[1.1rem] rounded-full font-semibold bg-white text-black flex items-center justify-center gap-3 text-[15px] shadow-[0_2px_20px_rgba(255,255,255,0.12)]"
            >
              <svg className="w-[18px] h-[18px]" viewBox="0 0 814 1000" fill="currentColor">
                <path d="M788.1 340.9c-5.8 4.5-108.2 62.2-108.2 190.5 0 148.4 130.3 200.9 134.2 202.2-.6 3.2-20.7 71.9-68.7 141.9-42.8 61.6-87.5 123.1-155.5 123.1s-85.5-39.5-164-39.5c-76 0-103.7 40.8-165.9 40.8s-105-37.5-155.5-127.4C46.7 790.7 0 663 0 541.8c0-207.5 135.4-317.3 269-317.3 70.1 0 128.4 46.4 172.5 46.4 42.8 0 109.6-49.1 189.6-49.1 30.5 0 110.5 2.6 171.3 64.3zm-217.2-141.5c31.1-36.9 53.1-88.1 53.1-139.3 0-7.1-.6-14.3-1.9-20.1-50.6 1.9-110.8 33.7-147.1 75.8-28.5 32.4-55.1 83.6-55.1 135.5 0 7.8 1.3 15.6 1.9 18.1 3.2.6 8.4 1.3 13.6 1.3 45.4 0 102.5-30.4 135.5-71.3z" />
              </svg>
              Continue with Apple
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleLogin}
              className="w-full py-[1.1rem] rounded-full font-semibold bg-white/8 text-white border border-white/10 flex items-center justify-center gap-3 text-[15px] hover:bg-white/12 transition-colors"
            >
              <svg className="w-[18px] h-[18px]" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Continue with Google
            </motion.button>
          </motion.div>

          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            onClick={handleLogin}
            className="mt-8 text-white/20 text-xs hover:text-white/45 transition-colors"
          >
            ← dev bypass login
          </motion.button>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────
  // UPLOAD SCREEN
  // ─────────────────────────────────────────────────────────────
  if (currentScreen === 'upload') {
    const isProcessing = uploadStage !== 'idle';
    const isCompressing = uploadStage === 'processing';
    const hasFiles = pendingFiles.length > 0;

    return (
      <div className="fixed inset-0 bg-zinc-950 text-white font-sans flex flex-col overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center px-6 pt-6 pb-4 flex-shrink-0">
          <Logo dark />
          <motion.button
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.92 }}
            onClick={clearUpload}
            className="p-2 rounded-full bg-white/10 hover:bg-white/18 transition-colors"
          >
            <X className="w-5 h-5" />
          </motion.button>
        </div>

        <div className="flex-1 flex flex-col w-full max-w-md mx-auto px-6 pb-8">
          <h1 className="text-4xl font-bold tracking-tight mb-6">File upload</h1>

          <input type="file" accept="image/*" multiple className="hidden" ref={fileInputRef} onChange={handleFileChange} />

          {!hasFiles ? (
            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => fileInputRef.current?.click()}
              className="w-full aspect-square max-w-[240px] mx-auto border-2 border-dashed border-white/15 rounded-3xl flex flex-col items-center justify-center gap-4 hover:border-white/30 hover:bg-white/4 transition-all"
            >
              <motion.div
                animate={{ y: [0, -6, 0] }}
                transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
              >
                <Folder className="w-16 h-16 text-white/35" strokeWidth={1} />
              </motion.div>
              <p className="text-sm font-medium text-white/40">Tap to choose photos</p>
            </motion.button>
          ) : (
            <div className="flex-1 overflow-y-auto">
              <div className="grid grid-cols-3 gap-2">
                {pendingFiles.map((file, i) => (
                  <motion.div
                    key={`${file.name}-${i}`}
                    initial={{ opacity: 0, scale: 0.82 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.22, delay: i * 0.04, ease: [0.23, 1, 0.32, 1] }}
                    className="relative aspect-square rounded-2xl overflow-hidden bg-white/5"
                  >
                    <img src={previewUrls[i]} alt={file.name} className="w-full h-full object-cover" />
                    {/* Uploading phase: show check per uploaded file, spinner on current */}
                    {uploadStage === 'uploading' && i < uploadedCount && (
                      <div className="absolute inset-0 bg-black/55 flex items-center justify-center">
                        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 400, damping: 22 }}>
                          <Check className="w-6 h-6 text-emerald-400" strokeWidth={3} />
                        </motion.div>
                      </div>
                    )}
                    {uploadStage === 'uploading' && i === uploadedCount && (
                      <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                        <Spinner className="w-6 h-6 text-white" />
                      </div>
                    )}
                    {/* Processing phase: show check for already-compressed, pulsing ring for pending */}
                    {uploadStage === 'processing' && i < compressionDone && (
                      <div className="absolute inset-0 bg-black/55 flex items-center justify-center">
                        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 380, damping: 22 }}>
                          <Check className="w-6 h-6 text-emerald-400" strokeWidth={3} />
                        </motion.div>
                      </div>
                    )}
                    {uploadStage === 'processing' && i >= compressionDone && (
                      <div className="absolute inset-0 bg-black/65 flex flex-col items-center justify-center gap-1.5">
                        <Spinner className="w-5 h-5 text-white/70" />
                      </div>
                    )}
                    {uploadStage === 'done' && (
                      <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                        <Check className="w-6 h-6 text-emerald-400" strokeWidth={3} />
                      </div>
                    )}
                    {!isProcessing && (
                      <button
                        onClick={() => handleRemoveFile(i)}
                        className="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-black/70 hover:bg-black flex items-center justify-center transition-colors"
                      >
                        <X className="w-3 h-3 text-white" />
                      </button>
                    )}
                    <div className="absolute bottom-0 inset-x-0 px-2 py-1 bg-gradient-to-t from-black/65 to-transparent">
                      <p className="text-white/75 text-[10px] truncate">{formatSize(file.size)}</p>
                    </div>
                  </motion.div>
                ))}
                {!isProcessing && (
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="aspect-square rounded-2xl border-2 border-dashed border-white/15 flex flex-col items-center justify-center gap-1 hover:border-white/30 hover:bg-white/5 transition-all"
                  >
                    <Plus className="w-6 h-6 text-white/35" />
                    <span className="text-white/35 text-[11px]">Add more</span>
                  </button>
                )}
              </div>

              <div className="mt-4 flex items-center gap-2">
                {uploadStage === 'processing' && (
                  <Spinner className="w-3.5 h-3.5 text-white/40 flex-shrink-0" />
                )}
                {uploadStage === 'done' && (
                  <Check className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" strokeWidth={3} />
                )}
                <p className="text-white/40 text-sm">
                  {uploadStage === 'uploading'
                    ? `Uploading ${uploadedCount} of ${pendingFiles.length}…`
                    : uploadStage === 'processing'
                    ? compressionDone > 0
                      ? `Compressed ${compressionDone} of ${uploadTotalRef.current}… checking every 5s`
                      : `Compressing ${uploadTotalRef.current} photo${uploadTotalRef.current !== 1 ? 's' : ''}… this may take a minute`
                    : uploadStage === 'done'
                    ? `All ${uploadTotalRef.current} photo${uploadTotalRef.current !== 1 ? 's' : ''} ready — loading…`
                    : `${pendingFiles.length} photo${pendingFiles.length !== 1 ? 's' : ''} selected`}
                </p>
              </div>
            </div>
          )}

          {/* Preset selector */}
          <div className="mt-6">
            <p className="text-white/40 text-[11px] font-semibold uppercase tracking-widest mb-3">Compression preset</p>
            <div className="grid grid-cols-3 gap-2">
              {([
                { id: 'storage',  label: 'Storage',  sub: 'Max compression',     ratio: '8–15×' },
                { id: 'balanced', label: 'Balanced', sub: 'Smart trade-off',      ratio: '4–8×'  },
                { id: 'quality',  label: 'Quality',  sub: 'Best visual fidelity', ratio: '2–4×'  },
              ] as const).map(({ id, label, sub, ratio }) => (
                <motion.button
                  key={id}
                  onClick={() => setPreset(id)}
                  disabled={isProcessing}
                  whileTap={!isProcessing ? { scale: 0.96 } : {}}
                  className={cn(
                    'rounded-2xl px-3 py-3.5 text-left transition-all duration-200 relative overflow-hidden',
                    preset === id
                      ? 'bg-white text-black shadow-[0_0_0_1px_rgba(255,255,255,0.15),0_4px_16px_rgba(255,255,255,0.08)]'
                      : 'bg-white/7 text-white/55 hover:bg-white/11 border border-white/8'
                  )}
                >
                  <p className={cn('text-sm font-bold', preset === id ? 'text-black' : 'text-white')}>{label}</p>
                  <p className={cn('text-[10px] mt-0.5 leading-tight', preset === id ? 'text-black/50' : 'text-white/32')}>{sub}</p>
                  <p className={cn('text-xs font-semibold mt-1.5', preset === id ? 'text-black/65' : 'text-white/38')}>{ratio}</p>
                </motion.button>
              ))}
            </div>
          </div>

          {/* CTA */}
          <div className="mt-5 pb-2">
            {!hasFiles ? (
              <motion.button
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}
                onClick={() => fileInputRef.current?.click()}
                className="w-full py-4 rounded-full font-semibold bg-white text-black flex items-center justify-center gap-2 text-[15px]"
              >
                <Upload className="w-5 h-5" />
                Browse files
              </motion.button>
            ) : (
              <button
                onClick={handleUpload}
                disabled={isProcessing}
                className={cn(
                  'w-full py-4 rounded-full font-semibold flex items-center justify-center gap-3 transition-all duration-300 text-[15px]',
                  uploadStage === 'idle'     && 'bg-white text-black hover:bg-gray-100 active:scale-95',
                  uploadStage === 'uploading' && 'bg-blue-500/18 text-blue-300 cursor-not-allowed',
                  isCompressing              && 'bg-amber-500/18 text-amber-300 cursor-not-allowed',
                  uploadStage === 'done'     && 'bg-emerald-500/18 text-emerald-300 cursor-not-allowed'
                )}
              >
                {uploadStage === 'idle' && <><Upload className="w-5 h-5" />Upload {pendingFiles.length} photo{pendingFiles.length !== 1 ? 's' : ''}</>}
                {uploadStage === 'uploading' && <><Spinner className="w-5 h-5" />Uploading {uploadedCount} of {pendingFiles.length}…</>}
                {isCompressing && (
                  <>
                    <Spinner className="w-5 h-5" />
                    {compressionDone > 0
                      ? `${compressionDone} / ${uploadTotalRef.current} compressed…`
                      : 'Compressing…'}
                  </>
                )}
                {uploadStage === 'done' && <><Check className="w-5 h-5" />Done!</>}
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────
  // VIEW SCREEN
  // ─────────────────────────────────────────────────────────────
  if (currentScreen === 'view' && selectedImage) {
    const hasPrev = selectedIndex > 0;
    const hasNext = selectedIndex < images.length - 1;

    const slideVariants = {
      enter: (dir: number) => ({ x: dir >= 0 ? '100%' : '-100%', opacity: 0 }),
      center: { x: 0, opacity: 1 },
      exit: (dir: number) => ({ x: dir >= 0 ? '-100%' : '100%', opacity: 0 }),
    };

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.18 }}
        className="fixed inset-0 bg-black z-50 flex flex-col font-sans"
      >
        {/* Top bar */}
        <div className="flex-shrink-0 flex items-center justify-between px-5 pt-5 pb-2 z-20">
          <button
            onClick={closeImageView}
            className="bg-white/12 backdrop-blur-md text-white px-4 py-2 rounded-full font-semibold flex items-center gap-2 text-sm hover:bg-white/22 transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="rotate-45">
              <line x1="5" y1="12" x2="19" y2="12" />
              <line x1="12" y1="5" x2="12" y2="19" />
            </svg>
            Drive
          </button>
          <div className="flex items-center gap-2">
            <a
              href={selectedImage.url}
              download={selectedImage.title + '.avif'}
              className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 transition-colors flex items-center justify-center"
              title="Download"
            >
              <Download className="w-4 h-4 text-white/70" />
            </a>
            {selectedImage.originalUrl && (
              <button
                onClick={() => { setShowingSlider(true); setShowingSummary(false); setConfirmingDelete(false); setSliderPos(50); }}
                className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 transition-colors flex items-center justify-center"
                title="Compare original vs compressed"
              >
                <Columns2 className="w-4 h-4 text-white/70" />
              </button>
            )}
            <button
              onClick={() => { setShowingSummary(true); setShowingSlider(false); setConfirmingDelete(false); }}
              className="h-9 px-3 rounded-full bg-white/10 hover:bg-white/20 transition-colors flex items-center gap-1.5"
              title="Visualize compression"
            >
              <BarChart2 className="w-4 h-4 text-white/70" />
              <span className="text-white/70 text-xs font-medium">Visualize</span>
            </button>
            <button
              onClick={() => setConfirmingDelete(true)}
              className="w-9 h-9 rounded-full bg-white/10 hover:bg-red-500/30 transition-colors flex items-center justify-center"
              title="Delete photo"
            >
              <Trash2 className="w-4 h-4 text-white/70" />
            </button>
          </div>
        </div>

        {/* Image area */}
        <div className="flex-1 relative overflow-hidden min-h-0">
          <AnimatePresence initial={false} custom={slideDirection} mode="popLayout">
            <motion.div
              key={selectedImage.id}
              custom={slideDirection}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ type: 'spring', stiffness: 350, damping: 36, mass: 0.8 }}
              drag="x"
              dragConstraints={{ left: 0, right: 0 }}
              dragElastic={0.12}
              onDragEnd={(_, info) => {
                const swipedFar = Math.abs(info.offset.x) > 70;
                const swipedFast = Math.abs(info.velocity.x) > 400;
                if (swipedFar || swipedFast) { if (info.offset.x < 0) goNext(); else goPrev(); }
              }}
              className="absolute inset-0 flex items-center justify-center px-4 py-2 cursor-grab active:cursor-grabbing"
            >
              <img
                src={selectedImage.url}
                alt={selectedImage.title}
                className="max-w-full max-h-full object-contain rounded-2xl select-none"
                draggable={false}
              />
            </motion.div>
          </AnimatePresence>

          {hasPrev && (
            <button onClick={goPrev} className="absolute left-0 inset-y-0 w-16 z-10 flex items-center justify-start pl-3 group">
              <div className="w-9 h-9 rounded-full bg-black/40 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <ChevronLeft className="w-5 h-5 text-white" />
              </div>
            </button>
          )}
          {hasNext && (
            <button onClick={goNext} className="absolute right-0 inset-y-0 w-16 z-10 flex items-center justify-end pr-3 group">
              <div className="w-9 h-9 rounded-full bg-black/40 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <ChevronRight className="w-5 h-5 text-white" />
              </div>
            </button>
          )}
        </div>

        {/* Bottom info */}
        <div className="flex-shrink-0 px-6 pt-3 pb-8">
          <div className="flex items-end justify-between gap-4">
            <div className="min-w-0">
              <h2 className="text-white text-2xl font-bold tracking-tight truncate">{selectedImage.title}</h2>
              <div className="flex items-center gap-3 mt-1">
                {selectedImage.size != null && (
                  <span className="text-white/40 text-sm">{formatSize(selectedImage.size)}</span>
                )}
                {selectedImage.ratio != null && (
                  <span className={cn('text-[11px] font-bold px-2 py-0.5 rounded-full', ratioBadge(selectedImage.ratio))}>
                    ↓{Math.round((1 - 1 / selectedImage.ratio) * 100)}% smaller
                  </span>
                )}
              </div>
            </div>
            {images.length > 1 && (
              <span className="flex-shrink-0 text-white/35 text-sm font-medium tabular-nums mb-0.5">
                {selectedIndex + 1} / {images.length}
              </span>
            )}
          </div>
        </div>

        {/* Compression summary overlay */}
        <AnimatePresence>
          {showingSummary && (() => {
            const summaryFilename = selectedImage.id.replace(/_step4_final_compressed\.[^.]+$/, '_compression_summary.png');
            const summaryUrl = `/output/${encodeURIComponent(summaryFilename)}`;
            return (
              <motion.div
                initial={{ opacity: 0, y: '100%' }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: '100%' }}
                transition={{ type: 'spring', stiffness: 320, damping: 36 }}
                className="absolute inset-0 z-40 bg-black flex flex-col"
              >
                <div className="flex-shrink-0 flex items-center justify-between px-5 pt-5 pb-3 border-b border-white/10">
                  <div>
                    <p className="text-white font-semibold text-sm">Compression pipeline</p>
                    <p className="text-white/40 text-xs mt-0.5">{selectedImage.title}</p>
                  </div>
                  <button onClick={() => setShowingSummary(false)} className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 transition-colors flex items-center justify-center">
                    <X className="w-4 h-4 text-white" />
                  </button>
                </div>
                <div className="flex-1 overflow-x-auto overflow-y-hidden h-full">
                  <img
                    src={summaryUrl}
                    alt="Compression summary"
                    style={{ height: '100%', width: 'auto', maxWidth: 'none', touchAction: 'pan-x pinch-zoom', display: 'block' }}
                    onError={(e) => {
                      (e.currentTarget as HTMLImageElement).style.display = 'none';
                      (e.currentTarget.nextElementSibling as HTMLElement | null)?.style.setProperty('display', 'flex');
                    }}
                  />
                  <div style={{ display: 'none' }} className="h-full min-h-[200px] items-center justify-center text-white/30 text-sm">
                    Summary not available yet — compression may still be running.
                  </div>
                </div>
              </motion.div>
            );
          })()}
        </AnimatePresence>

        {/* Split slider */}
        <AnimatePresence>
          {showingSlider && selectedImage.originalUrl && (
            <motion.div
              initial={{ opacity: 0, y: '100%' }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: '100%' }}
              transition={{ type: 'spring', stiffness: 320, damping: 36 }}
              className="absolute inset-0 z-40 bg-black flex flex-col"
            >
              <div className="flex-shrink-0 flex items-center justify-between px-5 pt-5 pb-3 border-b border-white/10">
                <div>
                  <p className="text-white font-semibold text-sm">Compare</p>
                  <p className="text-white/40 text-xs mt-0.5">Drag to reveal original vs compressed</p>
                </div>
                <button onClick={() => setShowingSlider(false)} className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 transition-colors flex items-center justify-center">
                  <X className="w-4 h-4 text-white" />
                </button>
              </div>
              <div
                ref={sliderContainerRef}
                className="flex-1 relative overflow-hidden"
                style={{ touchAction: 'none', userSelect: 'none', cursor: 'ew-resize' }}
                onPointerDown={(e) => {
                  isDraggingRef.current = true;
                  (e.currentTarget as HTMLDivElement).setPointerCapture(e.pointerId);
                  const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
                  setSliderPos(Math.min(100, Math.max(0, ((e.clientX - rect.left) / rect.width) * 100)));
                }}
                onPointerMove={(e) => {
                  if (!isDraggingRef.current) return;
                  const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
                  setSliderPos(Math.min(100, Math.max(0, ((e.clientX - rect.left) / rect.width) * 100)));
                }}
                onPointerUp={() => { isDraggingRef.current = false; }}
                onPointerCancel={() => { isDraggingRef.current = false; }}
              >
                <img src={selectedImage.url} alt="Compressed" className="absolute inset-0 w-full h-full object-contain" draggable={false} style={{ pointerEvents: 'none' }} />
                <img src={selectedImage.originalUrl} alt="Original" className="absolute inset-0 w-full h-full object-contain" style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)`, pointerEvents: 'none' }} draggable={false} />
                <div className="absolute top-0 bottom-0 w-0.5 bg-white/80 shadow-[0_0_12px_rgba(255,255,255,0.55)] z-10" style={{ left: `${sliderPos}%`, transform: 'translateX(-50%)', pointerEvents: 'none' }}>
                  <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-11 h-11 rounded-full bg-white shadow-xl flex items-center justify-center gap-0.5">
                    <ChevronLeft className="w-3.5 h-3.5 text-black" />
                    <ChevronRight className="w-3.5 h-3.5 text-black" />
                  </div>
                </div>
                {sliderPos > 12 && (
                  <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-black/60 backdrop-blur-sm text-white text-xs font-semibold pointer-events-none">Original</div>
                )}
                {sliderPos < 88 && (
                  <div className="absolute top-4 right-4 px-3 py-1 rounded-full bg-black/60 backdrop-blur-sm text-white text-xs font-semibold pointer-events-none">
                    Compressed
                    {selectedImage.ratio && <span className="ml-1.5 opacity-70">↓{Math.round((1 - 1 / selectedImage.ratio) * 100)}%</span>}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Delete confirmation */}
        <AnimatePresence>
          {confirmingDelete && (
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 24 }}
              transition={{ duration: 0.2 }}
              className="absolute inset-x-0 bottom-0 z-30 px-6 pb-10 pt-6 bg-gradient-to-t from-black via-black/90 to-transparent"
            >
              <p className="text-white text-lg font-semibold mb-1">Delete this photo?</p>
              <p className="text-white/40 text-sm mb-6">
                This will permanently remove it from <span className="text-white/60 font-medium">{decodeURIComponent(selectedImage.url.split('/')[2] ?? '')}</span>.
              </p>
              <div className="flex gap-3">
                <button onClick={() => setConfirmingDelete(false)} className="flex-1 py-3.5 rounded-full bg-white/12 text-white font-semibold hover:bg-white/18 transition-colors">
                  Cancel
                </button>
                <motion.button
                  whileTap={{ scale: 0.96 }}
                  onClick={handleDeleteImage}
                  className="flex-1 py-3.5 rounded-full bg-red-500 text-white font-semibold hover:bg-red-600 transition-colors flex items-center justify-center gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </motion.button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    );
  }

  // ─────────────────────────────────────────────────────────────
  // HOME SCREEN
  // ─────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-white font-sans">
      {/* Header */}
      <header className="flex justify-between items-center px-5 h-[60px] sticky top-0 bg-white/75 backdrop-blur-xl z-10 border-b border-black/[0.06]">
        <Logo />
        <div className="flex items-center gap-3">
          <AnimatePresence>
            {pendingQueue > 0 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.85, x: 8 }}
                animate={{ opacity: 1, scale: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.85, x: 8 }}
                transition={{ duration: 0.2 }}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-black text-white text-xs font-semibold rounded-full"
              >
                <Spinner className="w-3 h-3" />
                {pendingQueue} compressing…
              </motion.div>
            )}
          </AnimatePresence>
          <motion.button
            whileHover={{ scale: 1.06 }}
            whileTap={{ scale: 0.92 }}
            onClick={handleLogout}
            className="w-9 h-9 rounded-full overflow-hidden ring-2 ring-black/10 hover:ring-black/25 transition-all"
          >
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="Avatar" className="w-full h-full object-cover bg-gray-100" />
          </motion.button>
        </div>
      </header>

      <main className="px-5 max-w-3xl mx-auto pb-28">
        {/* Albums section */}
        <section className="mt-6">
          <div className="flex items-baseline justify-between mb-4">
            <h2 className="text-2xl font-bold tracking-tight">Albums</h2>
            {images.length > 0 && (
              <span className="text-sm text-black/35 font-medium">{images.length} photo{images.length !== 1 ? 's' : ''}</span>
            )}
          </div>

          {/* Animated folder pills */}
          <div className="flex overflow-x-auto -mx-5 px-5 pb-3 gap-2 no-scrollbar items-center">
            {folders.map((f) => (
              <button
                key={f}
                onClick={() => setActiveFolder(f)}
                className="relative flex-shrink-0 px-5 py-2 rounded-full text-sm font-medium"
              >
                {activeFolder === f && (
                  <motion.div
                    layoutId="pill-active"
                    className="absolute inset-0 bg-black rounded-full"
                    transition={{ type: 'spring', stiffness: 400, damping: 34 }}
                  />
                )}
                <span className={cn('relative z-10 transition-colors duration-150', activeFolder === f ? 'text-white' : 'text-black/55 hover:text-black')}>
                  {f}
                </span>
              </button>
            ))}
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              onClick={() => setCreatingFolder(true)}
              className="flex-shrink-0 px-4 py-2 rounded-full border border-dashed border-black/20 text-sm font-medium text-black/35 hover:bg-gray-50 hover:border-black/35 transition-colors flex items-center gap-1.5 whitespace-nowrap"
            >
              <Plus className="w-3.5 h-3.5" />
              New album
            </motion.button>
          </div>
        </section>

        {/* Photos grid */}
        <section className="mt-6">
          {images.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col items-center justify-center py-24 text-center"
            >
              <motion.div
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                className="w-20 h-20 rounded-2xl bg-gray-100 flex items-center justify-center mb-5"
              >
                <ImageIcon className="w-9 h-9 text-gray-400" strokeWidth={1.5} />
              </motion.div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">No photos yet</h3>
              <p className="text-gray-400 text-sm mb-8">Upload your first photo to get started</p>
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                onClick={() => setCurrentScreen('upload')}
                className="px-6 py-3 bg-black text-white rounded-full font-semibold text-sm"
              >
                Upload a photo
              </motion.button>
            </motion.div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-3">
              {images.map((img, i) => {
                const { cols, aspect } = getBento(i);
                return (
                  <motion.div
                    key={img.id}
                    initial={{ opacity: 0, scale: 0.94 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.4, delay: Math.min(i * 0.055, 0.45), ease: [0.23, 1, 0.32, 1] }}
                    whileHover={{ scale: 1.025 }}
                    whileTap={{ scale: 0.965 }}
                    onClick={() => handleImageClick(img)}
                    className={cn(
                      'relative group rounded-2xl overflow-hidden cursor-pointer',
                      'shadow-[0_1px_4px_rgba(0,0,0,0.06)] hover:shadow-[0_6px_24px_rgba(0,0,0,0.14)]',
                      'transition-shadow duration-300',
                      cols,
                      aspect
                    )}
                    style={{ willChange: 'transform' }}
                  >
                    {/* Image */}
                    <img
                      src={img.url}
                      alt={img.title}
                      className="absolute inset-0 w-full h-full object-cover"
                      loading="lazy"
                    />

                    {/* Hover gradient overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/65 via-black/0 to-black/0 opacity-0 group-hover:opacity-100 transition-opacity duration-250 pointer-events-none" />

                    {/* Hover title + size */}
                    <div className="absolute bottom-0 inset-x-0 p-3 pointer-events-none opacity-0 group-hover:opacity-100 translate-y-1.5 group-hover:translate-y-0 transition-all duration-250">
                      <p className="text-white text-[12px] font-semibold truncate drop-shadow-sm leading-snug">{img.title}</p>
                      {img.size != null && <p className="text-white/55 text-[10px] mt-0.5">{formatSize(img.size)}</p>}
                    </div>

                    {/* Compression badge */}
                    {img.ratio != null && (
                      <div className={cn(
                        'absolute top-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-bold backdrop-blur-sm pointer-events-none leading-none py-[3px]',
                        ratioBadge(img.ratio)
                      )}>
                        ↓{Math.round((1 - 1 / img.ratio) * 100)}%
                      </div>
                    )}
                  </motion.div>
                );
              })}
            </div>
          )}
        </section>
      </main>

      {/* FAB */}
      <motion.button
        initial={{ scale: 0, rotate: 135 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: 'spring', stiffness: 280, damping: 20, delay: 0.25 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.88 }}
        onClick={() => setCurrentScreen('upload')}
        className="fixed bottom-8 right-6 w-[60px] h-[60px] bg-black text-white rounded-full flex items-center justify-center shadow-[0_8px_28px_rgba(0,0,0,0.3),0_2px_8px_rgba(0,0,0,0.15)] z-20"
      >
        <Plus className="w-7 h-7" />
      </motion.button>

      {/* New album modal */}
      <AnimatePresence>
        {creatingFolder && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
              onClick={() => { setCreatingFolder(false); setNewFolderName(''); }}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.90, y: 28 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.90, y: 28 }}
              transition={{ type: 'spring', stiffness: 420, damping: 32 }}
              className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[88%] max-w-sm bg-white rounded-3xl p-6 shadow-[0_24px_60px_rgba(0,0,0,0.22)]"
            >
              <h3 className="text-xl font-bold tracking-tight mb-1">New album</h3>
              <p className="text-black/40 text-sm mb-5">Choose a name for this folder</p>
              <input
                ref={newFolderInputRef}
                autoFocus
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleCreateFolder();
                  if (e.key === 'Escape') { setCreatingFolder(false); setNewFolderName(''); }
                }}
                placeholder="e.g. Trip 2025"
                style={{ fontSize: '16px' }}
                className="w-full px-5 py-4 rounded-full border border-black/10 focus:border-black font-light outline-none transition-colors mb-4 bg-gray-50/60 focus:bg-white"
              />
              <div className="flex gap-3">
                <button
                  onClick={() => { setCreatingFolder(false); setNewFolderName(''); }}
                  className="flex-1 py-3.5 rounded-full border-2 border-black/10 text-black font-semibold hover:bg-gray-50 active:scale-95 transition-all"
                >
                  Cancel
                </button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={handleCreateFolder}
                  className="flex-1 py-3.5 rounded-full bg-black text-white font-semibold"
                >
                  Create
                </motion.button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
