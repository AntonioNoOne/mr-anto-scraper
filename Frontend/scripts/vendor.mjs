// Copia gli asset delle librerie da node_modules a Frontend/vendor/,
// così il frontend non dipende da nessuna CDN esterna (riproducibile, offline, CSP-safe).
import { cp, mkdir, rm } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const nm = join(root, "node_modules");
const vendor = join(root, "vendor");

const files = [
  // [sorgente in node_modules, destinazione in vendor]
  ["vue/dist/vue.global.prod.js", "vue.global.prod.js"],
  ["axios/dist/axios.min.js", "axios.min.js"],
  ["chart.js/dist/chart.umd.js", "chart.umd.js"],
  ["@fortawesome/fontawesome-free/css/all.min.css", "fontawesome/css/all.min.css"],
];

await rm(vendor, { recursive: true, force: true });
await mkdir(vendor, { recursive: true });

for (const [src, dest] of files) {
  const from = join(nm, src);
  const to = join(vendor, dest);
  if (!existsSync(from)) {
    console.error(`MANCA: ${src} — hai eseguito 'npm install'?`);
    process.exit(1);
  }
  await mkdir(dirname(to), { recursive: true });
  await cp(from, to);
  console.log(`ok ${dest}`);
}

// Font Awesome ha bisogno anche dei webfont referenziati dal CSS
const fonts = join(nm, "@fortawesome/fontawesome-free/webfonts");
await cp(fonts, join(vendor, "fontawesome/webfonts"), { recursive: true });
console.log("ok fontawesome/webfonts");
