# 📚 LM Wiki Reader

A modern, fast, zero-dependency visual documentation reader for LLM-generated research wikis, playbooks, and markdown notes.

Runs on `http://localhost:5111`.

---

## 🚀 Quick Start

To launch the reader, run:

```bash
./run_wiki.sh
```

Or using Python directly:

```bash
python3 wiki_server.py --port 5111
```

Once running, navigate to [http://localhost:5111](http://localhost:5111) in your browser.

---

## ✨ Features

- **📑 Leftbar Navigation Tree**: Organized by *Hub & Index*, *Playbooks & Output*, *Raw Papers*, *Articles*, and *Workspace Notes*.
- **⚡ Live SSE Auto-Sync**: Automatically detects when LLM agents create or modify wiki files and updates the reader live in real time.
- **🏷️ Frontmatter Metadata Card**: Displays paper types, authors, publication years, quality stars (★★★★★), confidence ratings, and direct source links (e.g. arXiv).
- **🔍 Global Command Palette (`⌘K` / `Ctrl+K`)**: Full-text fuzzy search across all research files with match snippets and keyboard navigation.
- **🕸️ Interactive Knowledge Graph (`⌘G`)**: Visual network graph displaying connections and citations across all wiki documents.
- **📐 Mathematical Formulas & Diagrams**: Fast LaTeX math rendering with KaTeX and architecture diagrams with Mermaid.js.
- **🔗 Smart Internal Link Resolver**: Seamlessly intercepts markdown links (`[paper](papers/...)`) and Obsidian wikilinks (`[[paper]]`) without full page reloads.
- **🌓 Theme Switching**: Dark slate mode (Obsidian-inspired) and crisp editorial light mode.
- **🖨️ Clean Export / Print Mode**: Academic paper print styling for reading and PDF export.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `⌘K` or `Ctrl+K` | Open Global Command Palette / Search |
| `/` | Quick Search Wiki |
| `⌘G` or `Ctrl+G` | Toggle Interactive Knowledge Graph Modal |
| `Esc` | Close Search / Graph Modal |
| `↑` / `↓` | Navigate search results |
| `Enter` | Select and open document from search |
