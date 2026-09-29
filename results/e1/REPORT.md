# SIH26096 — Phase E1 Archival OCR Benchmark Report

- **Execution Date:** 2026-09-29 10:41:24Z
- **Gate Status:** `BLOCKED_ON_HOST_OCR_BINARY`
- **Host Tesseract Available:** `False`
- **Target Languages:** eng, hin, mar
- **Preprocessing Variants:** raw, grayscale, denoise, deskew, adaptive_gaussian
- **Discovered Pages:** 5 (Target: 30–50 pages)

## Research Integrity & Gating Notice

> [!WARNING]
> **Phase E1 is BLOCKED on host OCR binary.** Tesseract OCR v5+ is not installed on host PATH.
> Remediation: Tesseract OCR binary not found. Searched: env TESSERACT_CMD/TESSERACT_PATH, system PATH lookup, C:\Program Files\Tesseract-OCR\tesseract.exe, C:\Program Files (x86)\Tesseract-OCR\tesseract.exe, C:\Users\user\AppData\Local\Programs\Tesseract-OCR\tesseract.exe. Remediation: Install Tesseract on Windows via 'winget install UB-Mannheim.TesseractOCR' or on Linux via 'sudo apt-get install tesseract-ocr', or pass --tesseract-cmd.

## Benchmark Metrics Summary

- **Total Execution Runs:** 0
- **Successfully Evaluated (with Ground Truth):** 0
- **Unannotated Runs (Ground Truth Unavailable):** 0
- **Mean CER / WER:** Not computed (Awaiting ground truth annotations)
