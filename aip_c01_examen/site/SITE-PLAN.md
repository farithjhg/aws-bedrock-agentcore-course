# SITE-PLAN.md — Docusaurus v3 migration of the AIP-C01 exam-prep course

Implementation plan for converting the existing Markdown course under `aip_c01_examen/`
into a Docusaurus v3 docs-only site, published at
`https://farithjhg.github.io/aws-bedrock-agentcore-course/aip_c01_examen/`.

This is **Option B**: everything else in the repo (the AgentCore course under
`intro_4h_agentcore/`, `v7_aprender_haciendo/`, the repo-root `index.html`) stays
untouched. Only the exam course becomes a Docusaurus site served at its own subpath.

The implementer should follow the numbered steps in the last section in order. The
sections before it record the decisions that drive those steps so nothing has to be
re-decided during implementation.

---

## 0. Confirmed environment and repo facts (verified during exploration)

- **Workspace root:** `c:\data-dev\personal\aws-bedrock-agentcore-course`
- **OS/shell:** Windows, bash. Node v24, npm v11 already installed.
- **Git remote:** `git@github.com:farithjhg/aws-bedrock-agentcore-course.git`, default branch `main`.
- **Pages model (read from `.github/workflows/pages.yml`):** on push to `main` or
  `workflow_dispatch`, the workflow runs `actions/checkout@v5` →
  `actions/configure-pages@v5` → `actions/upload-pages-artifact@v4` **with `path: .`**
  (uploads the whole repo as static files) → `actions/deploy-pages@v4`.
  `permissions: contents: read, pages: write, id-token: write`.
  `concurrency: group: pages, cancel-in-progress: false`. There is **no** Node setup
  and **no** build step today.
- **`.nojekyll`** exists at repo root (0 bytes) → GitHub Pages does not run Jekyll, so
  directories/files beginning with `_` (e.g. Docusaurus's `_` partials) are served fine.
- **Repo-root `.gitignore`** currently ignores only harness runtime state, Claude local
  settings, and `.venv/`. No `node_modules` entry yet.
- **Repo-root `index.html`** is a meta-refresh redirect to `v7_aprender_haciendo/` — do
  not touch it.
- **Docusaurus version to use:** latest stable **v3** (`@docusaurus/core` and
  `@docusaurus/preset-classic` `^3.8.0`; 3.10.x is current). v3 supports Node 20+ and
  React 18/19. (Confirmed via the Docusaurus release pages and npm; content rephrased for
  compliance with licensing restrictions.)

### Sibling top-level dirs that MUST stay untouched

- `intro_4h_agentcore/` — the companion AgentCore course (also served via Pages).
- `v7_aprender_haciendo/` — the Nova Assist course (root `index.html` redirects here).
- repo-root `index.html`, `.nojekyll`, `.gitattributes`, `CLAUDE.md`, `.github/`,
  `.kiro/`, `.claude/`, `.agents/`, `.venv/`.

The only files this task changes outside `aip_c01_examen/` are
`.github/workflows/pages.yml` and the repo-root `.gitignore` (see steps 10–11).

---

## 1. Decision: outDir mechanism (how built assets reach the subpath)

### Chosen mechanism

**Set Docusaurus `outDir` to `../` (i.e. `aip_c01_examen/`) so `npm run build` writes the
compiled static site directly into `aip_c01_examen/`, overwriting the old `index.html`
there. The Docusaurus source project lives in `aip_c01_examen/site/` and is never served.**

Concretely, in `docusaurus.config.ts`:

```ts
// aip_c01_examen/site/docusaurus.config.ts
const config: Config = {
  // ...
  outDir: '../', // build output lands in aip_c01_examen/ (the published subpath)
  baseUrl: '/aws-bedrock-agentcore-course/aip_c01_examen/',
  url: 'https://farithjhg.github.io',
  // ...
};
```

Because `baseUrl` is `/aws-bedrock-agentcore-course/aip_c01_examen/`, every asset
Docusaurus emits is already prefixed correctly for the subpath. Writing those files into
`aip_c01_examen/` means the published tree at
`farithjhg.github.io/aws-bedrock-agentcore-course/aip_c01_examen/` serves the built site
verbatim, with zero post-build copying.

### Why this option over the alternatives

- The existing workflow uploads the **whole repo** (`path: .`). Whatever physically sits
  at `aip_c01_examen/` is what gets published at that subpath. The simplest robust way to
  put the right bytes there is to have the build write them there directly.
- The alternative (build into `aip_c01_examen/site/build` and assemble the tree in CI with
  a copy step) adds a moving part — a copy/rsync in the workflow that must stay in sync
  with the `outDir` — for no benefit on the `path: .` model. `outDir: '../'` removes that
  step entirely.
- **Critical constraint honored:** the Docusaurus *source* (`node_modules/`, `src/`,
  `docusaurus.config.ts`, `package.json`, `sidebars.ts`, `.docusaurus/` cache) all live
  under `aip_c01_examen/site/`, which is a **subdirectory** of the output dir. We must
  ensure the source is never served and never committed:
  - `aip_c01_examen/site/node_modules/`, `aip_c01_examen/site/.docusaurus/`, and
    `aip_c01_examen/site/build/` are gitignored (step 11).
  - The build is run in CI (step 10) so the source files, while physically nested under
    the published dir, are irrelevant: Pages serves `aip_c01_examen/index.html` and the
    `assets/`, `img/`, doc HTML, etc. that Docusaurus emitted. The `site/` subfolder being
    present is harmless — nothing links to it and it is not an index. (If desired, the
    build step can additionally confirm `site/node_modules` is absent on the runner before
    build; not required.)

> **Note for the implementer:** `outDir: '../'` makes Docusaurus clean and write the parent
> dir on every build. Docusaurus's `build` removes the existing `outDir` contents first.
> This is intended — it replaces the old hand-written `aip_c01_examen/index.html` with the
> generated home page. The `site/` subdirectory itself is **not** deleted by the build
> (Docusaurus clears files it manages, not an unrelated nested project dir), but to be safe
> the source lives in `site/` precisely so the only thing at `aip_c01_examen/` root that
> matters is generated output. Verify after the first local build that
> `aip_c01_examen/index.html` is the generated Docusaurus page and that
> `aip_c01_examen/site/` still contains the source.

### trailingSlash decision

**Set `trailingSlash: false`.**

Reasoning: GitHub Pages serves `foo/index.html` for both `/foo` and `/foo/` requests, but
to keep generated internal links and the sitemap consistent on a project subpath, an
explicit value avoids the "sometimes 404 on refresh" ambiguity that the default
(`undefined`) can cause on some static hosts. `false` makes Docusaurus emit links without
trailing slashes and still writes `index.html` files, which GitHub Pages resolves
correctly. The implementer must **verify** this choice by loading a deep doc URL and
refreshing it (step 9) — if any deep link 404s on refresh on Pages, switch to
`trailingSlash: true` and rebuild. Document whichever value ends up verified.

---

## 2. Docs-only mode, docs tree, and frontmatter plan

### Mode

Use **docs-only mode** (no blog, no separate landing page component). In
`preset-classic`, set `docs.routeBasePath: '/'` and `blog: false`. The README becomes the
site home at the subpath root (`slug: /`).

### Source → docs mapping

All content files move from their current locations into
`aip_c01_examen/site/docs/`. The site `docs/` tree is **flattened/recategorized** into
four category folders that mirror the course. The original files under
`aip_c01_examen/*.md`, `aip_c01_examen/blueprint/`, `aip_c01_examen/tablas-decision/`, and
`aip_c01_examen/practica/` are the **content source**; the implementer copies their body
into the new docs files and adds frontmatter + rewritten links (section 3). (Do **not**
leave the old `.md` files in place at the published subpath — after the build, only the
generated HTML should be at `aip_c01_examen/`. The old `.md` originals can stay in the repo
under `aip_c01_examen/` for history since they are not linked by the site, but they will be
overwritten/ignored by the build at the root level only if they collide; they do not, so
leaving them is optional. Recommended: keep originals as the editable source of truth and
treat `site/docs/*` as the published copies. See step 3 note.)

> **Design note (kept brief):** rather than auto-importing the originals, we author the
> `docs/` copies explicitly so frontmatter and link rewrites are deterministic and
> `onBrokenLinks: throw` passes. This is one-time copy work, acceptable for 15 files.

### The exact `docs/` tree, with frontmatter per file

Sidebar categories and positions (sidebar is **autogenerated** from folder structure +
`sidebar_position`; see section 4 for the `sidebars.ts` choice). `_category_.json` files
set category labels and order.

```
aip_c01_examen/site/docs/
├── intro.md                         (from README.md)        slug: /        sidebar_position: 1
├── plan-estrategico.md              (from PLAN-ESTRATEGICO.md)              sidebar_position: 2
├── recursos.md                      (from recursos.md)                     sidebar_position: 3
├── blueprint/
│   ├── _category_.json              label "Blueprint", position 2
│   ├── vision-examen.md             (from blueprint/00-vision-examen.md)   sidebar_position: 1
│   ├── dominio-1-fundacion-datos.md (from blueprint/dominio-1-...)         sidebar_position: 2
│   ├── dominio-2-implementacion.md  (from blueprint/dominio-2-...)         sidebar_position: 3
│   ├── dominio-3-seguridad.md       (from blueprint/dominio-3-...)         sidebar_position: 4
│   ├── dominio-4-optimizacion.md    (from blueprint/dominio-4-...)         sidebar_position: 5
│   └── dominio-5-testing.md         (from blueprint/dominio-5-...)         sidebar_position: 6
├── tablas-decision/
│   ├── _category_.json              label "Decision tables", position 3
│   ├── decision-por-restriccion.md  (from tablas-decision/decision-por-restriccion.md)  sidebar_position: 1  ← MASTER, FIRST
│   ├── decision-vector-stores.md    (from tablas-decision/decision-vector-stores.md)    sidebar_position: 2
│   └── decision-despliegue.md       (from tablas-decision/decision-despliegue.md)       sidebar_position: 3
└── practica/
    ├── _category_.json              label "Practice", position 4
    ├── banco-preguntas.md           (from practica/banco-preguntas.md)     sidebar_position: 1
    ├── labs-hands-on.md             (from practica/labs-hands-on.md)       sidebar_position: 2
    └── simulacro-final.md           (from practica/simulacro-final.md)     sidebar_position: 3
```

Top-level Overview items (`intro`, `plan-estrategico`, `recursos`) sit at the docs root
with positions 1–3; the three category folders follow via their `_category_.json`
`position` values (2, 3, 4). Note: top-level docs and the categories share the same
numeric space in an autogenerated sidebar; using doc `sidebar_position` 1–3 for the three
Overview files and category `position` 2–4 means the categories interleave after the
loose docs. To make Overview a clean group, the implementer may instead wrap the three
loose docs in an `docs/` root with a manual sidebar — but the simpler autogenerated
approach is acceptable; **chosen: autogenerated sidebar** (section 4). Verify order in the
rendered sidebar (step 9); if interleaving looks wrong, bump the category positions to
10/20/30 and keep Overview docs at 1/2/3.

### Per-file frontmatter (id, slug, sidebar_position, title)

| docs path | id | slug | sidebar_position | title (human) |
|---|---|---|---|---|
| `docs/intro.md` | `intro` | `/` | 1 | AIP-C01 Exam-Prep Course |
| `docs/plan-estrategico.md` | `plan-estrategico` | (default `/plan-estrategico`) | 2 | 8-Week Strategy Plan |
| `docs/recursos.md` | `recursos` | (default `/recursos`) | 3 | Resources |
| `docs/blueprint/vision-examen.md` | `blueprint/vision-examen` | (default) | 1 | Exam Format & Strategy |
| `docs/blueprint/dominio-1-fundacion-datos.md` | `blueprint/dominio-1-fundacion-datos` | (default) | 2 | Domain 1 — Foundation, Data & Compliance (31%) |
| `docs/blueprint/dominio-2-implementacion.md` | `blueprint/dominio-2-implementacion` | (default) | 3 | Domain 2 — Implementation & Integration (26%) |
| `docs/blueprint/dominio-3-seguridad.md` | `blueprint/dominio-3-seguridad` | (default) | 4 | Domain 3 — AI Safety, Security & Governance (20%) |
| `docs/blueprint/dominio-4-optimizacion.md` | `blueprint/dominio-4-optimizacion` | (default) | 5 | Domain 4 — Operational Efficiency & Optimization (12%) |
| `docs/blueprint/dominio-5-testing.md` | `blueprint/dominio-5-testing` | (default) | 6 | Domain 5 — Testing, Validation & Troubleshooting (11%) |
| `docs/tablas-decision/decision-por-restriccion.md` | `tablas-decision/decision-por-restriccion` | (default) | 1 | Master Decision Table |
| `docs/tablas-decision/decision-vector-stores.md` | `tablas-decision/decision-vector-stores` | (default) | 2 | Vector & Search Stores |
| `docs/tablas-decision/decision-despliegue.md` | `tablas-decision/decision-despliegue` | (default) | 3 | Deployment & Inference Modes |
| `docs/practica/banco-preguntas.md` | `practica/banco-preguntas` | (default) | 1 | Practice Question Bank |
| `docs/practica/labs-hands-on.md` | `practica/labs-hands-on` | (default) | 2 | Optional Hands-On Labs |
| `docs/practica/simulacro-final.md` | `practica/simulacro-final` | (default) | 3 | Final Mock & Readiness Gate |

Frontmatter block to add at the top of each file, example for the home page:

```md
---
id: intro
slug: /
sidebar_position: 1
title: AIP-C01 Exam-Prep Course
---
```

> **Important:** each source file already starts with an H1 (`# ...`). When a `title:` is
> set in frontmatter, keep the H1 **or** remove it to avoid a duplicate visible title.
> Decision: **remove the leading H1** from each doc body and rely on the frontmatter
> `title`, so the page shows one title. (Docusaurus renders the frontmatter title as the
> page heading.) Alternatively keep the H1 and omit `title:` — but since we need stable
> `id`/`slug`, we set frontmatter and drop the H1.

`_category_.json` example (`docs/blueprint/_category_.json`):

```json
{ "label": "Blueprint", "position": 2, "collapsible": true, "collapsed": false }
```

With `decision-por-restriccion.md` at `sidebar_position: 1` it renders **first** in the
Decision tables category, as required (it is the master table).

---

## 3. Full link-rewrite map

Every relative Markdown cross-link in the source must become a Docusaurus doc link that
resolves under `routeBasePath: '/'`. Docusaurus resolves doc-to-doc links written as
relative `.md` paths against the current file, and (with the flattened tree) the cleanest
approach is to use **root-absolute doc links** of the form `/blueprint/vision-examen` etc.,
OR relative `./` / `../` `.md` links that match the new tree. Since the new tree largely
mirrors the old folder names, **relative `.md` links mostly keep working after renaming
`00-vision-examen.md` → `vision-examen.md` and `README.md` → the home slug**.

Decision: **use root-absolute links without the `.md` extension** for every cross-link
(e.g. `/blueprint/dominio-1-fundacion-datos`). This is unambiguous regardless of the source
file's folder depth, and makes `onBrokenLinks: throw` deterministic. The home page is
linked as `/`.

### Canonical target for each source doc (what every link to it becomes)

| Old link target (any form) | New Docusaurus link |
|---|---|
| `README.md`, `../README.md`, "course home" | `/` |
| `PLAN-ESTRATEGICO.md`, `../PLAN-ESTRATEGICO.md` | `/plan-estrategico` |
| `recursos.md`, `../recursos.md` | `/recursos` |
| `blueprint/00-vision-examen.md`, `./00-vision-examen.md`, `../blueprint/00-vision-examen.md` | `/blueprint/vision-examen` |
| `blueprint/dominio-1-fundacion-datos.md` (and `./`, `../blueprint/` forms) | `/blueprint/dominio-1-fundacion-datos` |
| `blueprint/dominio-2-implementacion.md` | `/blueprint/dominio-2-implementacion` |
| `blueprint/dominio-3-seguridad.md` | `/blueprint/dominio-3-seguridad` |
| `blueprint/dominio-4-optimizacion.md` | `/blueprint/dominio-4-optimizacion` |
| `blueprint/dominio-5-testing.md` | `/blueprint/dominio-5-testing` |
| `tablas-decision/decision-por-restriccion.md`, `./decision-por-restriccion.md`, `../tablas-decision/...` | `/tablas-decision/decision-por-restriccion` |
| `tablas-decision/decision-vector-stores.md` | `/tablas-decision/decision-vector-stores` |
| `tablas-decision/decision-despliegue.md` | `/tablas-decision/decision-despliegue` |
| `practica/banco-preguntas.md`, `./banco-preguntas.md`, `../practica/...` | `/practica/banco-preguntas` |
| `practica/labs-hands-on.md` | `/practica/labs-hands-on` |
| `practica/simulacro-final.md`, `./simulacro-final.md` | `/practica/simulacro-final` |

Apply this table to **every** cross-link found. The per-file link inventory below lists
exactly where they occur so none are missed.

### Per-file link inventory (links that must be rewritten)

- **README.md → intro.md:** links to PLAN-ESTRATEGICO, all 5 blueprint domains +
  00-vision-examen, all 3 decision tables (incl. `tablas-decision/` dir link →
  `/tablas-decision/decision-por-restriccion`), all 3 practica files, recursos.
- **PLAN-ESTRATEGICO.md → plan-estrategico.md:** links to README (`/`), 00-vision-examen,
  all 5 dominios, both specialized decision tables, master table, banco-preguntas,
  simulacro-final, labs-hands-on, **and one outbound link** `../intro_4h_agentcore/README.md`
  (see outbound rule below).
- **recursos.md → recursos.md:** links to README (`/`), 00-vision-examen, labs-hands-on,
  banco-preguntas, simulacro-final, **and outbound** `` `../intro_4h_agentcore/README.md` ``.
- **blueprint/00-vision-examen.md → vision-examen.md:** `../README.md` → `/`,
  `./dominio-1-fundacion-datos.md` → `/blueprint/dominio-1-fundacion-datos`,
  `../tablas-decision/decision-por-restriccion.md`, `../practica/banco-preguntas.md`.
- **blueprint/dominio-1..5.md:** each links `../README.md` → `/`, sibling
  `./00-vision-examen.md` → `/blueprint/vision-examen`, sibling dominios, several
  `../tablas-decision/*` and `../practica/*`. Domain 2 additionally has outbound reuse
  links (see below).
- **tablas-decision/decision-por-restriccion.md, decision-vector-stores.md,
  decision-despliegue.md:** each links `../README.md` → `/`, `../blueprint/*`, sibling
  tables, `../practica/banco-preguntas.md`.
- **practica/banco-preguntas.md:** `../README.md` → `/`, `../tablas-decision/*`,
  `../blueprint/*`, `./simulacro-final.md`.
- **practica/labs-hands-on.md:** `../README.md` → `/`, `../blueprint/dominio-2..3`,
  `../practica` siblings, `../recursos.md`, `../PLAN-ESTRATEGICO.md`, **plus outbound
  links** to `../../intro_4h_agentcore/README.md`, `../../intro_4h_agentcore/agent/main.py`,
  `.../agent/memoria.py`, `.../agent/herramientas.py` (see outbound rule).
- **practica/simulacro-final.md:** `../PLAN-ESTRATEGICO.md`, `../README.md` → `/`,
  `../recursos.md`, `../blueprint/*`, `../tablas-decision/decision-por-restriccion.md`,
  `./banco-preguntas.md`.

### Outbound links to the sibling AgentCore course (must be absolute external URLs)

These point **outside** the Docusaurus site, so they must become plain absolute URLs or
Docusaurus will treat them as broken internal links and `onBrokenLinks: throw` will fail
the build. The sibling course is published by the same Pages site under its own subpath.

| Old outbound link | New absolute URL |
|---|---|
| `../intro_4h_agentcore/README.md` | `https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/README.md` |
| `../../intro_4h_agentcore/README.md` | `https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/README.md` |
| `../../intro_4h_agentcore/agent/main.py` | `https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/main.py` |
| `../../intro_4h_agentcore/agent/memoria.py` | `https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/memoria.py` |
| `../../intro_4h_agentcore/agent/herramientas.py` | `https://github.com/farithjhg/aws-bedrock-agentcore-course/blob/main/intro_4h_agentcore/agent/herramientas.py` |

Rationale: the `README.md` and `.py` files live in the sibling course, which is **not** a
Docusaurus doc. The `intro_4h_agentcore/README.md` is published as a raw `.md` file by the
Pages `path: .` upload, so the Pages absolute URL is a live target. The `.py` source files
are better linked to the GitHub blob view (they are not meaningfully served by Pages).
The plain-text mentions of `teoria/cap09-identidad.html` and `cap07-mcp-gateway.html` in
Domain 2 / labs are **not links** (they are inline code spans) — leave them as text; if any
is actually a link in the source, point it at the GitHub blob URL the same way. The
external AWS doc links in `recursos.md` (already absolute `https://...`) stay as-is.

> **onBrokenLinks / onBrokenMarkdownLinks:** set **both to `'throw'`** in
> `docusaurus.config.ts`. The build will then fail fast if any rewrite above is missed,
> which is the desired guard.

---

## 4. Config specifics (`docusaurus.config.ts`, `sidebars.ts`, theme)

Use TypeScript config (`.ts`) — Docusaurus v3 supports it and `create-docusaurus` scaffolds
it. Key values:

```ts
const config: Config = {
  title: 'AIP-C01 Exam Prep',
  tagline: 'Pass the AWS Certified Generative AI Developer – Professional (AIP-C01) exam',
  favicon: 'img/favicon.ico',
  url: 'https://farithjhg.github.io',
  baseUrl: '/aws-bedrock-agentcore-course/aip_c01_examen/',
  organizationName: 'farithjhg',
  projectName: 'aws-bedrock-agentcore-course',
  trailingSlash: false,              // verify on Pages; flip to true if deep-link refresh 404s
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'throw',
  outDir: '../',                     // build into aip_c01_examen/ (section 1)
  i18n: { defaultLocale: 'en', locales: ['en'] },
  presets: [
    ['classic', {
      docs: {
        routeBasePath: '/',          // docs-only
        sidebarPath: './sidebars.ts',
        // editUrl optional; point at the repo if desired
      },
      blog: false,
      theme: { customCss: './src/css/custom.css' },
    }],
  ],
  themeConfig: {
    colorMode: { defaultMode: 'dark', respectPrefersColorScheme: false },
    navbar: {
      title: 'AIP-C01 Exam Prep',
      items: [
        { type: 'docSidebar', sidebarId: 'courseSidebar', position: 'left', label: 'Course' },
        { href: 'https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/README.md', label: 'AgentCore course', position: 'right' },
        { href: 'https://aws.amazon.com/certification/certified-generative-ai-developer-professional/', label: 'AWS exam page', position: 'right' },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        { title: 'Related', items: [
          { label: 'AgentCore course', href: 'https://farithjhg.github.io/aws-bedrock-agentcore-course/intro_4h_agentcore/README.md' },
          { label: 'AWS AIP-C01 exam page', href: 'https://aws.amazon.com/certification/certified-generative-ai-developer-professional/' },
          { label: 'Official exam guide', href: 'https://docs.aws.amazon.com/aws-certification/latest/ai-professional-01/ai-professional-01.html' },
        ]},
      ],
      copyright: `AIP-C01 Exam-Prep Course. Part of the AWS Bedrock AgentCore repository.`,
    },
    // if search plugin installs cleanly, its themeConfig goes here
  },
};
```

### sidebars.ts

Use an **autogenerated** sidebar so the folder structure + `sidebar_position` +
`_category_.json` drive it (less manual wiring, matches section 2):

```ts
const sidebars: SidebarsConfig = {
  courseSidebar: [{ type: 'autogenerated', dirName: '.' }],
};
```

The navbar `sidebarId` must be `courseSidebar` to match.

### Dark mode + color nudge

- `colorMode.defaultMode: 'dark'`, `respectPrefersColorScheme: false` → dark by default.
- Optional gold/green nudge via `src/css/custom.css` using Infima variables, matching the
  existing `index.html` palette (`#071d16` background, `#f5d547` accent/gold,
  `#164534`/`#0c2a20` surfaces, green `#1f6f4f`-ish for primary). Example:

```css
:root {
  --ifm-color-primary: #1f6f4f;
  --ifm-color-primary-dark: #1b6346;
}
[data-theme='dark'] {
  --ifm-background-color: #071d16;
  --ifm-background-surface-color: #0c2a20;
  --ifm-color-primary: #f5d547;      /* gold accent for links/primary in dark */
  --ifm-link-color: #f5d547;
}
```

This is a **nudge, not a requirement** — keep it minimal and verify contrast.

### Offline search (best-effort, must not break the build)

Attempt `@easyops-cn/docusaurus-search-local` (`^0.51.1`, supports Docusaurus v3 — confirmed
via npm/GitHub; content rephrased for compliance). Add to `package.json` and register as a
theme in `docusaurus.config.ts`:

```ts
themes: [
  ['@easyops-cn/docusaurus-search-local', { hashed: true, indexDocs: true, docsRouteBasePath: '/' }],
],
```

**Fallback rule:** if the package fails to install cleanly (`npm ci` error) or the build
fails because of it, **remove the dependency and the `themes` entry and build without
search** rather than block the migration. Record in the final report which path was taken.

---

## 5. Decision: package manager, Node, and scaffolding approach

- Scaffold with `npx create-docusaurus@latest site classic --typescript` run **from inside
  `aip_c01_examen/`**, producing `aip_c01_examen/site/`. Then replace the generated
  `docs/`, `docusaurus.config.ts`, `sidebars.ts`, and `src/css/custom.css` per sections 2–4,
  and delete the generated `blog/`, sample docs, and `src/pages/index.tsx` (docs-only, home
  is the README doc at slug `/`).
- Commit `package-lock.json` (needed for `npm ci` cache in CI). Do **not** commit
  `node_modules/`.
- Node 20 in CI (Docusaurus v3 supports 20+; local is 24, both fine).

---

## 6. Decision: `.github/workflows/pages.yml` edit

Keep the job name, triggers (`push: [main]`, `workflow_dispatch`), `permissions`,
`concurrency`, and `upload-pages-artifact path: .`. **Insert a build phase before the
upload** so the artifact already contains the freshly built site at `aip_c01_examen/`.
Add, after `actions/checkout@v5` and before `actions/configure-pages@v5`:

```yaml
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: npm
          cache-dependency-path: aip_c01_examen/site/package-lock.json
      - name: Build AIP-C01 Docusaurus site
        working-directory: aip_c01_examen/site
        run: |
          npm ci
          npm run build
```

`npm run build` writes to `aip_c01_examen/` (via `outDir: '../'`), so the subsequent
`upload-pages-artifact path: .` uploads the whole repo including the freshly built exam
site. The AgentCore course and everything else are unaffected — they are already static
and are uploaded as-is. Do not change the deploy step.

> The runner's `aip_c01_examen/site/node_modules` and `aip_c01_examen/site/build` (if any)
> get uploaded too since `path: .` is the whole tree — but `node_modules` under `site/` is
> harmless clutter, not served content, and `.docusaurus`/`build` are not referenced.
> `outDir: '../'` means Docusaurus does **not** create a `site/build` dir, so the only
> extra weight is `site/node_modules`. Acceptable. (If artifact size becomes a concern
> later, add an `rm -rf aip_c01_examen/site/node_modules` step after build — optional, not
> required for correctness.)

---

## 7. Decision: `.gitignore` additions

Append to the **repo-root** `.gitignore`:

```
# Docusaurus (AIP-C01 site)
aip_c01_examen/site/node_modules/
aip_c01_examen/site/.docusaurus/
aip_c01_examen/site/build/
```

`node_modules` and the `.docusaurus` cache must never be committed. `build/` is listed
defensively even though `outDir: '../'` avoids creating it, in case a dev runs a default
build. The generated output at `aip_c01_examen/` (index.html, assets/, etc.) is produced in
CI and need not be committed; whether to also gitignore the generated root output is
optional — **decision: do not gitignore the generated `aip_c01_examen/` output files**,
because the originals and generated files coexist and over-broad ignores risk hiding real
content. CI regenerates them on every deploy.

---

## 8. Known gaps / assumptions (flagged, not blocking)

- **Originals vs generated copies:** the plan keeps the original `.md` files under
  `aip_c01_examen/` as the human-editable source and authors parallel copies under
  `aip_c01_examen/site/docs/`. This duplicates content. Acceptable for a one-time
  migration; if the user prefers a single source of truth, a later step can delete the
  originals once the site is verified. Assumption: keep originals for now.
- **`outDir: '../'` writing into a dir that contains the source `site/`:** verified-safe by
  design (source nested in `site/`), but the implementer must confirm after the first build
  that `aip_c01_examen/site/` is intact and `aip_c01_examen/index.html` is the generated
  page (step 9).
- **trailingSlash** must be empirically verified on Pages (step 9); `false` is the starting
  choice.
- **Search plugin** may not install cleanly; fallback is to ship without search.
- The old hand-written `aip_c01_examen/index.html` is intentionally replaced by the
  generated home page.

---

## 9. Implementation steps (ordered, each independently verifiable)

- [ ] 1. **Scaffold the Docusaurus project.** From `aip_c01_examen/`, run
      `npx create-docusaurus@latest site classic --typescript`. Delete generated sample
      content that will be replaced: `src/pages/index.tsx` (and `index.module.css`),
      `src/components/HomepageFeatures/`, the sample `docs/` tree, and `blog/`.
      Files: creates `aip_c01_examen/site/` (package.json, docusaurus.config.ts,
      sidebars.ts, src/, static/, tsconfig.json).
      Verify: `cd aip_c01_examen/site && npm run build` succeeds on the scaffold (before
      customization) — confirms the toolchain works on Node 24.

- [ ] 2. **Write `docusaurus.config.ts`** with all values from section 4 (title, tagline,
      url, baseUrl, organizationName/projectName, `outDir: '../'`, `trailingSlash: false`,
      `onBrokenLinks: 'throw'`, `onBrokenMarkdownLinks: 'throw'`, docs-only preset
      `routeBasePath: '/'`, `blog: false`, dark mode default, navbar + footer links).
      Files: `aip_c01_examen/site/docusaurus.config.ts`.
      Verify: `npm run typecheck` (if present) or `npm run build` parses config without
      error (will still fail on missing docs until step 4 — acceptable at this point).

- [ ] 3. **Write `sidebars.ts`** as the single autogenerated `courseSidebar` (section 4).
      Files: `aip_c01_examen/site/sidebars.ts`.
      Verify: config references `courseSidebar`; final verification in step 7.

- [ ] 4. **Create the `docs/` tree and copy content** per section 2: create
      `docs/intro.md`, `docs/plan-estrategico.md`, `docs/recursos.md`, and the
      `blueprint/`, `tablas-decision/`, `practica/` folders with all 12 domain/table/
      practice files, plus three `_category_.json` files. For each file: copy the body from
      the corresponding original under `aip_c01_examen/`, add the frontmatter from the
      section-2 table, and **remove the leading H1**.
      Files: 15 `.md` files + 3 `_category_.json` under `aip_c01_examen/site/docs/`.
      Verify: `npm run build` progresses past "loading docs" (link errors expected until
      step 5).

- [ ] 5. **Rewrite every cross-link** using the section-3 map: all internal links become
      root-absolute, extension-less doc links (`/`, `/blueprint/...`, `/tablas-decision/...`,
      `/practica/...`); all outbound AgentCore links become the absolute URLs in the
      outbound table.
      Files: all 15 `docs/*.md`.
      Verify: `cd aip_c01_examen/site && npm run build` completes with **zero** broken-link
      errors (because `onBrokenLinks: 'throw'`). This is the primary content verification.

- [ ] 6. **Apply the dark/gold-green theme** via `src/css/custom.css` (section 4) and add a
      favicon/logo in `static/img/` if desired (optional).
      Files: `aip_c01_examen/site/src/css/custom.css`, `static/img/*` (optional).
      Verify: `npm run build` still succeeds; `npm run serve` shows dark mode by default.

- [ ] 7. **Attempt offline search.** Add `@easyops-cn/docusaurus-search-local` to
      `package.json`, register the theme (section 4), run `npm install`, then `npm run build`.
      If install or build fails, remove the dependency and the `themes` entry and rebuild.
      Files: `aip_c01_examen/site/package.json`, `docusaurus.config.ts`.
      Verify: `npm run build` succeeds either way; if search stayed, a search box appears in
      `npm run serve`.

- [ ] 8. **Edit `.github/workflows/pages.yml`** per section 6: add `actions/setup-node@v4`
      (node 20, npm cache keyed on `aip_c01_examen/site/package-lock.json`) and a build step
      (`working-directory: aip_c01_examen/site`, `npm ci && npm run build`) **before**
      `configure-pages`/`upload-pages-artifact`. Keep `path: .`, triggers, permissions,
      concurrency, and the deploy step unchanged.
      Files: `.github/workflows/pages.yml`.
      Verify: `yamllint`/`actionlint` if available, else visual diff confirming only the
      two steps were inserted and nothing else changed.

- [ ] 9. **Edit repo-root `.gitignore`** per section 7 (ignore `site/node_modules/`,
      `site/.docusaurus/`, `site/build/`).
      Files: `.gitignore`.
      Verify: `git status --porcelain aip_c01_examen/site/node_modules` shows nothing (path
      ignored).

- [ ] 10. **Full local build + output placement check.** From `aip_c01_examen/site` run
      `npm ci && npm run build`, then confirm `aip_c01_examen/index.html` is the generated
      Docusaurus home page, `aip_c01_examen/assets/` exists, and `aip_c01_examen/site/`
      (source) is intact. Then `npm run serve -- --host 0.0.0.0` and manually load the home
      page, a deep blueprint page, the master decision table (must be first in its
      category), and click an outbound AgentCore link.
      Files: none (verification only; clean up any stray build dirs under `site/`).
      Verify: build exits 0 with no broken-link throw; sidebar order matches section 2
      (Overview → Blueprint → Decision tables [master first] → Practice); dark mode on;
      deep-link refresh does not 404 (if it does, set `trailingSlash: true`, rebuild, re-verify,
      and record the change).

- [ ] 11. **Commit** (only when the user asks): stage `aip_c01_examen/site/` (source,
      including `package-lock.json`, excluding ignored dirs), the modified
      `.github/workflows/pages.yml`, and `.gitignore`. Do **not** stage `node_modules`.
      Push to a branch and confirm the Pages workflow builds green, then load the live URL
      `https://farithjhg.github.io/aws-bedrock-agentcore-course/aip_c01_examen/`.
      Verify: Actions run succeeds; live site loads with working internal links and the
      AgentCore course still reachable at its own subpath.

---

## 10. Summary of the two headline decisions

- **outDir mechanism:** Docusaurus `outDir: '../'`, so `npm run build` (run in
  `aip_c01_examen/site/`) writes the compiled site directly into `aip_c01_examen/`, which
  the existing `upload-pages-artifact path: .` publishes at
  `/aws-bedrock-agentcore-course/aip_c01_examen/`. No post-build copy step. The Docusaurus
  source stays in `aip_c01_examen/site/` and is gitignored where it matters
  (`node_modules`, `.docusaurus`, `build`); it is never the served index.
- **trailingSlash:** start with `trailingSlash: false` (explicit, avoids project-subpath
  ambiguity), and verify deep-link refresh on GitHub Pages in step 10; flip to `true` and
  rebuild only if a deep link 404s on refresh.
