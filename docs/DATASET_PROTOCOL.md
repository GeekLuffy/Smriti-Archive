# Archival Dataset Protocol: Provenance, Rights Hygiene, Quality Tiers & Annotation Standards

**Project**: SIH 2026 Problem Statement SIH26096 (Digital Heritage Archive for Memorials, Manuscripts & Ambedkar)  
**Document Version**: 1.0.0 (Phase E0 Specification)  
**Status**: Authoritative Protocol  

---

## 1. Introduction and Objectives

Archival documents, historical manuscripts, and government records—specifically the foundational works and speeches of Dr. B.R. Ambedkar—present unique preservation and machine-readability challenges. Unlike contemporary digital-native publications, historical volumes exhibit physical paper degradation, aged typography, multi-lingual scripts (English, Marathi, Hindi), variable photostatic printing, and complex parliamentary layouts.

The primary objective of this protocol is to define an immutable, research-grade intake and curation standard for the SIH26096 digital heritage repository. The protocol enforces:
1. **Provenance & Custodial Integrity**: Full traceability from institutional custodial sources to individual rendered page tokens.
2. **Rights & Legal Hygiene**: Explicit intellectual property classification preventing unauthorized ingestion of copyrighted materials.
3. **Scan Quality Stratification**: Standardized classification into Tier 1 (Pristine), Tier 2 (Archival/Microfilm), and Tier 3 (Degraded/Brittle).
4. **Stratified Page Sampling**: Rigorous representation of document layouts across voluminous archival publications.
5. **Human Annotation & Ground Truth Standards**: Strict double-blind transcription standards preserving historical orthography.

---

## 2. Archival Provenance and Custodial Integrity

### 2.1 Custodial Institutions & Acquisition Sources
All documents ingested into the repository must originate from authenticated custodial bodies or recognized public archival repositories:
- **Dr. Ambedkar Foundation (DAF)**, Ministry of Social Justice and Empowerment, Government of India.
- **Gazetteers Department & Education Department**, Government of Maharashtra (publishers of *Dr. Babasaheb Ambedkar: Writings and Speeches*).
- **National Archives of India (NAI)**, New Delhi.
- **Parliament Library & Constituent Assembly Debates Records**, New Delhi.
- **Public Domain Historical Repositories** (e.g., Digital Library of India, Internet Archive historical preservation scans with public licenses).

### 2.2 Strict Prohibition on Automated Scraping
Automated, unverified web scraping of external digital repositories is **strictly prohibited**. Ingestion must proceed through formal accessioning:
1. Offline receipt or manual retrieval from official custodial portals.
2. Integrity validation against institutional catalogs.
3. Creation and validation of a machine-readable `DocumentManifest` JSON before pipeline intake.

### 2.3 Physical Asset Separation & Cryptographic Chain
To maintain provenance and avoid data corruption:
- **Raw Document Storage (`data/raw/`)**: Original PDF documents and unedited high-resolution master scans are placed in `data/raw/`. Once placed, raw assets are treated as **read-only and immutable**.
- **Manifest Metadata (`data/manifests/`)**: Each document has an associated manifest `{document_id}.json` tracking its accession details.
- **Cryptographic Hashing**: Upon intake, every raw asset is hashed using SHA-256 (`checksum_sha256`). Any subsequent mutation or file corruption invalidates the manifest integrity check.
- **Processed Page Images (`data/processed/pages/`)**: Rendered pages are stored separately and cross-referenced with `{document_id}_p{page_num:04d}` identifiers and page provenance records.

---

## 3. Rights Verification Protocol and Legal Taxonomy

Archival documents must be audited for copyright status prior to benchmark execution or public data distribution.

### 3.1 Statutory Framework
The legal basis for processing historical Indian heritage records and Dr. Ambedkar's writings is governed by:
1. **The Indian Copyright Act, 1957, Section 52(1)(q)**: Specifically exempts from copyright infringement:
   - The reproduction or publication of any matter published in any Official Gazette.
   - The reproduction of the report of any committee, commission, council, or board appointed by the government, or of any Act of a Legislature.
   - The reproduction or publication of any judgment or order of a court, tribunal, or other judicial authority.
2. **The Indian Copyright Act, 1957, Section 22**: Copyright in published literary, dramatic, musical, and artistic works expires **60 years post-mortem** (calculated from the beginning of the calendar year following the year of the author's death). For works of Dr. B.R. Ambedkar (who passed away in December 1956), original copyright expired on January 1, 2017.
3. **Official Open Publication Declarations**: Publications issued by the Ministry of Social Justice and Empowerment for public educational use and historical scholarship.

### 3.2 Rights Status Taxonomy

| Rights Status | Definition | Benchmark Clearing | Public Redistribution | Evidence Requirement |
|---|---|---|---|---|
| `public` | Public domain under statutory expiry (Section 22) or official government proceedings (Section 52(1)(q)). | **Cleared** | **Permitted** | Statutory citation or official gazette reference. |
| `verified` | Explicit custodial permission, Creative Commons license, or open cultural heritage waiver. | **Cleared** | Governed by license terms (attribution required). | License URL, archival agreement ID, or custodial clearance memo. |
| `restricted` | Copyright active or disputed; fair-dealing educational/research exemption only. | **Cleared (Closed Benchmark Only)** | **Prohibited** | Description of fair-dealing research basis and limitations. |
| `unknown` | Intake incomplete; rights status not yet verified. | **Blocked** | **Prohibited** | Must undergo rights audit before inclusion in pipelines. |

### 3.3 Rights Hygiene Gates
The ingestion module `sih_archive.ingestion.protocol` evaluates all manifests through the `check_rights_hygiene()` function:
- Documents marked `unknown` are quarantined and raise warnings.
- Documents marked `verified` or `public` without non-empty `rights_evidence` fail schema validation.
- Pipeline runners check rights hygiene before batch rendering or OCR execution.

---

## 4. Archival Scan Quality Classification Tiers

Historical scans vary substantially in visual fidelity. To evaluate OCR performance fairly, documents and individual pages are categorized into three standardized scan quality tiers:

```
+-------------------------------------------------------------------------+
|                  Scan Quality Classification Hierarchy                  |
+-------------------------------------------------------------------------+
| Tier 1: Preservation Grade  | 300+ DPI, uniform illumination, flatbed   |
| Tier 2: Archival/Microfilm  | 200-300 DPI, moderate skew, slight bleed  |
| Tier 3: Severely Degraded   | <200 DPI, heavy bleed, foxing, torn, warp |
+-------------------------------------------------------------------------+
```

### 4.1 Tier 1: Preservation Grade (Pristine Archival Scan)
- **Resolution**: 300 DPI or higher.
- **Physical Characteristics**: Scanned from original bound volumes using modern planetary or flatbed scanners; uniform illumination without shadows; clean paper margins; negligible skew ($< 1.0^\circ$).
- **Text Characteristics**: Crisp letterpress or modern typeset typography; high contrast between ink and background; absence of bleed-through or ghosting.
- **Benchmark Role**: Serves as the upper-bound baseline to evaluate the core character recognition engine accuracy without compounding degradation factors.

### 4.2 Tier 2: Archival / Microfilm / Photostat
- **Resolution**: 200–300 DPI.
- **Physical Characteristics**: Scanned from second-generation photostatic prints, microfiche, or aged government gazette pulp paper (1920s–1950s). Mild page curvature near the binding; minor skew ($1.0^\circ \text{ to } 3.0^\circ$).
- **Text Characteristics**: Faint type bars, minor ink spread or stroke thinning, mild bleed-through from verso page, faint paper grain, occasional foxing spots.
- **Benchmark Role**: Tests the effectiveness of adaptive thresholding (Otsu, adaptive Gaussian), deskewing algorithms, and contrast enhancement (CLAHE).

### 4.3 Tier 3: Severely Degraded / Brittle Historical Manuscript
- **Resolution**: Below 200 DPI or high-resolution capture of physically decomposed originals.
- **Physical Characteristics**: Severe paper discoloration, brittle margins, torn edges, deep shadow gradients along gutter margins, heavy skew ($> 3.0^\circ$), water/damp staining, insect damage.
- **Text Characteristics**: Heavy ink bleed-through where reverse-side text collides with recto text; broken ligature strokes in Devanagari script; faded or smeared type; mixed handwritten marginalia.
- **Benchmark Role**: Tests advanced morphological filtering, binarization stability, and the ability of the pipeline to report low-confidence regions rather than catastrophic hallucination.

---

## 5. Stratified Page Selection Protocol

### 5.1 Rationale for Stratified Sampling
Archival volumes (e.g., *Dr. Babasaheb Ambedkar: Writings and Speeches*, Vol. 1–22) typically comprise 500 to 1,200 pages per volume. Exhaustive, character-accurate manual transcription of entire multi-volume sets is economically and operationally prohibitive for initial benchmark phases.

Arbitrary or convenient sampling (e.g., selecting the first 10 pages) introduces catastrophic evaluation bias because front matter (indexes, preface) differs radically from complex legislative debates or statistical appendices. Therefore, a **stratified random sampling protocol** is enforced.

### 5.2 Strata Definitions

| Stratum Code | Stratum Name | Visual & Layout Characteristics | Target Proportion |
|---|---|---|---|
| **Stratum A** | Front Matter & Structure | Title page, table of contents, publisher notes, Roman numeral pagination. | 10% |
| **Stratum B** | Standard Dense Prose | Single-column body text (speeches, essays, articles). Standard paragraph layout. | 45% |
| **Stratum C** | Complex Multi-Column & Footnotes | Legislative assembly debates, multi-column testimony, dense bilingual footnotes. | 25% |
| **Stratum D** | Tabular & Statistical Exhibits | Budgets, census tables, constituency breakdowns, numerical matrices. | 10% |
| **Stratum E** | Degraded / Damaged Samples | Pages with heavy physical defects, bleed-through, stains, or gutter curvature. | 10% |

### 5.3 Sample Size Accounting Table
All benchmark experiments must publish a stratified sample accounting table reporting target vs. actual sample sizes:

| Document ID | Stratum Code | Description | Target Sample Size | Actual Sample Size | Annotation Coverage (%) |
|---|---|---|---|---|---|
| `ambedkar_speech_vol1` | Stratum A | Front Matter (Title, TOC) | 1 page | 1 page | 100% |
| `ambedkar_speech_vol1` | Stratum B | Dense Prose (Castes in India, Annihilation) | 2 pages | 2 pages | 100% |
| `ambedkar_speech_vol1` | Stratum C | Complex Legislative / Essay | 1 page | 1 page | 100% |
| `ambedkar_speech_vol1` | Stratum D | Statistical Tables & Exhibits | 1 page | 1 page | 100% |
| `ambedkar_speech_vol1` | Stratum E | Degraded Historical Sample | 1 page | 1 page | 100% |

---

## 6. Human Annotation and Ground Truth Standards

### 6.1 Double-Blind Transcription Protocol
To prevent individual annotator bias and errors:
1. Two independent human transcribers transcribe each selected page image without viewing the output of any OCR engine.
2. An automated diff tool computes the character-level agreement between Transcriber 1 and Transcriber 2.
3. Where discrepancies occur (inter-annotator disagreement), an Archival Domain Adjudicator reviews the original scan and determines the definitive ground truth reference string.

### 6.2 Historical Orthography Preservation
- **No Modernizing Auto-Correction**: Transcribers must **preserve verbatim** the exact spelling, archaic terms, historical hyphenations, and period-specific punctuation appearing on the physical page (e.g., *"to-day"*, *"connexion"*, *"judgement"*, *"depressed classes"*).
- **Hyphenated Line Breaks**: Words split across lines with a trailing hyphen must be recorded as printed on the line break (e.g., `organi-` on line 1, `zation` on line 2), with layout tokens preserving the break.
- **Ligatures & Diacritics**: Transcribe Devanagari ligatures (संयुक्त अक्षरे) and Sanskrit/Marathi transliteration marks exactly according to Unicode standards (NFC normalization).

### 6.3 Standardized Anomaly & Damage Placeholders
When physical degradation destroys text beyond unambiguous legibility:
- `[illegible]`: Ink smeared, faded, or obscured such that transcribers cannot determine characters with 100% confidence.
- `[damaged]`: Physical paper void, tear, or missing fragment.
- `[marginalia: <text>]`: Marginal handwritten note or custodial stamp.
- `[strikethrough: <text>]`: Deleted text in manuscript drafts.

### 6.4 Bounding Box Annotation Standards
- **Coordinate System**: Absolute pixel coordinates `[x, y, w, h]` where:
  - `x`: Horizontal distance from left edge in pixels (at 300 DPI resolution).
  - `y`: Vertical distance from top edge in pixels.
  - `w`: Width of the bounding rectangle in pixels.
  - `h`: Height of the bounding rectangle in pixels.
- **Granularity**: Word-level bounding boxes enclosing all ascenders, descenders, and diacritics without excessive whitespace margins (padding $\le 2$ pixels).
- **Line & Block Grouping**: Words belonging to a coherent typographical line share the same `line_num`. Blocks share the same `block_num`.

### 6.5 Inter-Annotator Agreement (IAA) Quality Control
The quality of ground truth datasets is quantified using two metrics:
1. **Character Agreement Rate ($CAR$)**:
   $$CAR = 1.0 - \frac{\text{LevenshteinDistance}(T_1, T_2)}{\max(|T_1|, |T_2|)}$$
   The repository requires $CAR \ge 0.985$ before adjudication.
2. **Bounding Box Intersection-over-Union ($IoU$) Agreement**:
   For region annotations, annotator box overlap must achieve a mean $IoU \ge 0.85$.

---

## 7. Machine-Readable Manifest Schema Reference

Each document intake is governed by `src/sih_archive/schemas/manifest.py`. The required JSON structure:

```json
{
  "document_id": "ambedkar_speech_vol1",
  "title": "Dr. Babasaheb Ambedkar: Writings and Speeches, Vol. 1",
  "source_url": "https://www.mea.gov.in/books-writings-and-speeches-dr-ambedkar.htm",
  "source_organization": "Dr. Ambedkar Foundation, Ministry of Social Justice and Empowerment, Government of India",
  "language": "eng",
  "script": "Latn",
  "rights_status": "public",
  "rights_evidence": "Indian Copyright Act 1957 Section 52(1)(q); Government of India open publication for public education; author deceased 1956 (copyright expired under 60-year post-mortem rule Section 22).",
  "local_path": "data/raw/ambedkar_speech_vol1.pdf",
  "page_count": 5,
  "notes": "Archival benchmark volume 1 containing Castes in India (1916), Annihilation of Caste (1936), and Maharashtra as a Linguistic Province (1948).",
  "checksum_sha256": "1d82d8f2669f53762290adaac1fbb28f9410553ce014a59d3dcd2a3933cfe39f",
  "created_at": "2026-09-27T12:22:40.790773+00:00"
}
```

### 7.1 Field Definitions & Constraints

- `document_id` (*string, required*): Alphanumeric identifier, hyphens, and underscores only (`^[a-zA-Z0-9_\-]+$`), 3 to 64 characters. Directory traversal characters (`..`, `/`, `\`) are strictly forbidden.
- `title` (*string, required*): Full human-readable title (1 to 512 characters).
- `source_url` (*string, optional*): Authoritative URL of online archive or repository.
- `source_organization` (*string, required*): Custodial institution responsible for preservation.
- `language` (*string, required*): ISO 639-3 three-letter lowercase code (`^[a-z]{3}$`, e.g., `eng`, `mar`, `hin`).
- `script` (*string, required*): ISO 15924 four-letter code (`^[A-Z][a-z]{3}$`, e.g., `Latn`, `Deva`).
- `rights_status` (*enum, required*): One of `unknown`, `verified`, `restricted`, `public`.
- `rights_evidence` (*string, required for verified/public*): Detailed statutory citation or license reference.
- `local_path` (*string, required*): Path relative to repository root starting with `data/raw/`. Path traversal is rejected.
- `page_count` (*integer, required*): Total pages in the document ($\ge 1$).
- `notes` (*string, optional*): Physical condition, edition history, scan artifacts.
- `checksum_sha256` (*string, optional*): 64-character lowercase hexadecimal SHA-256 digest of the raw asset.
- `created_at` (*string, default: UTC ISO 8601*): Registration timestamp.

---

## 8. Summary Checklist for Archival Intake

- [x] Document acquired from authenticated custodial source or official portal.
- [x] Document placed directly into `data/raw/` without renaming corruption.
- [x] SHA-256 cryptographic digest calculated and stored.
- [x] Rights status verified against Indian Copyright Act 1957; statutory evidence cited.
- [x] Document manifest generated and saved to `data/manifests/{document_id}.json`.
- [x] Manifest validated via `validate_manifest()` and `audit_intake()`.
- [x] Quality tiers and sampling strata assigned for benchmark rendering.
