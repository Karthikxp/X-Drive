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

      // GET /api/folders — list subfolders of storage/
      // POST /api/folders — create a new subfolder
      server.middlewares.use('/api/folders', (req: any, res: any, next: any) => {
        res.setHeader('Content-Type', 'application/json');

        if (req.method === 'GET') {
          try {
            const folders = fs
              .readdirSync(storageDir)
              .filter((f) => fs.statSync(path.join(storageDir, f)).isDirectory());
            res.end(JSON.stringify(folders));
          } catch {
            res.statusCode = 500;
            res.end(JSON.stringify({ error: 'Failed to list folders' }));
          }
          return;
        }

        if (req.method === 'POST') {
          let body = '';
          req.on('data', (chunk: Buffer) => (body += chunk.toString()));
          req.on('end', () => {
            try {
              const { name } = JSON.parse(body) as { name: string };
              const safe = name.trim().replace(/[/\\]/g, '');
              if (!safe) {
                res.statusCode = 400;
                res.end(JSON.stringify({ error: 'Invalid folder name' }));
                return;
              }
              fs.mkdirSync(path.join(storageDir, safe), { recursive: true });
              res.end(JSON.stringify({ name: safe }));
            } catch {
              res.statusCode = 400;
              res.end(JSON.stringify({ error: 'Invalid request body' }));
            }
          });
          return;
        }

        next();
      });

      // Serve storage/ and its subfolders as static files under /storage/
      server.middlewares.use('/storage', (req: any, res: any, next: any) => {
        const filePath = path.join(storageDir, decodeURIComponent((req.url as string).replace(/^\//, '')));
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

          // Determine target storage subfolder (default: gallery)
          const folder = ((req.body?.folder as string) || 'gallery').replace(/[/\\]/g, '');
          const targetStorageDir = path.join(storageDir, folder);
          fs.mkdirSync(targetStorageDir, { recursive: true });

          // Spawn Python compression pipeline in the background (non-blocking)
          try {
            const proc = spawn(
              'python3',
              ['main.py', '--input', filePath, '--storage_dir', targetStorageDir],
              { cwd: backendDir, detached: true, stdio: 'ignore' }
            );
            proc.unref();
            console.log(`[compression] started for ${filename} → ${folder}/ (pid ${proc.pid})`);
          } catch (spawnErr) {
            console.error('[compression] failed to spawn process:', spawnErr);
          }

          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ id: filename, title: rawName, processing: true }));
        });
      });

      // GET /api/photos?folder=<name> — list processed images from a storage subfolder
      // DELETE /api/photos?folder=<name>&filename=<file> — delete a specific image
      server.middlewares.use('/api/photos', (req: any, res: any, next: any) => {
        res.setHeader('Content-Type', 'application/json');

        if (req.method === 'DELETE') {
          const qs = ((req.url as string).split('?')[1]) ?? '';
          const params = new URLSearchParams(qs);
          const folder = (params.get('folder') ?? '').replace(/[/\\]/g, '');
          const filename = (params.get('filename') ?? '').replace(/[/\\]/g, '');
          if (!folder || !filename) {
            res.statusCode = 400;
            res.end(JSON.stringify({ error: 'Missing folder or filename' }));
            return;
          }
          const filePath = path.join(storageDir, folder, filename);
          try {
            if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
            res.end(JSON.stringify({ ok: true }));
          } catch {
            res.statusCode = 500;
            res.end(JSON.stringify({ error: 'Failed to delete file' }));
          }
          return;
        }

        if (req.method !== 'GET') return next();
        try {
          const qs = ((req.url as string).split('?')[1]) ?? '';
          const folder = new URLSearchParams(qs).get('folder') ?? 'gallery';
          const safeFolder = folder.replace(/[/\\]/g, '');
          const targetDir = path.join(storageDir, safeFolder);

          if (!fs.existsSync(targetDir)) {
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify([]));
            return;
          }

          const files = fs
            .readdirSync(targetDir)
            .filter((f) => /\.(jpe?g|png|gif|webp|avif)$/i.test(f))
            .sort((a, b) => {
              const at = fs.statSync(path.join(targetDir, a)).mtimeMs;
              const bt = fs.statSync(path.join(targetDir, b)).mtimeMs;
              return bt - at;
            });

          const photos = files.map((f) => {
            const stat = fs.statSync(path.join(targetDir, f));
            return {
              id: f,
              url: `/storage/${encodeURIComponent(safeFolder)}/${f}`,
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
