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
      const originalsDir = path.join(process.cwd(), 'originals');
      const backendDir = path.join(process.cwd(), 'Backend');

      if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });
      if (!fs.existsSync(storageDir)) fs.mkdirSync(storageDir, { recursive: true });
      if (!fs.existsSync(originalsDir)) fs.mkdirSync(originalsDir, { recursive: true });

      // Track in-flight compression jobs for the queue indicator
      let pendingCompressions = 0;

      const upload = multer({ storage: multer.memoryStorage() });

      // GET /api/queue — number of compressions in progress
      server.middlewares.use('/api/queue', (req: any, res: any, next: any) => {
        if (req.method !== 'GET') return next();
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify({ pending: pendingCompressions }));
      });

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

      // Serve Backend/output/ as static files under /output/
      const outputDir = path.join(process.cwd(), 'Backend', 'output');
      server.middlewares.use('/output', (req: any, res: any, next: any) => {
        const filePath = path.join(outputDir, decodeURIComponent((req.url as string).replace(/^\//, '')));
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
          res.setHeader('Content-Type', 'image/png');
          fs.createReadStream(filePath).pipe(res);
        } else {
          next();
        }
      });

      // Serve originals/ and its subfolders as static files under /originals/
      server.middlewares.use('/originals', (req: any, res: any, next: any) => {
        const filePath = path.join(originalsDir, decodeURIComponent((req.url as string).replace(/^\//, '')));
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
          const ext = path.extname(filePath).toLowerCase();
          const mimeMap: Record<string, string> = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp',
          };
          res.setHeader('Content-Type', mimeMap[ext] ?? 'application/octet-stream');
          fs.createReadStream(filePath).pipe(res);
        } else {
          next();
        }
      });

      // Serve storage/ and its subfolders as static files under /storage/
      server.middlewares.use('/storage', (req: any, res: any, next: any) => {
        const filePath = path.join(storageDir, decodeURIComponent((req.url as string).replace(/^\//, '')));
        if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
          const ext = path.extname(filePath).toLowerCase();
          const mimeMap: Record<string, string> = {
            '.avif': 'image/avif', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp',
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

          // Determine target storage and originals subfolders
          const folder = ((req.body?.folder as string) || 'gallery').replace(/[/\\]/g, '');
          const targetStorageDir = path.join(storageDir, folder);
          const targetOriginalsDir = path.join(originalsDir, folder);
          fs.mkdirSync(targetStorageDir, { recursive: true });
          fs.mkdirSync(targetOriginalsDir, { recursive: true });

          // Spawn Python compression pipeline (tracked for queue indicator)
          try {
            const proc = spawn(
              'python3',
              [
                'main.py',
                '--input', filePath,
                '--storage_dir', targetStorageDir,
                '--originals_dir', targetOriginalsDir,
              ],
              { cwd: backendDir, stdio: 'ignore' }
            );
            pendingCompressions++;
            proc.on('close', () => {
              pendingCompressions = Math.max(0, pendingCompressions - 1);
            });
            proc.unref();
            console.log(`[compression] started for ${filename} → ${folder}/ (pid ${proc.pid})`);
          } catch (spawnErr) {
            console.error('[compression] failed to spawn process:', spawnErr);
          }

          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({ id: filename, title: rawName, processing: true }));
        });
      });

      // GET /api/photos?folder=<name> — list processed images with stats + original URLs
      // DELETE /api/photos?folder=<name>&filename=<file> — delete image + sidecar files
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

          const stem = filename.replace(/_step4_final_compressed\.[^.]+$/, '');
          const filesToDelete = [
            path.join(storageDir, folder, filename),
            path.join(storageDir, folder, `${stem}_stats.json`),
            path.join(process.cwd(), 'Backend', 'output', `${stem}_compression_summary.png`),
          ];

          // Also delete any matching original (unknown extension)
          const origFolder = path.join(originalsDir, folder);
          if (fs.existsSync(origFolder)) {
            fs.readdirSync(origFolder)
              .filter((f) => f.startsWith(stem))
              .forEach((f) => filesToDelete.push(path.join(origFolder, f)));
          }

          try {
            filesToDelete.forEach((p) => { if (fs.existsSync(p)) fs.unlinkSync(p); });
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
          const origFolder = path.join(originalsDir, safeFolder);

          if (!fs.existsSync(targetDir)) {
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
            const stem = f.replace(/_step4_final_compressed\.[^.]+$/, '');

            // Read sidecar stats JSON
            let originalSize: number | undefined;
            let ratio: number | undefined;
            const statsPath = path.join(targetDir, `${stem}_stats.json`);
            if (fs.existsSync(statsPath)) {
              try {
                const s = JSON.parse(fs.readFileSync(statsPath, 'utf8'));
                originalSize = s.originalSize;
                ratio = s.ratio;
              } catch { /* ignore */ }
            }

            // Find matching original file
            let originalUrl: string | undefined;
            if (fs.existsSync(origFolder)) {
              const orig = fs.readdirSync(origFolder)
                .find((o) => o.startsWith(stem) && /\.(jpe?g|png|webp|gif)$/i.test(o));
              if (orig) originalUrl = `/originals/${encodeURIComponent(safeFolder)}/${orig}`;
            }

            return {
              id: f,
              url: `/storage/${encodeURIComponent(safeFolder)}/${f}`,
              title: f
                .replace(/^\d+-/, '')
                .replace(/_step4_final_compressed/, '')
                .replace(/\.[^/.]+$/, '')
                .replace(/_/g, ' '),
              size: stat.size,
              originalSize,
              ratio,
              originalUrl,
            };
          });

          res.end(JSON.stringify(photos));
        } catch {
          res.statusCode = 500;
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
