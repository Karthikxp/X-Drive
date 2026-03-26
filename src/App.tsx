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

// --- Components ---

const Logo = ({ className, dark = false }: { className?: string; dark?: boolean }) => (
  <div className={cn('flex items-center gap-2 font-bold text-3xl tracking-tighter', className, dark ? 'text-white' : 'text-black')}>
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="rotate-45">
      <line x1="5" y1="12" x2="19" y2="12" />
      <line x1="12" y1="5" x2="12" y2="19" />
    </svg>
    Drive
  </div>
);

const Button = ({
  children,
  variant = 'primary',
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'outline' }) => (
  <button
    className={cn(
      'w-full py-4 rounded-full font-medium transition-transform active:scale-95 flex items-center justify-center gap-3',
      variant === 'primary' ? 'bg-black text-white' : 'bg-white text-black border-2 border-black',
      className
    )}
    {...props}
  >
    {children}
  </button>
);

const Pill = ({ children, active, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { active?: boolean }) => (
  <button
    className={cn(
      'px-6 py-2 rounded-full border border-black/20 whitespace-nowrap text-sm font-medium transition-colors',
      active ? 'bg-black text-white' : 'bg-white text-black hover:bg-gray-50'
    )}
    {...props}
  >
    {children}
  </button>
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
  const [currentScreen, setCurrentScreen] = useState<Screen>('login');
  const [images, setImages] = useState<ImageData[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [slideDirection, setSlideDirection] = useState<number>(0);
  const [uploadStage, setUploadStage] = useState<UploadStage>('idle');
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [uploadedCount, setUploadedCount] = useState(0);
  const [folders, setFolders] = useState<string[]>([]);
  const [activeFolder, setActiveFolder] = useState<string>('');
  const [creatingFolder, setCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [showingSummary, setShowingSummary] = useState(false);
  const [showingSlider, setShowingSlider] = useState(false);
  const [sliderPos, setSliderPos] = useState(50);
  const isDraggingRef = useRef(false);
  const [pendingQueue, setPendingQueue] = useState(0);
  const [preset, setPreset] = useState<'storage' | 'balanced' | 'quality'>('balanced');
  const sliderContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const newFolderInputRef = useRef<HTMLInputElement>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollCountRef = useRef(0);

  const selectedImage = images[selectedIndex] ?? null;

  // Load folder list once on mount
  useEffect(() => {
    fetch('/api/folders')
      .then((r) => r.json())
      .then((data: string[]) => {
        setFolders(data);
        if (data.length > 0) setActiveFolder(data[0]);
      })
      .catch(() => {});
  }, []);

  // Reload photos whenever the active folder changes
  useEffect(() => {
    if (!activeFolder) return;
    fetch(`/api/photos?folder=${encodeURIComponent(activeFolder)}`)
      .then((r) => r.json())
      .then((data: ImageData[]) => setImages(data))
      .catch(() => {});
  }, [activeFolder]);

  // Poll compression queue
  useEffect(() => {
    const id = setInterval(() => {
      fetch('/api/queue')
        .then((r) => r.json())
        .then((d: { pending: number }) => setPendingQueue(d.pending))
        .catch(() => {});
    }, 3000);
    return () => clearInterval(id);
  }, []);

  // --- Handlers ---
  const handleLogin = () => setCurrentScreen('home');
  const handleLogout = () => setCurrentScreen('login');

  const handleImageClick = (img: ImageData) => {
    const idx = images.findIndex((i) => i.id === img.id);
    setSelectedIndex(idx >= 0 ? idx : 0);
    setSlideDirection(0);
    setCurrentScreen('view');
  };

  const closeImageView = () => { setConfirmingDelete(false); setShowingSummary(false); setShowingSlider(false); setCurrentScreen('home'); };

  const goNext = () => {
    if (selectedIndex < images.length - 1) {
      setConfirmingDelete(false);
      setShowingSummary(false);
      setShowingSlider(false);
      setSlideDirection(1);
      setSelectedIndex((i) => i + 1);
    }
  };

  const goPrev = () => {
    if (selectedIndex > 0) {
      setConfirmingDelete(false);
      setShowingSummary(false);
      setShowingSlider(false);
      setSlideDirection(-1);
      setSelectedIndex((i) => i - 1);
    }
  };

  // Keyboard navigation in view screen
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
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    pollCountRef.current = 0;
  };

  const clearUpload = () => {
    stopPolling();
    previewUrls.forEach((u) => URL.revokeObjectURL(u));
    setPendingFiles([]);
    setPreviewUrls([]);
    setUploadedCount(0);
    setUploadStage('idle');
    setCurrentScreen('home');
  };

  // Append newly picked files (don't replace existing selection)
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
      await fetch('/api/folders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      setFolders((prev) => [...prev, name]);
      setActiveFolder(name);
    } catch (err) {
      console.error(err);
    }
    setNewFolderName('');
    setCreatingFolder(false);
  };

  const handleDeleteImage = async () => {
    if (!selectedImage) return;
    // URL format: /storage/<folder>/<filename>
    const parts = selectedImage.url.split('/');
    const folder = decodeURIComponent(parts[2] ?? '');
    const filename = parts[3] ?? '';
    if (!folder || !filename) return;

    try {
      await fetch(
        `/api/photos?folder=${encodeURIComponent(folder)}&filename=${encodeURIComponent(filename)}`,
        { method: 'DELETE' }
      );
    } catch (err) {
      console.error(err);
    }

    const remaining = images.filter((img) => img.id !== selectedImage.id);
    setImages(remaining);
    setConfirmingDelete(false);

    if (remaining.length === 0) {
      setCurrentScreen('home');
    } else {
      setSelectedIndex(Math.min(selectedIndex, remaining.length - 1));
    }
  };

  // Poll /api/photos?folder=X until new compressed images appear, then update the gallery
  const startPollingForResults = (knownCount: number, folder: string) => {
    stopPolling();
    pollCountRef.current = 0;
    const MAX_POLLS = 60; // ~5 minutes at 5s intervals

    pollTimerRef.current = setInterval(async () => {
      pollCountRef.current += 1;
      try {
        const r = await fetch(`/api/photos?folder=${encodeURIComponent(folder)}`);
        const data: ImageData[] = await r.json();
        if (data.length > knownCount) {
          setImages(data);
          stopPolling();
          setUploadStage('done');
          setTimeout(clearUpload, 1500);
        }
      } catch { /* ignore transient errors */ }

      if (pollCountRef.current >= MAX_POLLS) {
        stopPolling();
        clearUpload();
      }
    }, 5000);
  };

  // Upload all pending files one by one, then wait for compression
  const handleUpload = async () => {
    if (pendingFiles.length === 0) return;
    setUploadStage('uploading');

    try {
      for (let i = 0; i < pendingFiles.length; i++) {
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

      // Switch to processing state and poll until compressed images land in storage
      setUploadStage('processing');
      startPollingForResults(images.length, activeFolder);
    } catch (err) {
      console.error(err);
      setUploadStage('idle');
    }
  };

  // --- Login Screen ---
  if (currentScreen === 'login') {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6 font-sans">
        <div className="flex-1 flex flex-col items-center justify-center w-full max-w-md space-y-12">
          <Logo className="scale-150 mb-8" />
          <h1 className="text-2xl font-medium text-center tracking-tight leading-snug">
            Affordable cloud storage for
            <br />
            everyone
          </h1>
          <div className="w-full space-y-4 mt-12">
            <Button onClick={handleLogin}>
              <svg className="w-5 h-5" viewBox="0 0 814 1000" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path d="M788.1 340.9c-5.8 4.5-108.2 62.2-108.2 190.5 0 148.4 130.3 200.9 134.2 202.2-.6 3.2-20.7 71.9-68.7 141.9-42.8 61.6-87.5 123.1-155.5 123.1s-85.5-39.5-164-39.5c-76 0-103.7 40.8-165.9 40.8s-105-37.5-155.5-127.4C46.7 790.7 0 663 0 541.8c0-207.5 135.4-317.3 269-317.3 70.1 0 128.4 46.4 172.5 46.4 42.8 0 109.6-49.1 189.6-49.1 30.5 0 110.5 2.6 171.3 64.3zm-217.2-141.5c31.1-36.9 53.1-88.1 53.1-139.3 0-7.1-.6-14.3-1.9-20.1-50.6 1.9-110.8 33.7-147.1 75.8-28.5 32.4-55.1 83.6-55.1 135.5 0 7.8 1.3 15.6 1.9 18.1 3.2.6 8.4 1.3 13.6 1.3 45.4 0 102.5-30.4 135.5-71.3z"/>
              </svg>
              Continue with apple
            </Button>
            <Button variant="outline" onClick={handleLogin}>
              Continue with Google
            </Button>
          </div>
          <button onClick={handleLogin} className="text-sm font-medium mt-8 hover:underline">
            **** DUMMY LOGIN PASS *****
          </button>
        </div>
      </div>
    );
  }

  // --- Upload Screen ---
  if (currentScreen === 'upload') {
    const isProcessing = uploadStage !== 'idle';
    const isCompressing = uploadStage === 'processing';
    const hasFiles = pendingFiles.length > 0;

    return (
      <div className="fixed inset-0 bg-black text-white font-sans flex flex-col overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8 px-6 pt-6">
          <Logo dark />
          <button onClick={clearUpload} className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex-1 flex flex-col w-full max-w-md mx-auto px-6 pb-6">
          <h1 className="text-4xl font-bold tracking-tight mb-6">File upload</h1>

          {/* Hidden file input — multiple */}
          <input
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileChange}
          />

          {!hasFiles ? (
            /* Empty drop zone */
            <button
              onClick={() => fileInputRef.current?.click()}
              className="w-full aspect-square max-w-[260px] mx-auto border-2 border-dashed border-white/20 rounded-3xl flex flex-col items-center justify-center gap-4 hover:border-white/40 hover:bg-white/5 transition-all"
            >
              <Folder className="w-20 h-20 text-white/50" strokeWidth={1} />
              <p className="text-base font-medium text-white/50">Tap to choose photos</p>
            </button>
          ) : (
            /* Thumbnail grid */
            <div className="flex-1 overflow-y-auto">
              <div className="grid grid-cols-3 gap-2">
                {pendingFiles.map((file, i) => (
                  <motion.div
                    key={`${file.name}-${i}`}
                    initial={{ opacity: 0, scale: 0.85 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.2 }}
                    className="relative aspect-square rounded-2xl overflow-hidden bg-white/5"
                  >
                    <img src={previewUrls[i]} alt={file.name} className="w-full h-full object-cover" />
                    {/* Per-file upload overlay */}
                    {uploadStage === 'uploading' && i < uploadedCount && (
                      <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                        <Check className="w-6 h-6 text-green-400" strokeWidth={3} />
                      </div>
                    )}
                    {uploadStage === 'uploading' && i === uploadedCount && (
                      <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                        <Spinner className="w-6 h-6 text-white" />
                      </div>
                    )}
                    {/* Remove button — only when idle */}
                    {!isProcessing && (
                      <button
                        onClick={() => handleRemoveFile(i)}
                        className="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-black/70 flex items-center justify-center hover:bg-black transition-colors"
                      >
                        <X className="w-3.5 h-3.5 text-white" />
                      </button>
                    )}
                    {/* File size label */}
                    <div className="absolute bottom-0 inset-x-0 px-1.5 py-1 bg-gradient-to-t from-black/70 to-transparent">
                      <p className="text-white/80 text-[10px] truncate">{formatSize(file.size)}</p>
                    </div>
                  </motion.div>
                ))}

                {/* Add more tile */}
                {!isProcessing && (
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="aspect-square rounded-2xl border-2 border-dashed border-white/20 flex flex-col items-center justify-center gap-1 hover:border-white/40 hover:bg-white/5 transition-all"
                  >
                    <Plus className="w-6 h-6 text-white/40" />
                    <span className="text-white/40 text-[11px]">Add more</span>
                  </button>
                )}
              </div>

              {/* File count + status */}
              <p className="text-white/40 text-sm mt-4">
                {uploadStage === 'uploading'
                  ? `Uploading ${uploadedCount} of ${pendingFiles.length}…`
                  : uploadStage === 'processing'
                  ? `Compressing ${pendingFiles.length} photo${pendingFiles.length !== 1 ? 's' : ''}… this may take a minute`
                  : uploadStage === 'done'
                  ? `${pendingFiles.length} photo${pendingFiles.length !== 1 ? 's' : ''} ready!`
                  : `${pendingFiles.length} photo${pendingFiles.length !== 1 ? 's' : ''} selected`}
              </p>
            </div>
          )}

          {/* Preset selector */}
          <div className="mt-6">
            <p className="text-white/40 text-xs font-medium uppercase tracking-wider mb-3">Compression preset</p>
            <div className="grid grid-cols-3 gap-2">
              {([ 
                { id: 'storage',  label: 'Storage',  sub: 'Max compression',     ratio: '8–15×' },
                { id: 'balanced', label: 'Balanced', sub: 'Smart trade-off',      ratio: '4–8×'  },
                { id: 'quality',  label: 'Quality',  sub: 'Best visual fidelity', ratio: '2–4×'  },
              ] as const).map(({ id, label, sub, ratio }) => (
                <button
                  key={id}
                  onClick={() => setPreset(id)}
                  disabled={isProcessing}
                  className={cn(
                    'rounded-2xl px-3 py-3 text-left transition-all',
                    preset === id
                      ? 'bg-white text-black'
                      : 'bg-white/8 text-white/60 hover:bg-white/12'
                  )}
                >
                  <p className={cn('text-sm font-bold', preset === id ? 'text-black' : 'text-white')}>{label}</p>
                  <p className={cn('text-[10px] mt-0.5 leading-tight', preset === id ? 'text-black/50' : 'text-white/35')}>{sub}</p>
                  <p className={cn('text-xs font-semibold mt-1.5', preset === id ? 'text-black/70' : 'text-white/40')}>{ratio}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Bottom action */}
          <div className="mt-4 pb-4">
            {!hasFiles ? (
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full py-4 rounded-full font-medium bg-white text-black hover:bg-gray-100 active:scale-95 transition-all flex items-center justify-center gap-2"
              >
                <Upload className="w-5 h-5" />
                Browse files
              </button>
            ) : (
              <button
                onClick={handleUpload}
                disabled={isProcessing}
                className={cn(
                  'w-full py-4 rounded-full font-medium flex items-center justify-center gap-3 transition-all duration-300',
                  uploadStage === 'idle' && 'bg-white text-black hover:bg-gray-100 active:scale-95',
                  uploadStage === 'uploading' && 'bg-blue-400/20 text-blue-300 cursor-not-allowed',
                  isCompressing && 'bg-yellow-400/20 text-yellow-300 cursor-not-allowed',
                  uploadStage === 'done' && 'bg-green-400/20 text-green-300 cursor-not-allowed'
                )}
              >
                {uploadStage === 'idle' && (
                  <>
                    <Upload className="w-5 h-5" />
                    Upload {pendingFiles.length} photo{pendingFiles.length !== 1 ? 's' : ''}
                  </>
                )}
                {uploadStage === 'uploading' && (
                  <>
                    <Spinner className="w-5 h-5" />
                    Uploading {uploadedCount} of {pendingFiles.length}…
                  </>
                )}
                {isCompressing && (
                  <>
                    <Spinner className="w-5 h-5" />
                    Compressing…
                  </>
                )}
                {uploadStage === 'done' && (
                  <>
                    <Check className="w-5 h-5" />
                    Done!
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // --- View Screen ---
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
            className="bg-white/15 backdrop-blur-md text-white px-4 py-2 rounded-full font-semibold flex items-center gap-2 text-sm hover:bg-white/25 transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="rotate-45">
              <line x1="5" y1="12" x2="19" y2="12" />
              <line x1="12" y1="5" x2="12" y2="19" />
            </svg>
            Drive
          </button>
          <div className="flex items-center gap-2">
            {/* Download */}
            <a
              href={selectedImage.url}
              download={selectedImage.title + '.avif'}
              className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 transition-colors flex items-center justify-center"
              title="Download"
            >
              <Download className="w-4 h-4 text-white/70" />
            </a>
            {/* Compare slider — only when original is available */}
            {selectedImage.originalUrl && (
              <button
                onClick={() => { setShowingSlider(true); setShowingSummary(false); setConfirmingDelete(false); setSliderPos(50); }}
                className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 transition-colors flex items-center justify-center"
                title="Compare original vs compressed"
              >
                <Columns2 className="w-4 h-4 text-white/70" />
              </button>
            )}
            {/* Visualize pipeline */}
            <button
              onClick={() => { setShowingSummary(true); setShowingSlider(false); setConfirmingDelete(false); }}
              className="h-9 px-3 rounded-full bg-white/10 hover:bg-white/20 transition-colors flex items-center gap-1.5"
              title="Visualize compression"
            >
              <BarChart2 className="w-4 h-4 text-white/70" />
              <span className="text-white/70 text-xs font-medium">Visualize</span>
            </button>
            {/* Delete */}
            <button
              onClick={() => setConfirmingDelete(true)}
              className="w-9 h-9 rounded-full bg-white/10 hover:bg-red-500/30 transition-colors flex items-center justify-center"
              title="Delete photo"
            >
              <Trash2 className="w-4 h-4 text-white/70" />
            </button>
          </div>
        </div>

        {/* Image area with swipe */}
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
                if (swipedFar || swipedFast) {
                  if (info.offset.x < 0) goNext();
                  else goPrev();
                }
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

          {/* Left tap zone */}
          {hasPrev && (
            <button
              onClick={goPrev}
              className="absolute left-0 inset-y-0 w-16 z-10 flex items-center justify-start pl-3 group"
            >
              <div className="w-9 h-9 rounded-full bg-black/40 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <ChevronLeft className="w-5 h-5 text-white" />
              </div>
            </button>
          )}

          {/* Right tap zone */}
          {hasNext && (
            <button
              onClick={goNext}
              className="absolute right-0 inset-y-0 w-16 z-10 flex items-center justify-end pr-3 group"
            >
              <div className="w-9 h-9 rounded-full bg-black/40 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <ChevronRight className="w-5 h-5 text-white" />
              </div>
            </button>
          )}
        </div>

        {/* Bottom info */}
        <div className="flex-shrink-0 px-6 pt-3 pb-8">
          <h2 className="text-white text-3xl font-bold tracking-tight">{selectedImage.title}</h2>
          <div className="flex items-center justify-between mt-1">
            {selectedImage.size != null && (
              <p className="text-white/40 text-sm">{formatSize(selectedImage.size)}</p>
            )}
            {images.length > 1 && (
              <span className="text-white/40 text-sm font-medium tabular-nums">
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
                {/* Summary top bar */}
                <div className="flex-shrink-0 flex items-center justify-between px-5 pt-5 pb-3 border-b border-white/10">
                  <div>
                    <p className="text-white font-semibold text-sm">Compression pipeline</p>
                    <p className="text-white/40 text-xs mt-0.5">{selectedImage.title}</p>
                  </div>
                  <button
                    onClick={() => setShowingSummary(false)}
                    className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 transition-colors flex items-center justify-center"
                  >
                    <X className="w-4 h-4 text-white" />
                  </button>
                </div>

                {/* Scrollable image area — screen height, natural width, horizontal scroll */}
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
                  <div
                    style={{ display: 'none' }}
                    className="h-full min-h-[200px] items-center justify-center text-white/30 text-sm"
                  >
                    Summary not available yet — compression may still be running.
                  </div>
                </div>
              </motion.div>
            );
          })()}
        </AnimatePresence>

        {/* Split-slider: original vs compressed */}
        <AnimatePresence>
          {showingSlider && selectedImage.originalUrl && (
            <motion.div
              initial={{ opacity: 0, y: '100%' }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: '100%' }}
              transition={{ type: 'spring', stiffness: 320, damping: 36 }}
              className="absolute inset-0 z-40 bg-black flex flex-col"
            >
              {/* Top bar */}
              <div className="flex-shrink-0 flex items-center justify-between px-5 pt-5 pb-3 border-b border-white/10">
                <div>
                  <p className="text-white font-semibold text-sm">Compare</p>
                  <p className="text-white/40 text-xs mt-0.5">Drag to reveal original vs compressed</p>
                </div>
                <button
                  onClick={() => setShowingSlider(false)}
                  className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 transition-colors flex items-center justify-center"
                >
                  <X className="w-4 h-4 text-white" />
                </button>
              </div>

              {/* Slider area — pointer capture on container, ref-based drag state */}
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
                {/* Compressed image — full background */}
                <img
                  src={selectedImage.url}
                  alt="Compressed"
                  className="absolute inset-0 w-full h-full object-contain"
                  draggable={false}
                  style={{ pointerEvents: 'none' }}
                />
                {/* Original image — clipped to left portion */}
                <img
                  src={selectedImage.originalUrl}
                  alt="Original"
                  className="absolute inset-0 w-full h-full object-contain"
                  style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)`, pointerEvents: 'none' }}
                  draggable={false}
                />

                {/* Divider line + handle — pointer-events none so container captures all */}
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-white/80 shadow-[0_0_10px_rgba(255,255,255,0.6)] z-10"
                  style={{ left: `${sliderPos}%`, transform: 'translateX(-50%)', pointerEvents: 'none' }}
                >
                  <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-11 h-11 rounded-full bg-white shadow-xl flex items-center justify-center gap-0.5">
                    <ChevronLeft className="w-3.5 h-3.5 text-black" />
                    <ChevronRight className="w-3.5 h-3.5 text-black" />
                  </div>
                </div>

                {/* Side labels */}
                {sliderPos > 12 && (
                  <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-black/60 backdrop-blur-sm text-white text-xs font-semibold pointer-events-none">
                    Original
                  </div>
                )}
                {sliderPos < 88 && (
                  <div className="absolute top-4 right-4 px-3 py-1 rounded-full bg-black/60 backdrop-blur-sm text-white text-xs font-semibold pointer-events-none">
                    Compressed
                    {selectedImage.ratio && (
                      <span className="ml-1.5 opacity-70">↓{Math.round((1 - 1 / selectedImage.ratio) * 100)}%</span>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Delete confirmation overlay */}
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
                <button
                  onClick={() => setConfirmingDelete(false)}
                  className="flex-1 py-3.5 rounded-full bg-white/30 text-white font-medium hover:bg-white/20 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteImage}
                  className="flex-1 py-3.5 rounded-full bg-red-500 text-white font-medium hover:bg-red-600 active:scale-95 transition-all flex items-center justify-center gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    );
  }

  // --- Home Screen ---
  return (
    <div className="min-h-screen bg-white font-sans pb-28">
      <header className="flex justify-between items-center p-6 sticky top-0 bg-white/80 backdrop-blur-md z-10">
        <Logo />
        <button onClick={handleLogout} className="w-11 h-11 rounded-full overflow-hidden border-2 border-black">
          <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="Avatar" className="w-full h-full object-cover bg-gray-100" />
        </button>
      </header>

      <main className="px-6 max-w-3xl mx-auto">
        <section className="mt-6">
          <h2 className="text-4xl font-bold tracking-tight mb-5">Albums</h2>
          <div className="flex overflow-x-auto pb-4 -mx-6 px-6 gap-3 no-scrollbar items-center">
            {folders.map((f) => (
              <Pill key={f} active={activeFolder === f} onClick={() => setActiveFolder(f)}>
                {f}
              </Pill>
            ))}

            <button
              onClick={() => setCreatingFolder(true)}
              className="flex-shrink-0 px-5 py-2 rounded-full border border-dashed border-black/25 text-sm font-medium text-black/40 hover:bg-gray-50 hover:border-black/40 transition-colors whitespace-nowrap flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              New folder
            </button>
          </div>
        </section>

        <section className="mt-8">
          <h2 className="text-4xl font-bold tracking-tight mb-5">Home</h2>

          {images.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <div className="w-24 h-24 rounded-full bg-gray-100 flex items-center justify-center mb-5">
                <ImageIcon className="w-11 h-11 text-gray-400" strokeWidth={1.5} />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No photos yet</h3>
              <p className="text-gray-400 text-sm mb-8">Upload your first photo to get started</p>
              <button
                onClick={() => setCurrentScreen('upload')}
                className="px-6 py-3 bg-black text-white rounded-full font-medium text-sm hover:bg-gray-900 active:scale-95 transition-all"
              >
                Upload a photo
              </button>
            </div>
          ) : (
            <div className="columns-2 gap-4 space-y-4">
              {images.map((img, i) => (
                <motion.div
                  key={img.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.04 }}
                  className="break-inside-avoid rounded-3xl overflow-hidden cursor-pointer transition-transform hover:scale-[1.02] active:scale-95 shadow-sm relative"
                  onClick={() => handleImageClick(img)}
                >
                  <img src={img.url} alt={img.title} className="w-full h-auto object-cover" loading="lazy" />
                  {img.ratio != null && (
                    <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-sm text-white text-[10px] font-bold tracking-tight pointer-events-none">
                      ↓{Math.round((1 - 1 / img.ratio) * 100)}%
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </section>
      </main>

      <button
        onClick={() => setCurrentScreen('upload')}
        className="fixed bottom-8 right-8 w-16 h-16 bg-black text-white rounded-full flex items-center justify-center shadow-2xl hover:scale-105 transition-transform active:scale-95 z-20"
      >
        <Plus className="w-8 h-8" />
      </button>

      {/* Processing queue indicator */}
      <AnimatePresence>
        {pendingQueue > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
            className="fixed top-20 left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 px-4 py-2 bg-black text-white text-sm font-medium rounded-full shadow-lg"
          >
            <Spinner className="w-3.5 h-3.5" />
            {pendingQueue} compressing…
          </motion.div>
        )}
      </AnimatePresence>

      {/* New folder modal */}
      <AnimatePresence>
        {creatingFolder && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
              onClick={() => { setCreatingFolder(false); setNewFolderName(''); }}
            />

            {/* Card */}
            <motion.div
              initial={{ opacity: 0, scale: 0.92, y: 32 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.92, y: 32 }}
              transition={{ type: 'spring', stiffness: 420, damping: 32 }}
              className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[88%] max-w-sm bg-white rounded-3xl p-6 shadow-2xl"
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
                className="w-full px-5 py-4 rounded-full border-1 border-black/10 focus:border-black font-light outline-none transition-colors mb-4"
              />

              <div className="flex gap-3">
                <button
                  onClick={() => { setCreatingFolder(false); setNewFolderName(''); }}
                  className="flex-1 py-3.5 rounded-full border-2 border-black/10 text-black font-medium active:scale-95 transition-transform"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateFolder}
                  className="flex-1 py-3.5 rounded-full bg-black text-white font-medium active:scale-95 transition-transform"
                >
                  Create
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
