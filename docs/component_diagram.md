# USB PD Parser – Data Flow Diagram (Component Diagram)

This document shows the **data flow** between components of the USB PD Parser, in the same style as the sample project (e.g. Face Recognition): processes, labeled data flows, data stores, and external entities that consume outputs.

> **Viewing the diagram**  
> IntelliJ does not render Mermaid by default. View this file on **GitHub**, use a **Mermaid plugin** in IntelliJ, or paste the code block into [mermaid.live](https://mermaid.live).

---

## Data Flow Diagram (DFD)

```mermaid
graph TD
    %% External source
    PDF((PDF File))
    User((User / CLI))

    %% Processes
    P1[CLI]
    P2[USBPDParser]
    P3[PDF Extract]
    P4[TOC Extract]
    P5[Inline Headings]
    P6[Section Build]
    P7[Write Core JSONL]
    P8[Metadata + Content + Summary]
    P9[Validator]
    P10[Excel Report]

    %% Data stores
    D1[(usb_pd_toc.jsonl)]
    D2[(usb_pd_spec.jsonl)]
    D3[(usb_pd_content.jsonl)]
    D4[(usb_pd_metadata.jsonl)]
    D5[(output.json)]
    D6[(validation_report.json)]
    D7[(validation_report.xlsx)]
    D8[(usbpd_parser.log)]

    %% External entities that consume
    Dev((Developer))
    Consumer((Downstream apps))

    %% Flows
    User -->|command, pdf_path, output_dir| P1
    PDF -->|path| P2
    P1 -->|invoke parse| P2
    P2 -->|PDF path| P3
    P3 -->|page dicts with text| P4
    P3 -->|page dicts| P5
    P4 -->|TOC entries| P6
    P5 -->|inline headings| P6
    P3 -->|pages| P6
    P6 -->|sections + toc| P7
    P7 -->|toc, spec paths| P8
    P7 -->|toc, spec| P9
    P9 -->|validation JSON| P10
    P2 -->|log events| D8

    P7 -->|write| D1
    P7 -->|write| D2
    P8 -->|write| D3
    P8 -->|write| D4
    P8 -->|write| D5
    P9 -->|write| D6
    P10 -->|write| D7

    D8 -->|review errors, timings| Dev
    D1 -->|structured TOC| Consumer
    D2 -->|spec content| Consumer
    D5 -->|summary stats| Consumer
```

---

## Flow Descriptions

| Flow label | From → To | Description |
|------------|-----------|-------------|
| command, pdf_path, output_dir | User → CLI | User runs e.g. `parse <pdf> --out data` |
| invoke parse | CLI → USBPDParser | CLI calls the parser with arguments |
| PDF path | Parser → PDF Extract | Path to the USB PD spec PDF |
| page dicts with text | PDF Extract → TOC Extract | List of `{page, text}` per page |
| page dicts | PDF Extract → Inline Headings | Same page list for heading scan |
| TOC entries | TOC Extract → Section Build | section_id, title, page, level, etc. |
| inline headings | Inline Headings → Section Build | Numeric headings from body |
| pages | PDF Extract → Section Build | Page text for content extraction |
| sections + toc | Section Build → Write Core JSONL | In-memory data to persist |
| toc, spec paths | Core → Metadata + Content + Summary | Paths to generated files |
| toc, spec | Core → Validator | TOC vs spec comparison |
| validation JSON | Validator → Excel Report | validation_report.json |
| log events | Parser → usbpd_parser.log | Timings, I/O metadata, errors |
| write | Processes → Data stores | Each process writes its output file(s) |
| review errors, timings | Log → Developer | Developer uses log for debugging |
| structured TOC / spec content / summary stats | Data stores → Downstream apps | Outputs consumed by other tools or users |

---

## Component Summary

- **Processes (rectangles):** CLI, USBPDParser, PDF Extract, TOC Extract, Inline Headings, Section Build, Write Core JSONL, Metadata/Content/Summary generators, Validator, Excel Report.
- **Data stores (cylinders):** All JSONL/JSON/Excel outputs and the log file.
- **External entities (double circles):** User/CLI (input), Developer (consumes log), Downstream apps (consume TOC, spec, summary).

For **inputs, processing, and outputs** of each component in detail, see [architecture.md](architecture.md).
