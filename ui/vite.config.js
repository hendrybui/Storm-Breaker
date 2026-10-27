import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// P11.1 — builds straight into the Flask static folder so /panel2 can load it
// without a separate dev server. Fixed asset names keep panel2.html stable.
export default defineConfig({
  plugins: [react()],
  // Flask serves static_folder at /assets (app.factory sets static_url_path).
  base: "/assets/ui_v2/",
  build: {
    outDir: "../storm-web/assets/ui_v2",
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: "app.js",
        assetFileNames: "app.[ext]",
        chunkFileNames: "chunk-[name].js",
      },
    },
  },
});
