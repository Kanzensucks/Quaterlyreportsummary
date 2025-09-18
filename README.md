# Quarterly Report Summariser

A lightweight pipeline that reads quarterly PDF reports, extracts decision-useful points, and ranks them by **Value** only

---

## Features
- **PDF ingestion** → reads text directly from `.pdf` files in `./reports/`.
- **Chunking** → splits large reports into realistic chunks (`max_chars` + overlap).
- **Summarisation** → uses an LLM (via [Ollama](https://ollama.ai/)) to extract concise bullet points with metrics, guidance, and KPIs.
- **Ranking (Value only)** → scores each point based on numbers, %, pp, $, and KPI keywords.
- **Outputs**:
  - `points_output/*.txt` → raw summarised points
  - `ranker_output/*.txt` → ranked points by Value

---

##  Project Structure
```
quaterly_report_summary/
├── app/
│   ├── config.py
│   ├── main.py
├── pipeline/
│   ├── chunker.py
│   ├── ollama_client.py
│   ├── pdf_reader.py
│   ├── ranker.py
│   └── summariser.py
├── prompts/
│   ├── points_prompt.txt
│   └── title_prompt.txt
├── points_output/
├── ranker_output/
├── reports/
├── .env
├── requirements.txt
└── run.py
```

---

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up `.env`**
   ```ini
   OLLAMA_HOST=http://127.0.0.1:11434
   MODEL=llama3.1:8b
   MAX_CHARS=3000
   OVERLAP=200
   TEMPERATURE=0.1
   TIMEOUT=60
   POINTS_PROMPT=prompts/points_prompt.txt
   ```

3. **Place reports**
   - Put your PDF reports in the `./reports/` folder.

---

## Run

```bash
python run.py --verbose
```

This will:
1. Extract text from the latest PDF in `./reports/`.
2. Summarise into bullet points (`points_output/*.txt`).
3. Rank the points by **Value only** (`ranker_output/*.txt`).

---

## Output Example

`points_output/MSFT_FY25_Q4_POINTS_20250918.txt`:
```
- Revenue grew +11% YoY to $9.8b on subscription strength. [p.3]
- Market share +120bps QoQ in North America. [p.5]
- Retention improved +2pp QoQ to 68%. [p.9]
```

`ranker_output/Ranked_Points_20250918.txt`:
```
Ranked Points (Value Only)
===================================

Rank  Value  Point
-----------------------------------
  1    62.0  Revenue grew +11% YoY to $9.8b on subscription strength. [p.3]
  2    57.5  Market share +120bps QoQ in North America. [p.5]
  3    52.0  Retention improved +2pp QoQ to 68%. [p.9]
```

---

## Notes
- Works best with reports that contain real text (not scanned images).
- If reports are image-based, add OCR (e.g. `pytesseract`) before feeding into the pipeline.
- No business model or alignment scoring is used anymore — **pure Value ranking**.
