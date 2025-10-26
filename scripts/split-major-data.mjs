#!/usr/bin/env node

/**
 * Split the large major data JSON file into smaller chunks so that Cloudflare Pages
 * can serve them without hitting the 25 MiB per-file limit.
 */

import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const SOURCE_PATH = join(ROOT, 'data', 'major_data_processed.json');
const OUTPUT_DIR = join(ROOT, 'public', 'data', 'major-data');
const MANIFEST_PATH = join(ROOT, 'public', 'data', 'major-data-manifest.json');

const CHUNK_SIZE = 2000;

function chunkArray(array, size) {
  const chunks = [];
  for (let index = 0; index < array.length; index += size) {
    chunks.push(array.slice(index, index + size));
  }
  return chunks;
}

function main() {
  const contents = readFileSync(SOURCE_PATH, 'utf8');
  const majors = JSON.parse(contents);

  rmSync(OUTPUT_DIR, { recursive: true, force: true });
  mkdirSync(OUTPUT_DIR, { recursive: true });

  const chunks = chunkArray(majors, CHUNK_SIZE);
  const manifest = {
    source: 'data/major_data_processed.json',
    generatedAt: new Date().toISOString(),
    totalItems: majors.length,
    chunkSize: CHUNK_SIZE,
    chunks: [],
  };

  chunks.forEach((chunk, index) => {
    const fileName = `major-data-${String(index + 1).padStart(2, '0')}.json`;
    const filePath = join(OUTPUT_DIR, fileName);
    writeFileSync(filePath, JSON.stringify(chunk));
    manifest.chunks.push({
      file: `data/major-data/${fileName}`,
      start: index * CHUNK_SIZE,
      count: chunk.length,
    });
  });

  writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2));
}

main();
