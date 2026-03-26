import { Apple, Check, ChevronLeft, ChevronRight, Folder, Image as ImageIcon, Plus, Upload, X } from 'lucide-react';
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
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollCountRef = useRef(0);

  const selectedImage = images[selectedIndex] ?? null;

  useEffect(() => {
    fetch('/api/photos')
      .then((r) => r.json())
      .then((data: ImageData[]) => setImages(data))
      .catch(() => {});
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

  const closeImageView = () => setCurrentScreen('home');

  const goNext = () => {
    if (selectedIndex < images.length - 1) {
      setSlideDirection(1);
      setSelectedIndex((i) => i + 1);
    }
  };

  const goPrev = () => {
    if (selectedIndex > 0) {
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

  // Poll /api/photos until new compressed images appear, then update the gallery
  const startPollingForResults = (knownCount: number) => {
    stopPolling();
    pollCountRef.current = 0;
    const MAX_POLLS = 60; // ~5 minutes at 5s intervals

    pollTimerRef.current = setInterval(async () => {
      pollCountRef.current += 1;
      try {
        const r = await fetch('/api/photos');
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

        const response = await fetch('/api/upload', { method: 'POST', body: formData });
        if (!response.ok) throw new Error(`Upload failed for ${file.name}`);
      }

      // Switch to processing state and poll until compressed images land in storage
      setUploadStage('processing');
      startPollingForResults(images.length);
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
              <Apple className="w-5 h-5" />
              Continue with apple
            </Button>
            <Button variant="outline" onClick={handleLogin}>
              Continue with Phone
            </Button>
          </div>
          <button onClick={handleLogin} className="text-sm font-medium mt-8 hover:underline">
            Sign in to Continue
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
      <div className="min-h-screen bg-black text-white p-6 font-sans flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <Logo dark />
          <button onClick={clearUpload} className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex-1 flex flex-col w-full max-w-md mx-auto">
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

          {/* Bottom action */}
          <div className="mt-6 pb-4">
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
          {images.length > 1 && (
            <span className="text-white/50 text-sm font-medium tabular-nums">
              {selectedIndex + 1} / {images.length}
            </span>
          )}
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
          {selectedImage.size != null && (
            <p className="text-white/40 text-sm mt-1">{formatSize(selectedImage.size)}</p>
          )}
        </div>
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
          <div className="flex overflow-x-auto pb-4 -mx-6 px-6 gap-3 no-scrollbar">
            <Pill active>2025 Album</Pill>
            <Pill>Shares</Pill>
            <Pill>Downloads</Pill>
            <Pill>Trip 2025</Pill>
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
                  className="break-inside-avoid rounded-3xl overflow-hidden cursor-pointer transition-transform hover:scale-[1.02] active:scale-95 shadow-sm"
                  onClick={() => handleImageClick(img)}
                >
                  <img src={img.url} alt={img.title} className="w-full h-auto object-cover" loading="lazy" />
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
    </div>
  );
}
