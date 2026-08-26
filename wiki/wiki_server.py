#!/usr/bin/env python3
"""
LM Wiki Reader Server
A lightweight, zero-dependency documentation & wiki server for browsing LLM-generated research wikis.
Runs on http://localhost:5111 by default.
"""

import os
import sys
import json
import time
import re
import mimetypes
import argparse
import webbrowser
import threading
from pathlib import Path
from socketserver import ThreadingMixIn
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

PORT = 5111
HOST = "127.0.0.1"

# Directory paths
WORKSPACE_DIR = Path(__file__).resolve().parent
WIKI_DIR = WORKSPACE_DIR / ".wiki"
READER_STATIC_DIR = WORKSPACE_DIR / "wiki_reader"

# Global lock & cache for file metadata
_file_cache_lock = threading.Lock()
_file_cache = {}
_subscribers = []
_subscribers_lock = threading.Lock()


def parse_frontmatter(content: str):
    """Extract YAML frontmatter and markdown body without external dependencies."""
    frontmatter = {}
    body = content

    if content.startswith("---"):
        match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", content, re.DOTALL)
        if match:
            fm_text = match.group(1)
            body = match.group(2)

            for line in fm_text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip()

                    # Clean quotes
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]

                    # Parse arrays like [tag1, tag2]
                    if val.startswith("[") and val.endswith("]"):
                        items = [item.strip().strip("'\"") for item in val[1:-1].split(",") if item.strip()]
                        frontmatter[key] = items
                    # Parse integers / floats / booleans
                    elif val.isdigit():
                        frontmatter[key] = int(val)
                    elif val.lower() == "true":
                        frontmatter[key] = True
                    elif val.lower() == "false":
                        frontmatter[key] = False
                    else:
                        frontmatter[key] = val

    # Fallback to extract title from first # Heading if title not in frontmatter
    if "title" not in frontmatter:
        heading_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if heading_match:
            frontmatter["title"] = heading_match.group(1).strip()

    return frontmatter, body


def extract_links(content: str, doc_path: str):
    """Extract standard markdown links [text](path) and wikilinks [[path]]."""
    outlinks = []
    
    # Standard markdown links: [text](target)
    for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
        text, target = match.groups()
        # Ignore external URLs, anchor-only links, and mailto
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        outlinks.append({
            "text": text.strip(),
            "target": target.strip(),
            "type": "markdown"
        })

    # Wikilinks: [[target|text]] or [[target]]
    for match in re.finditer(r'\[\[([^\]]+)\]\]', content):
        inner = match.group(1).strip()
        if "|" in inner:
            target, text = inner.split("|", 1)
        else:
            target, text = inner, inner
        outlinks.append({
            "text": text.strip(),
            "target": target.strip(),
            "type": "wikilink"
        })

    return outlinks


def scan_all_documents():
    """Scan all markdown files in .wiki/ and workspace root, parse metadata and build graph."""
    documents = {}
    search_dirs = [WIKI_DIR, WORKSPACE_DIR]
    scanned_paths = set()

import datetime


def parse_date_info(doc_path: str, fm: dict, stat):
    """Extract standard ISO date and human display date from frontmatter, filename, or stats."""
    raw_date = None

    # 1. Check frontmatter fields
    for field in ["date", "created", "day", "timestamp"]:
        if field in fm and fm[field]:
            val = str(fm[field]).strip()
            # Match YYYY-MM-DD
            m = re.search(r'\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b', val)
            if m:
                raw_date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
                break
            # Match DD-MMM-YYYY or DDMMMYYYY (e.g. 15aug2026 or 15-aug-2026)
            m2 = re.search(r'\b(\d{1,2})[-_]?([a-zA-Z]{3,9})[-_]?(20\d{2})\b', val)
            if m2:
                try:
                    dt = datetime.datetime.strptime(f"{m2.group(1)} {m2.group(2)[:3]} {m2.group(3)}", "%d %b %Y")
                    raw_date = dt.strftime("%Y-%m-%d")
                    break
                except ValueError:
                    pass

    # 2. Check filename / path for YYYY-MM-DD or DDMMMYYYY
    if not raw_date:
        m = re.search(r'\b(20\d{2})[-_](\d{2})[-_](\d{2})\b', doc_path)
        if m:
            raw_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        else:
            m2 = re.search(r'\b(\d{1,2})[-_]?([a-zA-Z]{3,9})[-_]?(20\d{2})\b', doc_path)
            if m2:
                try:
                    dt = datetime.datetime.strptime(f"{m2.group(1)} {m2.group(2)[:3]} {m2.group(3)}", "%d %b %Y")
                    raw_date = dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass

    # 3. Format into human friendly display string
    if raw_date:
        try:
            dt = datetime.datetime.strptime(raw_date, "%Y-%m-%d")
            display_date = dt.strftime("%d %b %Y")  # e.g. 15 Aug 2026
            return {
                "rawDate": raw_date,
                "displayDate": display_date,
                "isGeneral": False
            }
        except ValueError:
            pass

    return {
        "rawDate": "0000-00-00",
        "displayDate": "General Notes & Reference",
        "isGeneral": True
    }


def scan_all_documents():
    """Scan all markdown files in .wiki/ and workspace root, parse metadata, dates and build graph."""
    documents = {}
    search_dirs = [WIKI_DIR, WORKSPACE_DIR]
    scanned_paths = set()

    for base_dir in search_dirs:
        if not base_dir.exists():
            continue
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") or d == ".wiki"]
            dirs[:] = [d for d in dirs if d not in ("node_modules", ".claude", "wiki_reader")]

            for file in files:
                if file.endswith(".md"):
                    full_path = Path(root) / file
                    try:
                        rel_path = full_path.relative_to(WORKSPACE_DIR).as_posix()
                    except ValueError:
                        continue

                    if rel_path in scanned_paths:
                        continue
                    scanned_paths.add(rel_path)

                    try:
                        stat = full_path.stat()
                        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                            raw_content = f.read()

                        fm, body = parse_frontmatter(raw_content)
                        outlinks = extract_links(raw_content, rel_path)
                        date_info = parse_date_info(rel_path, fm, stat)

                        category = "Other"
                        if rel_path.startswith(".wiki/raw/papers"):
                            category = "Raw Papers"
                        elif rel_path.startswith(".wiki/raw"):
                            category = "Raw Sources"
                        elif rel_path.startswith(".wiki/output"):
                            category = "Playbooks & Output"
                        elif rel_path.startswith(".wiki/articles"):
                            category = "Articles"
                        elif rel_path.startswith(".wiki/theses"):
                            category = "Theses"
                        elif rel_path.startswith(".wiki"):
                            category = "Hub & Index"
                        elif rel_path == "notes.md":
                            category = "Notes"

                        title = fm.get("title") or file.replace(".md", "").replace("-", " ").replace("_", " ").title()

                        documents[rel_path] = {
                            "path": rel_path,
                            "filename": file,
                            "title": title,
                            "category": category,
                            "frontmatter": fm,
                            "dateInfo": date_info,
                            "outlinks": outlinks,
                            "mtime": stat.st_mtime,
                            "size": stat.st_size,
                            "wordCount": len(body.split()),
                            "content": raw_content
                        }
                    except Exception as e:
                        print(f"[Warn] Error scanning {rel_path}: {e}")

    # Build backlinks
    for path, doc in documents.items():
        doc["backlinks"] = []

    for source_path, doc in documents.items():
        source_dir = Path(source_path).parent
        for outlink in doc["outlinks"]:
            target_str = outlink["target"]
            resolved_rel = None
            
            if target_str.endswith(".md"):
                candidate1 = (source_dir / target_str).resolve()
                try:
                    c1_rel = candidate1.relative_to(WORKSPACE_DIR).as_posix()
                    if c1_rel in documents:
                        resolved_rel = c1_rel
                except ValueError:
                    pass

            if not resolved_rel:
                target_stem = Path(target_str).stem.lower()
                for cand_path in documents:
                    if Path(cand_path).stem.lower() == target_stem or cand_path.lower().endswith(target_str.lower()):
                        resolved_rel = cand_path
                        break

            if resolved_rel and resolved_rel in documents:
                outlink["resolvedPath"] = resolved_rel
                documents[resolved_rel]["backlinks"].append({
                    "sourcePath": source_path,
                    "sourceTitle": doc["title"],
                    "linkText": outlink["text"]
                })

    return documents


def get_wiki_tree():
    """Build a structured tree hierarchy for sidebar navigation (both by Date and by Category)."""
    with _file_cache_lock:
        docs = scan_all_documents()
        
        # 1. Category groupings
        categories = {
            "Hub & Index": [],
            "Playbooks & Output": [],
            "Raw Papers": [],
            "Raw Sources": [],
            "Articles": [],
            "Theses": [],
            "Notes": [],
            "Other": []
        }

        # 2. Date-wise groupings (newest dates first)
        date_groups = {}

        for path, doc in sorted(docs.items(), key=lambda x: (x[1]["category"], x[1]["title"])):
            doc_meta = {k: v for k, v in doc.items() if k != "content"}
            categories[doc["category"]].append(doc_meta)

            # Date grouping
            d_info = doc["dateInfo"]
            raw_d = d_info["rawDate"]
            display_d = d_info["displayDate"]

            if raw_d not in date_groups:
                date_groups[raw_d] = {
                    "rawDate": raw_d,
                    "displayDate": display_d,
                    "isGeneral": d_info["isGeneral"],
                    "docs": [],
                    "counts": {"papers": 0, "playbooks": 0, "notes": 0, "other": 0}
                }

            date_groups[raw_d]["docs"].append(doc_meta)
            
            # Sub-counts
            if doc["category"] == "Raw Papers":
                date_groups[raw_d]["counts"]["papers"] += 1
            elif doc["category"] == "Playbooks & Output":
                date_groups[raw_d]["counts"]["playbooks"] += 1
            elif doc["category"] == "Notes":
                date_groups[raw_d]["counts"]["notes"] += 1
            else:
                date_groups[raw_d]["counts"]["other"] += 1

        # Sort date groups descending (newest dates first, general at the end)
        sorted_date_groups = {}
        for k in sorted(date_groups.keys(), reverse=True):
            if k != "0000-00-00":
                sorted_date_groups[k] = date_groups[k]
        if "0000-00-00" in date_groups:
            sorted_date_groups["0000-00-00"] = date_groups["0000-00-00"]

        filtered_categories = {k: v for k, v in categories.items() if len(v) > 0}

        return {
            "categories": filtered_categories,
            "dateGroups": sorted_date_groups,
            "totalCount": len(docs),
            "stats": {
                "papers": len(categories.get("Raw Papers", [])),
                "playbooks": len(categories.get("Playbooks & Output", [])),
                "articles": len(categories.get("Articles", [])),
                "hubs": len(categories.get("Hub & Index", [])),
                "dateCount": len([k for k in sorted_date_groups.keys() if k != "0000-00-00"])
            }
        }


def search_documents(query: str):
    """Full text search across title, tags, and content with snippet extraction."""
    if not query or len(query.strip()) == 0:
        return []

    q = query.lower().strip()
    words = q.split()
    results = []

    with _file_cache_lock:
        docs = scan_all_documents()

    for path, doc in docs.items():
        title = doc["title"].lower()
        tags = [str(t).lower() for t in doc["frontmatter"].get("tags", [])]
        summary = str(doc["frontmatter"].get("summary", "")).lower()
        content = doc["content"]
        content_lower = content.lower()

        score = 0
        snippets = []

        if q in title:
            score += 100
        elif any(w in title for w in words):
            score += 40

        if any(q in t for t in tags):
            score += 50
        elif any(w in t for t in tags for w in words):
            score += 25

        if q in summary:
            score += 30

        if q in content_lower:
            score += 20
            idx = content_lower.find(q)
            start = max(0, idx - 60)
            end = min(len(content), idx + len(q) + 100)
            snippet = content[start:end].strip()
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
            snippets.append(snippet)
        else:
            for w in words:
                if len(w) > 2 and w in content_lower:
                    score += 5
                    idx = content_lower.find(w)
                    start = max(0, idx - 50)
                    end = min(len(content), idx + len(w) + 80)
                    snippet = content[start:end].strip()
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(content):
                        snippet = snippet + "..."
                    snippets.append(snippet)
                    break

        if score > 0:
            doc_meta = {k: v for k, v in doc.items() if k != "content"}
            results.append({
                "document": doc_meta,
                "score": score,
                "snippets": snippets[:2]
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:20]


def get_graph_data():
    """Generate nodes and edges network data for knowledge graph visualization."""
    with _file_cache_lock:
        docs = scan_all_documents()

    nodes = []
    edges = []
    node_set = set()

    for path, doc in docs.items():
        node_set.add(path)
        group = doc["category"]
        val = 5
        if group == "Hub & Index":
            val = 14
        elif group == "Playbooks & Output":
            val = 12
        elif group == "Raw Papers":
            val = 8

        nodes.append({
            "id": path,
            "title": doc["title"],
            "category": doc["category"],
            "val": val,
            "tags": doc["frontmatter"].get("tags", []),
            "year": doc["frontmatter"].get("year", ""),
            "quality": doc["frontmatter"].get("quality", "")
        })

    for path, doc in docs.items():
        for outlink in doc["outlinks"]:
            resolved = outlink.get("resolvedPath")
            if resolved and resolved in node_set and resolved != path:
                edges.append({
                    "source": path,
                    "target": resolved,
                    "label": outlink.get("text", "")
                })

    return {"nodes": nodes, "edges": edges}


def watch_filesystem_loop():
    """Background watcher for file changes to send SSE notifications."""
    last_mtimes = {}
    while True:
        try:
            time.sleep(1.0)
            changed = False
            current_mtimes = {}
            for base in [WIKI_DIR, WORKSPACE_DIR]:
                if not base.exists():
                    continue
                for root, dirs, files in os.walk(base):
                    dirs[:] = [d for d in dirs if not d.startswith(".") or d == ".wiki"]
                    dirs[:] = [d for d in dirs if d not in ("node_modules", ".claude", "wiki_reader")]
                    for file in files:
                        if file.endswith(".md"):
                            fp = Path(root) / file
                            try:
                                mtime = fp.stat().st_mtime
                                current_mtimes[str(fp)] = mtime
                                if str(fp) in last_mtimes and last_mtimes[str(fp)] != mtime:
                                    changed = True
                            except OSError:
                                pass

            if last_mtimes and (changed or set(current_mtimes.keys()) != set(last_mtimes.keys())):
                with _subscribers_lock:
                    for sub_queue in _subscribers:
                        try:
                            sub_queue.append("reload")
                        except Exception:
                            pass

            last_mtimes = current_mtimes
        except Exception:
            time.sleep(2.0)


class WikiHTTPRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if args and len(args) >= 2 and str(args[1]).startswith(('4', '5')):
            super().log_message(format, *args)

    def end_headers_with_cors(self, content_type="application/json"):
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers_with_cors()

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/new-research":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body_bytes = self.rfile.read(content_length)
                data = json.loads(body_bytes.decode('utf-8'))

                # Validate required title
                title = data.get("title", "").strip()
                if not title:
                    self.send_response(400)
                    self.end_headers_with_cors()
                    self.wfile.write(json.dumps({"error": "Title is required"}).encode("utf-8"))
                    return

                doc_type = data.get("type", "paper").strip().lower()
                req_date = data.get("date", "").strip()
                if not req_date:
                    req_date = datetime.date.today().isoformat()
                
                # Normalize date (ensure YYYY-MM-DD)
                m = re.search(r'\b(20\d{2})[-_]?(\d{1,2})[-_]?(\d{1,2})\b', req_date)
                if m:
                    date_str = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
                else:
                    date_str = datetime.date.today().isoformat()

                # Slugify
                slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
                if len(slug) > 50:
                    slug = slug[:50].rstrip('-')

                # Determine directory & filename
                if doc_type == "paper":
                    target_dir = WIKI_DIR / "raw" / "papers"
                    filename = f"{date_str}-{slug}.md"
                elif doc_type == "playbook":
                    target_dir = WIKI_DIR / "output"
                    filename = f"playbook-{slug}-{date_str}.md"
                elif doc_type == "thesis":
                    target_dir = WIKI_DIR / "theses"
                    filename = f"{date_str}-{slug}.md"
                else:
                    target_dir = WIKI_DIR / "articles"
                    filename = f"{date_str}-{slug}.md"

                target_dir.mkdir(parents=True, exist_ok=True)
                full_file_path = target_dir / filename

                # Frontmatter fields
                tags = data.get("tags", [])
                if isinstance(tags, str):
                    tags = [t.strip().lstrip('#') for t in tags.split(',') if t.strip()]

                authors = data.get("authors", "").strip()
                source = data.get("source", "").strip()
                summary = data.get("summary", "").strip()
                year = data.get("year", datetime.date.today().year)
                quality = int(data.get("quality", 5))
                confidence = data.get("confidence", "high").strip()

                custom_content = data.get("content", "").strip()
                if not custom_content:
                    custom_content = f"""# {title}

**Authors:** {authors or 'Research Agent'} ({year})

## Key Findings
- {summary or 'Summary of the research findings...'}

## Thesis Potential & Methodology
- Novel contributions and experimental validation
- Feasibility analysis and benchmark comparisons
"""

                # Construct frontmatter
                fm_lines = [
                    "---",
                    f"date: {date_str}",
                    f"title: \"{title}\""
                ]
                if source:
                    fm_lines.append(f"source: {source}")
                fm_lines.append(f"type: {doc_type}")
                fm_lines.append(f"year: {year}")
                if tags:
                    tag_str = "[" + ", ".join(tags) + "]"
                    fm_lines.append(f"tags: {tag_str}")
                fm_lines.append(f"quality: {quality}")
                fm_lines.append(f"confidence: {confidence}")
                if summary:
                    fm_lines.append(f"summary: {summary}")
                fm_lines.append("---\n")

                file_content = "\n".join(fm_lines) + custom_content

                with open(full_file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)

                rel_path = full_file_path.relative_to(WORKSPACE_DIR).as_posix()

                # Update .wiki/log.md
                log_file = WIKI_DIR / "log.md"
                if log_file.exists():
                    try:
                        with open(log_file, "r", encoding="utf-8") as lf:
                            current_log = lf.read()
                        log_entry = f"\n## [{date_str}] research | \"{title}\" → 1 {doc_type} added ({filename})\n"
                        if summary:
                            log_entry += f"- Summary: {summary}\n"
                        if tags:
                            log_entry += f"- Tags: {', '.join(tags)}\n"
                        with open(log_file, "w", encoding="utf-8") as lf:
                            lf.write(current_log + log_entry)
                    except Exception as le:
                        print(f"[Warn] Failed updating log.md: {le}")

                # Notify SSE subscribers
                with _subscribers_lock:
                    for sub_queue in _subscribers:
                        try:
                            sub_queue.append("reload")
                        except Exception:
                            pass

                self.send_response(200)
                self.end_headers_with_cors("application/json")
                self.wfile.write(json.dumps({
                    "success": True,
                    "path": rel_path,
                    "title": title,
                    "date": date_str
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers_with_cors()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers_with_cors()
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query_params = parse_qs(parsed.query)

        # 1. API: Navigation Tree
        if path == "/api/tree":
            try:
                tree_data = get_wiki_tree()
                self.send_response(200)
                self.end_headers_with_cors("application/json")
                self.wfile.write(json.dumps(tree_data).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers_with_cors()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 2. API: Document Detail
        elif path == "/api/document":
            doc_path_param = query_params.get("path", [None])[0]
            if not doc_path_param:
                self.send_response(400)
                self.end_headers_with_cors()
                self.wfile.write(json.dumps({"error": "Missing 'path' query parameter"}).encode("utf-8"))
                return

            doc_path_param = unquote(doc_path_param).lstrip("/")
            full_file_path = (WORKSPACE_DIR / doc_path_param).resolve()

            try:
                full_file_path.relative_to(WORKSPACE_DIR)
            except ValueError:
                self.send_response(403)
                self.end_headers_with_cors()
                self.wfile.write(json.dumps({"error": "Access denied"}).encode("utf-8"))
                return

            if not full_file_path.is_file() or not full_file_path.name.endswith(".md"):
                self.send_response(404)
                self.end_headers_with_cors()
                self.wfile.write(json.dumps({"error": f"Document not found: {doc_path_param}"}).encode("utf-8"))
                return

            try:
                with open(full_file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                fm, body = parse_frontmatter(content)
                stat = full_file_path.stat()
                rel_path = full_file_path.relative_to(WORKSPACE_DIR).as_posix()

                with _file_cache_lock:
                    all_docs = scan_all_documents()
                
                current_doc_meta = all_docs.get(rel_path, {})
                backlinks = current_doc_meta.get("backlinks", [])
                outlinks = current_doc_meta.get("outlinks", [])

                response_data = {
                    "path": rel_path,
                    "filename": full_file_path.name,
                    "title": fm.get("title") or full_file_path.stem.replace("-", " ").title(),
                    "frontmatter": fm,
                    "content": content,
                    "body": body,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                    "wordCount": len(body.split()),
                    "backlinks": backlinks,
                    "outlinks": outlinks
                }

                self.send_response(200)
                self.end_headers_with_cors("application/json")
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers_with_cors()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 3. API: Search
        elif path == "/api/search":
            q = query_params.get("q", [""])[0]
            try:
                results = search_documents(q)
                self.send_response(200)
                self.end_headers_with_cors("application/json")
                self.wfile.write(json.dumps({"query": q, "results": results}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers_with_cors()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 4. API: Knowledge Graph
        elif path == "/api/graph":
            try:
                graph_data = get_graph_data()
                self.send_response(200)
                self.end_headers_with_cors("application/json")
                self.wfile.write(json.dumps(graph_data).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers_with_cors()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 5. API: Server-Sent Events for Live Reload
        elif path == "/api/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            sub_queue = []
            with _subscribers_lock:
                _subscribers.append(sub_queue)

            try:
                self.wfile.write(b": connected\n\n")
                self.wfile.flush()

                while True:
                    time.sleep(0.5)
                    while sub_queue:
                        event = sub_queue.pop(0)
                        msg = f"event: change\ndata: {json.dumps({'action': event})}\n\n"
                        self.wfile.write(msg.encode("utf-8"))
                        self.wfile.flush()
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with _subscribers_lock:
                    if sub_queue in _subscribers:
                        _subscribers.remove(sub_queue)
            return

        # 6. Raw file access
        elif path.startswith("/raw/"):
            rel_file = unquote(path[5:])
            full_path = (WORKSPACE_DIR / rel_file).resolve()
            try:
                full_path.relative_to(WORKSPACE_DIR)
                if full_path.is_file():
                    mime, _ = mimetypes.guess_type(str(full_path))
                    self.send_response(200)
                    self.end_headers_with_cors(mime or "application/octet-stream")
                    with open(full_path, "rb") as f:
                        self.wfile.write(f.read())
                    return
            except Exception:
                pass
            self.send_response(404)
            self.end_headers_with_cors()
            self.wfile.write(b"Not Found")
            return

        # 7. Static UI Files (wiki_reader/)
        static_file = path.lstrip("/")
        if not static_file or static_file == "/":
            static_file = "index.html"

        target_file = (READER_STATIC_DIR / static_file).resolve()
        try:
            target_file.relative_to(READER_STATIC_DIR)
        except ValueError:
            target_file = READER_STATIC_DIR / "index.html"

        if not target_file.is_file():
            target_file = READER_STATIC_DIR / "index.html"

        if target_file.is_file():
            mime, _ = mimetypes.guess_type(str(target_file))
            self.send_response(200)
            self.end_headers_with_cors(mime or "text/html; charset=utf-8")
            with open(target_file, "rb") as f:
                self.wfile.write(f.read())
            return

        self.send_response(404)
        self.end_headers_with_cors()
        self.wfile.write(b"Not Found")


class ReusableThreadingServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_server(port=PORT, host=HOST, auto_open=False):
    server_address = (host, port)
    
    watcher_thread = threading.Thread(target=watch_filesystem_loop, daemon=True)
    watcher_thread.start()

    try:
        httpd = ReusableThreadingServer(server_address, WikiHTTPRequestHandler)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"[Error] Port {port} is already in use.")
            print(f"To free up port {port}, run: lsof -ti:{port} | xargs kill -9")
            sys.exit(1)
        raise

    url = f"http://localhost:{port}"
    print(f"\n=======================================================")
    print(f" 📚  LM Wiki Reader is running!")
    print(f" 🌐  Open in browser: {url}")
    print(f" 📁  Scanning: {WORKSPACE_DIR}")
    print(f" 🔄  Live SSE Auto-Sync: Active")
    print(f" Press Ctrl+C to stop the server")
    print(f"=======================================================\n")

    if auto_open:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping LM Wiki Reader server...")
        httpd.server_close()
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LM Wiki Reader Server")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port to bind (default: {PORT})")
    parser.add_argument("--host", type=str, default=HOST, help=f"Host address (default: {HOST})")
    parser.add_argument("--open", action="store_true", help="Automatically open in default web browser")
    parser.add_argument("--no-open", action="store_true", help="Do not open web browser")

    args = parser.parse_args()
    open_browser = args.open
    start_server(port=args.port, host=args.host, auto_open=open_browser)
