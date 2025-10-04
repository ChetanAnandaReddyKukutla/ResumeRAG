# Visual Assets

This directory contains visual assets for documentation and marketing.

## Files

### Architecture Diagrams
- `architecture-diagram.png` - System architecture overview
- `dataflow-diagram.png` - Data flow through the system
- `er-diagram.png` - Database entity-relationship diagram

### Screenshots
- `screenshot-upload.png` - Upload page interface
- `screenshot-search.png` - Search results page
- `screenshot-jobs.png` - Job matching interface
- `screenshot-detail.png` - Candidate detail view

### Marketing
- `banner-cover.png` - Repository banner/cover image
- `demo-gif.gif` - Animated demo of key features

## Generating Diagrams

### From Mermaid (in ARCHITECTURE.md)

Use [Mermaid Live Editor](https://mermaid.live/) to generate PNG/SVG:

1. Copy Mermaid code from ARCHITECTURE.md
2. Paste into editor
3. Export as PNG (transparent background)
4. Save to this directory

### From PlantUML

```bash
# Install PlantUML
brew install plantuml  # macOS
# or download from https://plantuml.com/

# Generate diagram
plantuml docs/architecture.puml -o assets/
```

### Screenshots

Use browser's screenshot tool or:
- **macOS**: Cmd+Shift+4
- **Windows**: Win+Shift+S
- **Chrome DevTools**: Cmd/Ctrl+Shift+P → "Capture full size screenshot"

Recommended size: 1920x1080 for full screenshots, crop to relevant areas

### Demo GIF

Use [ScreenToGif](https://www.screentogif.com/) or:

```bash
# Record with QuickTime/OBS
# Convert to GIF with ffmpeg
ffmpeg -i demo.mp4 -vf "fps=10,scale=1280:-1:flags=lanczos" -loop 0 demo-gif.gif

# Optimize size
gifsicle -O3 --lossy=80 demo-gif.gif -o demo-gif-optimized.gif
```

Max size for GitHub: 10 MB

## Placeholder Images

Until real screenshots are created, use these placeholders:

```markdown
![Upload Page](https://via.placeholder.com/1200x800/4A5568/FFFFFF?text=Upload+Page)
![Search Results](https://via.placeholder.com/1200x800/3B82F6/FFFFFF?text=Search+Results)
![Job Matching](https://via.placeholder.com/1200x800/10B981/FFFFFF?text=Job+Matching)
```

---

_Last updated: October 4, 2025_
