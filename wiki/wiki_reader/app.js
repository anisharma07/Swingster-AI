/**
 * LM Wiki Reader — Client Application
 * Handles date-wise documentation rendering, logging new research, tree navigation,
 * search, graph visualization, KaTeX math, Mermaid diagrams, and live SSE sync.
 */

// Global State
const state = {
  tree: null,
  currentDoc: null,
  currentPath: null,
  viewMode: localStorage.getItem('wiki_view_mode') || 'date', // 'date' or 'category'
  activeFilter: 'all',
  searchQuery: '',
  theme: localStorage.getItem('wiki_theme') || 'dark',
  fontSize: parseInt(localStorage.getItem('wiki_font_size') || '16', 10),
  graphData: null,
  allDocPaths: [],
  allDocTitles: {},
  isRawView: false
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initFontSizer();
  initMarked();
  initMermaid();
  initRouter();
  initSidebar();
  initLogResearchModal();
  initOutlineScrollspy();
  initSearchModal();
  initGraphModal();
  initLiveSync();
  initTopbarActions();
});

/* ==========================================
   THEME & FONT SIZER
   ========================================== */

function initTheme() {
  document.documentElement.setAttribute('data-theme', state.theme);
  updateThemeIcons();

  const themeBtn = document.getElementById('btn-theme-toggle');
  themeBtn?.addEventListener('click', () => {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', state.theme);
    localStorage.setItem('wiki_theme', state.theme);
    updateThemeIcons();
    
    const hljsTheme = document.getElementById('hljs-theme');
    if (hljsTheme) {
      hljsTheme.href = state.theme === 'dark' 
        ? 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css'
        : 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-light.min.css';
    }
  });
}

function updateThemeIcons() {
  const moonIcon = document.querySelector('.icon-moon');
  const sunIcon = document.querySelector('.icon-sun');
  if (moonIcon && sunIcon) {
    if (state.theme === 'dark') {
      moonIcon.style.display = 'block';
      sunIcon.style.display = 'none';
    } else {
      moonIcon.style.display = 'none';
      sunIcon.style.display = 'block';
    }
  }
}

function initFontSizer() {
  applyFontSize(state.fontSize);

  document.getElementById('btn-font-dec')?.addEventListener('click', () => {
    if (state.fontSize > 13) {
      state.fontSize -= 1;
      applyFontSize(state.fontSize);
    }
  });

  document.getElementById('btn-font-inc')?.addEventListener('click', () => {
    if (state.fontSize < 22) {
      state.fontSize += 1;
      applyFontSize(state.fontSize);
    }
  });
}

function applyFontSize(size) {
  document.documentElement.style.setProperty('--content-font-size', `${size}px`);
  localStorage.setItem('wiki_font_size', size.toString());
}

/* ==========================================
   ROUTING & TREE LOADER
   ========================================== */

async function initRouter() {
  window.addEventListener('hashchange', handleHashChange);
  await loadTree();

  const hash = window.location.hash.replace(/^#\/?/, '');
  if (hash) {
    loadDocument(hash);
  } else if (state.allDocPaths.length > 0) {
    const indexDoc = state.allDocPaths.find(p => p.endsWith('_index.md')) || state.allDocPaths[0];
    window.location.hash = `#/${indexDoc}`;
  }
}

function handleHashChange() {
  const hash = window.location.hash.replace(/^#\/?/, '');
  if (hash) {
    loadDocument(hash);
  } else if (state.allDocPaths.length > 0) {
    const indexDoc = state.allDocPaths.find(p => p.endsWith('_index.md')) || state.allDocPaths[0];
    window.location.hash = `#/${indexDoc}`;
  }
}

async function loadTree() {
  try {
    const res = await fetch('/api/tree');
    if (!res.ok) throw new Error('Failed to load navigation tree');
    const data = await res.json();
    state.tree = data;
    
    state.allDocPaths = [];
    state.allDocTitles = {};
    for (const [cat, docs] of Object.entries(data.categories || {})) {
      for (const doc of docs) {
        state.allDocPaths.push(doc.path);
        state.allDocTitles[doc.path] = doc.title;
      }
    }

    renderTree();
    document.getElementById('stat-total-docs').textContent = `${data.totalCount || 0} docs`;
  } catch (err) {
    console.error('Error loading tree:', err);
    document.getElementById('sidebar-nav').innerHTML = `
      <div class="nav-loading" style="color: var(--accent-rose);">
        <span>Failed to load wiki tree</span>
        <button class="btn-action-small" onclick="loadTree()">Retry</button>
      </div>
    `;
  }
}

function renderTree() {
  const nav = document.getElementById('sidebar-nav');
  if (!nav || !state.tree) return;

  const searchFilter = (document.getElementById('tree-filter-input')?.value || '').toLowerCase().trim();
  let html = '';

  if (state.viewMode === 'date' && state.tree.dateGroups) {
    // DATE-WISE SEGREGATION MODE
    const dateGroups = state.tree.dateGroups;
    let isFirstGroup = true;

    for (const [rawDate, group] of Object.entries(dateGroups)) {
      const filteredDocs = group.docs.filter(doc => {
        if (!searchFilter) return true;
        const titleMatch = doc.title.toLowerCase().includes(searchFilter);
        const pathMatch = doc.path.toLowerCase().includes(searchFilter);
        const tags = (doc.frontmatter?.tags || []).map(t => String(t).toLowerCase());
        const tagMatch = tags.some(t => t.includes(searchFilter));
        return titleMatch || pathMatch || tagMatch;
      });

      if (filteredDocs.length === 0) continue;

      const collapsedClass = isFirstGroup ? '' : 'collapsed';
      isFirstGroup = false;

      const counts = group.counts || {};
      const subparts = [];
      if (counts.papers) subparts.push(`${counts.papers} paper${counts.papers > 1 ? 's' : ''}`);
      if (counts.playbooks) subparts.push(`${counts.playbooks} playbook`);
      if (counts.notes) subparts.push(`${counts.notes} note`);
      const summaryText = subparts.length > 0 ? subparts.join(' · ') : `${filteredDocs.length} items`;

      html += `
        <div class="date-section ${collapsedClass}" data-date="${rawDate}">
          <div class="date-section-header">
            <span class="date-section-title">
              <svg class="date-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
              <span>📅 ${group.displayDate}</span>
            </span>
            <div class="date-header-badges">
              <span class="date-count-badge" title="${summaryText}">${filteredDocs.length}</span>
            </div>
          </div>
          <ul class="date-items-list">
      `;

      for (const doc of filteredDocs) {
        const isActive = state.currentPath === doc.path ? 'active' : '';
        const docType = doc.frontmatter?.type || '';
        let badgeClass = 'paper';
        if (docType === 'research-playbook' || docType === 'playbook') badgeClass = 'playbook';
        else if (docType === 'hub') badgeClass = 'hub';

        html += `
          <li class="tree-item">
            <a href="#/${doc.path}" class="tree-link ${isActive}" data-path="${doc.path}" title="${doc.title} (${doc.path})">
              <span class="tree-item-icon">
                ${getDocIcon(doc.category, docType)}
              </span>
              <span class="tree-item-label">${doc.title}</span>
              ${docType ? `<span class="tree-item-badge ${badgeClass}">${docType.replace('research-', '')}</span>` : ''}
            </a>
          </li>
        `;
      }

      html += `
          </ul>
        </div>
      `;
    }
  } else {
    // CATEGORY-WISE MODE
    const categories = state.tree.categories || {};
    const filter = state.activeFilter;

    for (const [categoryName, docs] of Object.entries(categories)) {
      if (filter !== 'all' && categoryName !== filter) continue;

      const filteredDocs = docs.filter(doc => {
        if (!searchFilter) return true;
        const titleMatch = doc.title.toLowerCase().includes(searchFilter);
        const pathMatch = doc.path.toLowerCase().includes(searchFilter);
        const tags = (doc.frontmatter?.tags || []).map(t => String(t).toLowerCase());
        const tagMatch = tags.some(t => t.includes(searchFilter));
        return titleMatch || pathMatch || tagMatch;
      });

      if (filteredDocs.length === 0) continue;

      html += `
        <div class="tree-section" data-category="${categoryName}">
          <div class="tree-section-header">
            <span class="tree-section-title">
              <svg class="tree-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
              ${categoryName}
            </span>
            <span class="tree-count-badge">${filteredDocs.length}</span>
          </div>
          <ul class="tree-items-list">
      `;

      for (const doc of filteredDocs) {
        const isActive = state.currentPath === doc.path ? 'active' : '';
        const docType = doc.frontmatter?.type || '';
        let badgeClass = 'paper';
        if (docType === 'research-playbook' || docType === 'playbook') badgeClass = 'playbook';
        else if (docType === 'hub') badgeClass = 'hub';

        html += `
          <li class="tree-item">
            <a href="#/${doc.path}" class="tree-link ${isActive}" data-path="${doc.path}" title="${doc.title} (${doc.path})">
              <span class="tree-item-icon">
                ${getDocIcon(doc.category, docType)}
              </span>
              <span class="tree-item-label">${doc.title}</span>
              ${docType ? `<span class="tree-item-badge ${badgeClass}">${docType.replace('research-', '')}</span>` : ''}
            </a>
          </li>
        `;
      }

      html += `
          </ul>
        </div>
      `;
    }
  }

  if (html === '') {
    html = `<div class="search-hint">No matching research documents found</div>`;
  }

  nav.innerHTML = html;

  nav.querySelectorAll('.date-section-header, .tree-section-header').forEach(header => {
    header.addEventListener('click', () => {
      header.parentElement.classList.toggle('collapsed');
    });
  });
}

function getDocIcon(category, type) {
  if (type === 'hub' || category === 'Hub & Index') {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>`;
  }
  if (type === 'research-playbook' || category === 'Playbooks & Output') {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>`;
  }
  if (category === 'Raw Papers') {
    return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>`;
  }
  return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"></path></svg>`;
}

function updateActiveSidebarLink() {
  document.querySelectorAll('.tree-link').forEach(link => {
    if (link.getAttribute('data-path') === state.currentPath) {
      link.classList.add('active');
      const parentSection = link.closest('.date-section, .tree-section');
      if (parentSection) {
        parentSection.classList.remove('collapsed');
      }
    } else {
      link.classList.remove('active');
    }
  });
}

/* ==========================================
   DOCUMENT LOADER & RENDERER
   ========================================== */

async function loadDocument(docPath) {
  state.currentPath = docPath;
  updateActiveSidebarLink();

  const markdownBody = document.getElementById('markdown-body');
  const rawBody = document.getElementById('raw-markdown-body');
  const hero = document.getElementById('frontmatter-hero');

  if (markdownBody) {
    markdownBody.innerHTML = `
      <div class="nav-loading">
        <div class="spinner"></div>
        <span>Loading document...</span>
      </div>
    `;
  }

  try {
    const res = await fetch(`/api/document?path=${encodeURIComponent(docPath)}`);
    if (!res.ok) throw new Error(`Document not found: ${docPath}`);
    const data = await res.json();
    state.currentDoc = data;

    renderBreadcrumbs(docPath, data.title);

    const wordCount = data.wordCount || 0;
    const readTimeMinutes = Math.max(1, Math.ceil(wordCount / 200));
    document.getElementById('stat-word-count').textContent = `${wordCount} words`;
    document.getElementById('stat-read-time').textContent = `⏱ ${readTimeMinutes} min read`;

    const docDate = data.frontmatter?.date || data.frontmatter?.created || '15 Aug 2026';
    const statDateEl = document.getElementById('stat-doc-date');
    if (statDateEl) {
      statDateEl.textContent = `📅 ${docDate}`;
    }

    renderFrontmatterHero(data.frontmatter, data.title);

    const rawText = data.body !== undefined ? data.body : data.content;
    const renderedHtml = renderMarkdownWithPlugins(rawText || '');
    if (markdownBody) {
      markdownBody.innerHTML = renderedHtml;
    }

    if (rawBody) {
      const codeEl = rawBody.querySelector('code');
      if (codeEl) codeEl.textContent = data.content;
    }

    postRenderEnhancements(markdownBody, docPath);
    generateOutline(markdownBody);
    renderBacklinks(data.backlinks || []);
    renderDocNavFooter(docPath);

    document.getElementById('main-content').scrollTop = 0;
    updateReadingProgress();

  } catch (err) {
    console.error('Error loading doc:', err);
    if (markdownBody) {
      markdownBody.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon" style="color: var(--accent-rose);">⚠️</div>
          <h2>Could not load document</h2>
          <p>${err.message}</p>
          <button class="btn-action" style="margin: 16px auto;" onclick="loadDocument('${docPath}')">Retry</button>
        </div>
      `;
    }
    if (hero) hero.style.display = 'none';
  }
}

function renderBreadcrumbs(docPath, title) {
  const parts = docPath.split('/');
  let html = `<span class="crumb root" onclick="window.location.hash='#/${state.allDocPaths[0]}'" style="cursor: pointer;">Wiki</span>`;

  for (let i = 0; i < parts.length - 1; i++) {
    html += `
      <span class="crumb separator">/</span>
      <span class="crumb">${parts[i].replace(/^\./, '')}</span>
    `;
  }

  html += `
    <span class="crumb separator">/</span>
    <span class="crumb current">${title || parts[parts.length - 1]}</span>
  `;

  document.getElementById('breadcrumbs').innerHTML = html;
}

function renderFrontmatterHero(fm, fallbackTitle) {
  const hero = document.getElementById('frontmatter-hero');
  if (!fm || Object.keys(fm).length === 0) {
    if (hero) hero.style.display = 'none';
    return;
  }

  if (hero) hero.style.display = 'block';

  document.getElementById('hero-title').textContent = fm.title || fallbackTitle;

  const typeBadge = document.getElementById('hero-type-badge');
  if (fm.type) {
    typeBadge.textContent = fm.type.toUpperCase();
    typeBadge.style.display = 'inline-block';
  } else {
    typeBadge.style.display = 'none';
  }

  const scoresContainer = document.getElementById('hero-scores');
  let scoresHtml = '';
  if (fm.quality) {
    const stars = '★'.repeat(Math.min(5, Number(fm.quality))) + '☆'.repeat(Math.max(0, 5 - Number(fm.quality)));
    scoresHtml += `<span class="hero-pill quality" title="Quality rating: ${fm.quality}/5">${stars} (${fm.quality}/5)</span>`;
  }
  if (fm.confidence) {
    scoresHtml += `<span class="hero-pill confidence" title="Confidence level">Confidence: ${fm.confidence}</span>`;
  }
  scoresContainer.innerHTML = scoresHtml;

  const dateBadge = document.getElementById('hero-date-badge');
  const dVal = fm.date || fm.created || fm.year;
  if (dVal) {
    dateBadge.textContent = `📅 ${dVal}`;
    dateBadge.style.display = 'inline-block';
  } else {
    dateBadge.style.display = 'none';
  }

  const authorsEl = document.getElementById('hero-authors');
  if (fm.authors || fm.author) {
    authorsEl.innerHTML = `<strong>Authors:</strong> ${fm.authors || fm.author}`;
    authorsEl.style.display = 'block';
  } else {
    authorsEl.style.display = 'none';
  }

  const sourceEl = document.getElementById('hero-source');
  if (fm.source) {
    const isUrl = String(fm.source).startsWith('http');
    sourceEl.innerHTML = `
      <strong>Source:</strong> 
      ${isUrl ? `<a href="${fm.source}" target="_blank" rel="noopener noreferrer">${fm.source} <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg></a>` : fm.source}
    `;
    sourceEl.style.display = 'block';
  } else {
    sourceEl.style.display = 'none';
  }

  const tagsEl = document.getElementById('hero-tags');
  if (fm.tags && Array.isArray(fm.tags) && fm.tags.length > 0) {
    tagsEl.innerHTML = fm.tags.map(t => `<span class="tag-chip" onclick="filterByTag('${t}')">#${t}</span>`).join('');
    tagsEl.style.display = 'flex';
  } else {
    tagsEl.style.display = 'none';
  }

  const summaryEl = document.getElementById('hero-summary');
  if (fm.summary) {
    summaryEl.innerHTML = `<strong>Summary:</strong> ${fm.summary}`;
    summaryEl.style.display = 'block';
  } else {
    summaryEl.style.display = 'none';
  }
}

function filterByTag(tag) {
  const treeFilter = document.getElementById('tree-filter-input');
  if (treeFilter) {
    treeFilter.value = tag;
    document.getElementById('tree-clear-filter').style.display = 'block';
    renderTree();
  }
}

/* ==========================================
   MARKDOWN PARSER & EXTENSIONS
   ========================================== */

function initMarked() {
  if (window.marked) {
    try {
      marked.setOptions({
        gfm: true,
        breaks: true
      });
    } catch (e) {}
  }
}

function initMermaid() {
  if (window.mermaid) {
    try {
      mermaid.initialize({
        startOnLoad: false,
        theme: state.theme === 'dark' ? 'dark' : 'default',
        securityLevel: 'loose'
      });
    } catch (e) {}
  }
}

function renderMarkdownWithPlugins(markdownText) {
  if (!markdownText) return '';
  try {
    let processed = markdownText.replace(
      /^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\r?\n((?:>.*\r?\n?)*)/gim,
      function(match, type, content) {
        const cleanContent = content.replace(/^>\s?/gm, '').trim();
        const lowerType = type.toLowerCase();
        return `<div class="admonition ${lowerType}"><div class="admonition-title">${type}</div>\n\n${cleanContent}\n\n</div>\n`;
      }
    );

    processed = processed.replace(/\[\[(.*?)\]\]/g, (match, inner) => {
      let target = inner.trim();
      let text = target;
      if (inner.includes('|')) {
        const parts = inner.split('|');
        target = parts[0].trim();
        text = parts[1].trim();
      }
      return `[${text}](${target}.md)`;
    });

    if (window.marked && typeof window.marked.parse === 'function') {
      return window.marked.parse(processed);
    }
  } catch (e) {
    console.error('Markdown parsing error:', e);
  }
  return `<pre style="white-space: pre-wrap; font-family: inherit;">${escapeHtml(markdownText)}</pre>`;
}

function postRenderEnhancements(container, currentDocPath) {
  if (!container) return;
  const currentDir = currentDocPath.substring(0, currentDocPath.lastIndexOf('/'));

  try {
    container.querySelectorAll('a').forEach(anchor => {
      const href = anchor.getAttribute('href');
      if (!href) return;

      if (!href.startsWith('http://') && !href.startsWith('https://') && !href.startsWith('#') && !href.startsWith('mailto:')) {
        anchor.classList.add('internal-wiki-link');
        
        let targetPath = href;
        if (targetPath.startsWith('/')) {
          targetPath = targetPath.substring(1);
        } else if (currentDir) {
          const parts = (currentDir + '/' + targetPath).split('/');
          const stack = [];
          for (const p of parts) {
            if (p === '.' || p === '') continue;
            if (p === '..') {
              if (stack.length > 0) stack.pop();
            } else {
              stack.push(p);
            }
          }
          targetPath = stack.join('/');
        }

        if (!targetPath.endsWith('.md') && state.allDocPaths.some(p => p.endsWith(targetPath + '.md'))) {
          targetPath = targetPath + '.md';
        }

        anchor.setAttribute('href', `#/${targetPath}`);
        anchor.addEventListener('click', (e) => {
          e.preventDefault();
          window.location.hash = `#/${targetPath}`;
        });
      } else if (href.startsWith('http')) {
        anchor.setAttribute('target', '_blank');
        anchor.setAttribute('rel', 'noopener noreferrer');
      }
    });

    container.querySelectorAll('table').forEach(table => {
      if (!table.parentElement.classList.contains('table-wrapper')) {
        const wrapper = document.createElement('div');
        wrapper.className = 'table-wrapper';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
      }
    });

    container.querySelectorAll('pre code').forEach(codeBlock => {
      const pre = codeBlock.parentElement;
      if (pre.parentElement.classList.contains('code-block-container')) return;

      const langClass = Array.from(codeBlock.classList).find(c => c.startsWith('language-'));
      const lang = langClass ? langClass.replace('language-', '') : 'text';

      if (lang === 'mermaid' && window.mermaid) {
        const mermaidContainer = document.createElement('div');
        mermaidContainer.className = 'mermaid';
        mermaidContainer.textContent = codeBlock.textContent;
        pre.parentNode.replaceChild(mermaidContainer, pre);
        try {
          mermaid.init(undefined, mermaidContainer);
        } catch (e) {}
        return;
      }

      if (window.hljs) {
        try {
          hljs.highlightElement(codeBlock);
        } catch (e) {}
      }

      const containerDiv = document.createElement('div');
      containerDiv.className = 'code-block-container';

      const header = document.createElement('div');
      header.className = 'code-block-header';
      header.innerHTML = `
        <span class="code-lang-badge">${lang}</span>
        <button class="btn-copy-code" title="Copy code">Copy</button>
      `;

      const copyBtn = header.querySelector('.btn-copy-code');
      copyBtn?.addEventListener('click', () => {
        navigator.clipboard.writeText(codeBlock.textContent).then(() => {
          copyBtn.textContent = 'Copied!';
          setTimeout(() => { copyBtn.textContent = 'Copy'; }, 2000);
        });
      });

      pre.parentNode.insertBefore(containerDiv, pre);
      containerDiv.appendChild(header);
      containerDiv.appendChild(pre);
    });

    if (window.renderMathInElement) {
      try {
        renderMathInElement(container, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false },
            { left: '\\(', right: '\\)', display: false },
            { left: '\\[', right: '\\]', display: true }
          ],
          throwOnError: false
        });
      } catch (e) {}
    }
  } catch (err) {
    console.warn('postRenderEnhancements warning:', err);
  }
}

/* ==========================================
   OUTLINE (TABLE OF CONTENTS) & SCROLLSPY
   ========================================== */

function generateOutline(container) {
  const outlineList = document.getElementById('outline-list');
  if (!outlineList) return;
  const headings = container ? container.querySelectorAll('h2, h3, h4') : [];

  if (!headings || headings.length === 0) {
    outlineList.innerHTML = `<li class="outline-empty">No headings found</li>`;
    return;
  }

  let html = '';
  headings.forEach((heading, idx) => {
    const id = `heading-${idx}`;
    heading.setAttribute('id', id);

    const level = heading.tagName.toLowerCase();
    const depth = level === 'h2' ? 2 : level === 'h3' ? 3 : 4;
    const text = heading.textContent.replace(/^[#\s]+/, '').trim();

    html += `
      <li class="outline-item depth-${depth}">
        <a href="#${id}" class="outline-link" data-target="${id}" title="${text}">
          ${text}
        </a>
      </li>
    `;
  });

  outlineList.innerHTML = html;

  outlineList.querySelectorAll('.outline-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('data-target');
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

function initOutlineScrollspy() {
  const mainContent = document.getElementById('main-content');
  if (!mainContent) return;

  mainContent.addEventListener('scroll', () => {
    updateReadingProgress();
    updateActiveOutlineItem();
  });

  document.getElementById('btn-scroll-top')?.addEventListener('click', () => {
    mainContent.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

function updateReadingProgress() {
  const mainContent = document.getElementById('main-content');
  const progressBar = document.getElementById('reading-progress-bar');
  if (!mainContent || !progressBar) return;

  const scrollTop = mainContent.scrollTop;
  const scrollHeight = mainContent.scrollHeight - mainContent.clientHeight;
  const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;

  progressBar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
}

function updateActiveOutlineItem() {
  const headings = document.querySelectorAll('.markdown-body h2, .markdown-body h3, .markdown-body h4');
  const outlineLinks = document.querySelectorAll('.outline-link');
  if (headings.length === 0 || outlineLinks.length === 0) return;

  let currentHeadingId = null;
  const scrollOffset = 140;

  headings.forEach(heading => {
    const rect = heading.getBoundingClientRect();
    if (rect.top <= scrollOffset) {
      currentHeadingId = heading.getAttribute('id');
    }
  });

  if (!currentHeadingId && headings.length > 0) {
    currentHeadingId = headings[0].getAttribute('id');
  }

  outlineLinks.forEach(link => {
    if (link.getAttribute('data-target') === currentHeadingId) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
}

/* ==========================================
   BACKLINKS & FOOTER NAVIGATION
   ========================================== */

function renderBacklinks(backlinks) {
  const section = document.getElementById('backlinks-section');
  const grid = document.getElementById('backlinks-grid');
  const count = document.getElementById('backlinks-count');
  if (!section || !grid) return;

  if (!backlinks || backlinks.length === 0) {
    section.style.display = 'none';
    return;
  }

  section.style.display = 'block';
  if (count) count.textContent = backlinks.length;

  grid.innerHTML = backlinks.map(b => `
    <a href="#/${b.sourcePath}" class="backlink-card">
      <span class="backlink-title">${b.sourceTitle || b.sourcePath}</span>
      <span class="backlink-snippet">Referenced as: "${b.linkText}"</span>
    </a>
  `).join('');
}

function renderDocNavFooter(currentPath) {
  const footer = document.getElementById('doc-nav-footer');
  if (!footer) return;
  const currentIndex = state.allDocPaths.indexOf(currentPath);

  if (currentIndex === -1 || state.allDocPaths.length <= 1) {
    footer.innerHTML = '';
    return;
  }

  const prevPath = currentIndex > 0 ? state.allDocPaths[currentIndex - 1] : null;
  const nextPath = currentIndex < state.allDocPaths.length - 1 ? state.allDocPaths[currentIndex + 1] : null;

  let html = '';
  if (prevPath) {
    html += `
      <a href="#/${prevPath}" class="nav-card prev">
        <span class="nav-direction">← Previous</span>
        <span class="nav-title">${state.allDocTitles[prevPath] || prevPath}</span>
      </a>
    `;
  } else {
    html += `<div></div>`;
  }

  if (nextPath) {
    html += `
      <a href="#/${nextPath}" class="nav-card next">
        <span class="nav-direction">Next →</span>
        <span class="nav-title">${state.allDocTitles[nextPath] || nextPath}</span>
      </a>
    `;
  }

  footer.innerHTML = html;
}

/* ==========================================
   SIDEBAR INTERACTIONS & VIEW MODES
   ========================================== */

function initSidebar() {
  const viewModeButtons = document.querySelectorAll('.view-mode-tab');
  viewModeButtons.forEach(btn => {
    if (btn.getAttribute('data-mode') === state.viewMode) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }

    btn.addEventListener('click', () => {
      viewModeButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.viewMode = btn.getAttribute('data-mode');
      localStorage.setItem('wiki_view_mode', state.viewMode);

      const catFilters = document.getElementById('category-filters');
      if (catFilters) {
        catFilters.style.display = state.viewMode === 'category' ? 'flex' : 'none';
      }

      renderTree();
    });
  });

  const catFilters = document.getElementById('category-filters');
  if (catFilters) {
    catFilters.style.display = state.viewMode === 'category' ? 'flex' : 'none';
  }

  const filterButtons = document.querySelectorAll('.filter-chip');
  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      filterButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.activeFilter = btn.getAttribute('data-filter');
      renderTree();
    });
  });

  const filterInput = document.getElementById('tree-filter-input');
  const clearFilterBtn = document.getElementById('tree-clear-filter');

  filterInput?.addEventListener('input', (e) => {
    const val = e.target.value;
    if (clearFilterBtn) clearFilterBtn.style.display = val ? 'block' : 'none';
    renderTree();
  });

  clearFilterBtn?.addEventListener('click', () => {
    if (filterInput) filterInput.value = '';
    clearFilterBtn.style.display = 'none';
    renderTree();
  });

  document.getElementById('btn-toggle-sidebar')?.addEventListener('click', () => {
    document.getElementById('app-layout').classList.toggle('sidebar-collapsed');
  });
}

/* ==========================================
   LOG NEW RESEARCH MODAL
   ========================================== */

function initLogResearchModal() {
  const modal = document.getElementById('log-modal');
  const openBtn = document.getElementById('btn-open-log-modal');
  const closeBtn = document.getElementById('btn-close-log-modal');
  const cancelBtn = document.getElementById('btn-cancel-log');
  const form = document.getElementById('log-research-form');
  const dateInput = document.getElementById('log-date');

  function openLogModal() {
    if (modal) modal.style.display = 'flex';
    if (dateInput && !dateInput.value) {
      dateInput.value = '2026-08-15';
    }
    document.getElementById('log-title')?.focus();
  }

  function closeLogModal() {
    if (modal) modal.style.display = 'none';
  }

  openBtn?.addEventListener('click', openLogModal);
  closeBtn?.addEventListener('click', closeLogModal);
  cancelBtn?.addEventListener('click', closeLogModal);

  modal?.addEventListener('click', (e) => {
    if (e.target === modal) closeLogModal();
  });

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById('btn-submit-log');
    if (submitBtn) submitBtn.disabled = true;

    const payload = {
      date: document.getElementById('log-date').value || '2026-08-15',
      type: document.getElementById('log-type').value || 'paper',
      title: document.getElementById('log-title').value.trim(),
      authors: document.getElementById('log-authors').value.trim(),
      source: document.getElementById('log-source').value.trim(),
      tags: document.getElementById('log-tags').value.trim(),
      quality: parseInt(document.getElementById('log-quality').value || '5', 10),
      summary: document.getElementById('log-summary').value.trim(),
      content: document.getElementById('log-content').value.trim()
    };

    try {
      const res = await fetch('/api/new-research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed saving research');

      showToast(`✅ Research logged for ${payload.date}!`);
      closeLogModal();
      form.reset();

      await loadTree();
      window.location.hash = `#/${data.path}`;
    } catch (err) {
      alert(`Error logging research: ${err.message}`);
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  });
}

/* ==========================================
   COMMAND PALETTE SEARCH MODAL (⌘K)
   ========================================== */

function initSearchModal() {
  const modal = document.getElementById('search-modal');
  const trigger = document.getElementById('search-trigger');
  const input = document.getElementById('modal-search-input');
  const closeBtn = document.getElementById('btn-close-search');
  const resultsContainer = document.getElementById('search-modal-results');

  function openSearch() {
    if (!modal || !input) return;
    modal.style.display = 'flex';
    input.value = '';
    input.focus();
    resultsContainer.innerHTML = `<div class="search-hint">Type keywords to search across all wiki files...</div>`;
  }

  function closeSearch() {
    if (modal) modal.style.display = 'none';
  }

  trigger?.addEventListener('click', openSearch);
  closeBtn?.addEventListener('click', closeSearch);

  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (modal && modal.style.display === 'flex') closeSearch();
      else openSearch();
    } else if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
      e.preventDefault();
      openSearch();
    } else if (e.key === 'Escape') {
      if (modal && modal.style.display === 'flex') closeSearch();
      const logModal = document.getElementById('log-modal');
      if (logModal && logModal.style.display === 'flex') logModal.style.display = 'none';
      const graphModal = document.getElementById('graph-modal');
      if (graphModal && graphModal.style.display === 'flex') graphModal.style.display = 'none';
    }
  });

  modal?.addEventListener('click', (e) => {
    if (e.target === modal) closeSearch();
  });

  let searchDebounceTimer = null;
  input?.addEventListener('input', (e) => {
    clearTimeout(searchDebounceTimer);
    const query = e.target.value.trim();
    if (!query) {
      resultsContainer.innerHTML = `<div class="search-hint">Type keywords to search across all wiki files...</div>`;
      return;
    }

    searchDebounceTimer = setTimeout(async () => {
      try {
        resultsContainer.innerHTML = `<div class="search-hint"><div class="spinner"></div> Searching...</div>`;
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        renderSearchResults(data.results || [], query);
      } catch (err) {
        resultsContainer.innerHTML = `<div class="search-hint" style="color: var(--accent-rose);">Search failed</div>`;
      }
    }, 150);
  });

  input?.addEventListener('keydown', (e) => {
    const items = resultsContainer.querySelectorAll('.search-result-item');
    if (items.length === 0) return;

    let selectedIdx = Array.from(items).findIndex(it => it.classList.contains('selected'));

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (selectedIdx === -1 || selectedIdx >= items.length - 1) selectedIdx = 0;
      else selectedIdx++;
      highlightSearchItem(items, selectedIdx);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (selectedIdx <= 0) selectedIdx = items.length - 1;
      else selectedIdx--;
      highlightSearchItem(items, selectedIdx);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIdx >= 0 && items[selectedIdx]) {
        items[selectedIdx].click();
      }
    }
  });

  function highlightSearchItem(items, index) {
    items.forEach(it => it.classList.remove('selected'));
    if (items[index]) {
      items[index].classList.add('selected');
      items[index].scrollIntoView({ block: 'nearest' });
    }
  }

  function renderSearchResults(results, query) {
    if (results.length === 0) {
      resultsContainer.innerHTML = `<div class="search-hint">No results found for "${query}"</div>`;
      return;
    }

    let html = '';
    results.forEach((r, idx) => {
      const doc = r.document;
      const snippet = r.snippets.length > 0 ? r.snippets[0] : '';
      const selectedClass = idx === 0 ? 'selected' : '';

      html += `
        <div class="search-result-item ${selectedClass}" data-path="${doc.path}">
          <div class="search-result-top">
            <span class="tree-item-badge paper">${doc.category}</span>
            <span class="search-result-title">${doc.title}</span>
            <span class="search-result-path">${doc.path}</span>
          </div>
          ${snippet ? `<div class="search-result-snippet">${escapeHtml(snippet)}</div>` : ''}
        </div>
      `;
    });

    resultsContainer.innerHTML = html;

    resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
      item.addEventListener('click', () => {
        const path = item.getAttribute('data-path');
        window.location.hash = `#/${path}`;
        closeSearch();
      });
    });
  }
}

/* ==========================================
   INTERACTIVE KNOWLEDGE GRAPH MODAL
   ========================================== */

function initGraphModal() {
  const modal = document.getElementById('graph-modal');
  const trigger = document.getElementById('btn-graph-view');
  const closeBtn = document.getElementById('btn-close-graph');
  const resetBtn = document.getElementById('btn-reset-graph');
  const canvas = document.getElementById('graph-canvas');
  const tooltip = document.getElementById('graph-tooltip');

  if (!modal || !canvas) return;

  const ctx = canvas.getContext('2d');
  let simulationRunning = false;
  let nodes = [];
  let edges = [];
  let transform = { x: 0, y: 0, scale: 1 };
  let isDragging = false;
  let dragNode = null;
  let startX, startY;

  async function openGraph() {
    modal.style.display = 'flex';
    resizeCanvas();
    await loadGraphData();
    startSimulation();
  }

  function closeGraph() {
    modal.style.display = 'none';
    simulationRunning = false;
  }

  trigger?.addEventListener('click', openGraph);
  closeBtn?.addEventListener('click', closeGraph);
  resetBtn?.addEventListener('click', resetGraphView);

  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'g') {
      e.preventDefault();
      if (modal.style.display === 'flex') closeGraph();
      else openGraph();
    }
  });

  function resizeCanvas() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }

  function resetGraphView() {
    transform = { x: canvas.width / (2 * window.devicePixelRatio), y: canvas.height / (2 * window.devicePixelRatio), scale: 0.85 };
  }

  async function loadGraphData() {
    try {
      const res = await fetch('/api/graph');
      const data = await res.json();
      state.graphData = data;

      const width = canvas.width / window.devicePixelRatio;
      const height = canvas.height / window.devicePixelRatio;

      nodes = data.nodes.map((n, i) => {
        const angle = (i / data.nodes.length) * 2 * Math.PI;
        const radius = Math.min(width, height) * 0.35;
        return {
          ...n,
          x: Math.cos(angle) * radius,
          y: Math.sin(angle) * radius,
          vx: 0,
          vy: 0,
          radius: n.category === 'Hub & Index' ? 14 : n.category === 'Playbooks & Output' ? 11 : 8
        };
      });

      const nodeMap = new Map(nodes.map(n => [n.id, n]));
      edges = data.edges
        .map(e => ({ source: nodeMap.get(e.source), target: nodeMap.get(e.target), label: e.label }))
        .filter(e => e.source && e.target);

      resetGraphView();
    } catch (e) {
      console.error('Error loading graph:', e);
    }
  }

  function startSimulation() {
    simulationRunning = true;
    let iteration = 0;

    function step() {
      if (!simulationRunning) return;

      if (iteration < 300) {
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const dx = nodes[j].x - nodes[i].x;
            const dy = nodes[j].y - nodes[i].y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            if (dist < 280) {
              const force = (280 - dist) / dist * 0.05;
              nodes[i].vx -= dx * force;
              nodes[i].vy -= dy * force;
              nodes[j].vx += dx * force;
              nodes[j].vy += dy * force;
            }
          }
        }

        for (const edge of edges) {
          const dx = edge.target.x - edge.source.x;
          const dy = edge.target.y - edge.source.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (dist - 120) * 0.01;
          edge.source.vx += (dx / dist) * force;
          edge.source.vy += (dy / dist) * force;
          edge.target.vx -= (dx / dist) * force;
          edge.target.vy -= (dy / dist) * force;
        }

        for (const node of nodes) {
          if (node !== dragNode) {
            node.x += node.vx;
            node.y += node.vy;
            node.vx *= 0.85;
            node.vy *= 0.85;
          }
        }
        iteration++;
      }

      drawGraph();
      requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
  }

  function drawGraph() {
    const width = canvas.width / window.devicePixelRatio;
    const height = canvas.height / window.devicePixelRatio;

    ctx.clearRect(0, 0, width, height);
    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.scale, transform.scale);

    const isDark = state.theme === 'dark';

    for (const edge of edges) {
      ctx.beginPath();
      ctx.moveTo(edge.source.x, edge.source.y);
      ctx.lineTo(edge.target.x, edge.target.y);
      ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.1)';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    for (const node of nodes) {
      const isCurrent = node.id === state.currentPath;

      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius + (isCurrent ? 3 : 0), 0, 2 * Math.PI);

      if (node.category === 'Hub & Index') ctx.fillStyle = isDark ? '#10b981' : '#059669';
      else if (node.category === 'Playbooks & Output') ctx.fillStyle = isDark ? '#8b5cf6' : '#7c3aed';
      else if (node.category === 'Raw Papers') ctx.fillStyle = isDark ? '#3b82f6' : '#2563eb';
      else ctx.fillStyle = isDark ? '#ec4899' : '#db2777';

      ctx.fill();

      if (isCurrent) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2.5;
        ctx.stroke();
      }

      ctx.font = '10.5px Plus Jakarta Sans, sans-serif';
      ctx.fillStyle = isDark ? '#cbd5e1' : '#334155';
      ctx.textAlign = 'center';
      ctx.fillText(node.title.length > 20 ? node.title.substring(0, 18) + '…' : node.title, node.x, node.y + node.radius + 13);
    }

    ctx.restore();
  }

  canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left - transform.x) / transform.scale;
    const my = (e.clientY - rect.top - transform.y) / transform.scale;

    for (const node of nodes) {
      const dx = node.x - mx;
      const dy = node.y - my;
      if (Math.sqrt(dx * dx + dy * dy) <= node.radius + 4) {
        dragNode = node;
        break;
      }
    }

    isDragging = true;
    startX = e.clientX - transform.x;
    startY = e.clientY - transform.y;
  });

  window.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    if (isDragging) {
      if (dragNode) {
        dragNode.x = (e.clientX - rect.left - transform.x) / transform.scale;
        dragNode.y = (e.clientY - rect.top - transform.y) / transform.scale;
      } else {
        transform.x = e.clientX - startX;
        transform.y = e.clientY - startY;
      }
      drawGraph();
    } else {
      const mx = (e.clientX - rect.left - transform.x) / transform.scale;
      const my = (e.clientY - rect.top - transform.y) / transform.scale;
      let hoveredNode = null;

      for (const node of nodes) {
        const dx = node.x - mx;
        const dy = node.y - my;
        if (Math.sqrt(dx * dx + dy * dy) <= node.radius + 4) {
          hoveredNode = node;
          break;
        }
      }

      if (hoveredNode) {
        tooltip.style.display = 'block';
        tooltip.style.left = `${e.clientX - rect.left + 12}px`;
        tooltip.style.top = `${e.clientY - rect.top + 12}px`;
        tooltip.innerHTML = `<strong>${hoveredNode.title}</strong><br><span style="color: var(--text-subtle);">${hoveredNode.category}</span>`;
      } else {
        tooltip.style.display = 'none';
      }
    }
  });

  window.addEventListener('mouseup', (e) => {
    if (dragNode) {
      const rect = canvas.getBoundingClientRect();
      const mx = (e.clientX - rect.left - transform.x) / transform.scale;
      const my = (e.clientY - rect.top - transform.y) / transform.scale;
      const dx = dragNode.x - mx;
      const dy = dragNode.y - my;
      if (Math.sqrt(dx * dx + dy * dy) < 4) {
        window.location.hash = `#/${dragNode.id}`;
        closeGraph();
      }
    }
    isDragging = false;
    dragNode = null;
  });

  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    transform.scale = Math.min(3.0, Math.max(0.3, transform.scale * zoomFactor));
    drawGraph();
  });
}

/* ==========================================
   LIVE SSE AUTO-SYNC
   ========================================== */

function initLiveSync() {
  if (!window.EventSource) return;

  const eventSource = new EventSource('/api/events');

  eventSource.addEventListener('change', async (e) => {
    showToast('🔄 Wiki updated live');
    await loadTree();
    if (state.currentPath) {
      await loadDocument(state.currentPath);
    }
  });

  eventSource.onerror = () => {
    console.warn('[LiveSync] EventSource reconnecting...');
  };
}

/* ==========================================
   TOPBAR ACTIONS & UTILITIES
   ========================================== */

function initTopbarActions() {
  const rawBtn = document.getElementById('btn-view-raw');
  const markdownBody = document.getElementById('markdown-body');
  const rawBody = document.getElementById('raw-markdown-body');

  rawBtn?.addEventListener('click', () => {
    state.isRawView = !state.isRawView;
    if (state.isRawView) {
      if (markdownBody) markdownBody.style.display = 'none';
      if (rawBody) rawBody.style.display = 'block';
      rawBtn.classList.add('active');
    } else {
      if (markdownBody) markdownBody.style.display = 'block';
      if (rawBody) rawBody.style.display = 'none';
      rawBtn.classList.remove('active');
    }
  });

  document.getElementById('btn-copy-md')?.addEventListener('click', () => {
    if (state.currentDoc?.content) {
      navigator.clipboard.writeText(state.currentDoc.content).then(() => {
        showToast('📋 Markdown copied to clipboard!');
      });
    }
  });

  document.getElementById('btn-print')?.addEventListener('click', () => {
    window.print();
  });

  document.getElementById('btn-zen-mode')?.addEventListener('click', () => {
    const layout = document.getElementById('app-layout');
    if (layout) {
      layout.classList.toggle('sidebar-collapsed');
      layout.classList.toggle('outline-collapsed');
    }
  });
}

function showToast(message) {
  const toast = document.getElementById('toast');
  const msg = document.getElementById('toast-msg');
  if (!toast || !msg) return;

  msg.textContent = message;
  toast.style.display = 'block';

  setTimeout(() => {
    toast.style.display = 'none';
  }, 2400);
}

function escapeHtml(str) {
  return str.replace(/[&<>"']/g, m => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[m]);
}
