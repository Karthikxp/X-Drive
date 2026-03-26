import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { spawn } from 'child_process';
import fs from 'fs';
import multer from 'multer';
import path from 'path';
import type { Plugin } from 'vite';
import { defineConfig, loadEnv } from 'vite';

function uploadPlugin(): Plugin {
  return {
    name: 'upload-plugin',
    configureServer(server) {
      const uploadDir = path.join(process.cwd(), 'public', 'user_photos');
      const storageDir = path.join(process.cwd(), 'storage');
      const backendDir = path.join(process.cwd(), 'Backend');

      if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });
      if (!fs.existsSync(storageDir)) fs.mkdirSync(storageDir, { recursive: true });

      const upload = multer({ storage: multer.memoryStorage() });

      // Serve storage/ directory as static files under /storage/
      server.middlewares.use('/storage', (req: any, res: any, next: any) => {
        const filePath = path.join(storageDir, (req.url as string).replace(/^\//, ''));
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
          const ext = path.extname(filePath).toLowerCase();
          const mimeMap: Record<string, string> = {
            '.avif': 'image/avif',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
          };
          res.setHeader('Content-Type', mimeMap[ext] ?? 'application/octet-stream');
          fs.createReadStream(filePath).pipe(res);
        } else {
          next();
        }
      });

      // POST /api/upload — save to public/user_photos/, then run compression in background
      server.middlewares.use('/api/upload', (req: any, res: any, next: any) => {
        if (req.method !== 'POST') return next();

        upload.single('image')(req, res, (err: any) => {
          if (err) {
            res.statusCode = 500;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ error: err.message }));
            return;
          }
          const file = req.file;
          if (!file) {
            res.statusCode = 400;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ error: 'No file uploaded' }));
            return;
          }

          const ext = path.extname(file.originalname) || '.jpg';
          const rawName = ((req.body?.originalName as string) || 'image').slice(0, 80);
          const safeName = rawName.replace(/[^a-zA-Z0-9._-]/g, '_');
          const filename = `${Date.now()}-${safeName}${ext}`;
          const filePath = path.join(uploadDir, filename);

          fs.writeFileSync(filePath, file.buffer);

          // Spawn Python compression pipeline in the background (non-blocking)
          try {
            const proc = spawn('python3', ['main.py', '--input', filePath], {
              cwd: backendDir,
              detached: true,
              stdio: 'ignore',
            });
            proc.unref();
            console.log(`[compression] started for ${filename} (pid ${proc.pid})`);
          } catch (spawnErr) {
            console.error('[compression] failed to spawn process:', spawnErr);
          }

          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ id: filename, title: rawName, processing: true }));
        });
      });

      // GET /api/photos — list processed images from storage/
      server.middlewares.use('/api/photos', (req: any, res: any, next: any) => {
        if (req.method !== 'GET') return next();
        try {
          const files = fs
            .readdirSync(storageDir)
            .filter((f) => /\.(jpe?g|png|gif|webp|avif)$/i.test(f))
            .sort((a, b) => {
              // Sort by mtime descending (newest first)
              const at = fs.statSync(path.join(storageDir, a)).mtimeMs;
              const bt = fs.statSync(path.join(storageDir, b)).mtimeMs;
              return bt - at;
            });

          const photos = files.map((f) => {
            const stat = fs.statSync(path.join(storageDir, f));
            return {
              id: f,
              url: `/storage/${f}`,
              title: f
                .replace(/^\d+-/, '')
                .replace(/_step4_final_compressed/, '')
                .replace(/\.[^/.]+$/, '')
                .replace(/_/g, ' '),
              size: stat.size,
            };
          });

          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify(photos));
        } catch {
          res.statusCode = 500;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ error: 'Failed to list photos' }));
        }
      });
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  return {
    plugins: [react(), tailwindcss(), uploadPlugin()],
    define: {
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      hmr: process.env.DISABLE_HMR !== 'true',
    },
  };
});
