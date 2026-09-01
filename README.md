# Traceweave

**🇮🇹 Italiano | [🇬🇧 English](#english)**

Un analizzatore di log HTTP da riga di comando scritto in Python. Analizza file in formato Common Log Format (CLF), calcola riepiloghi del traffico con pandas e genera un report testuale e un grafico del traffico orario.

Costruito e validato sul dataset NASA HTTP Logs, ma funziona con qualsiasi file di log in formato Common Log Format.

## Panoramica

Traceweave prende un log di accesso HTTP grezzo e lo trasforma in un'analisi strutturata: codici di stato, metodi HTTP, host principali, tipi di risorsa e distribuzione oraria del traffico. È un tool CLI a file singolo progettato per mostrare un'architettura a pipeline pulita e leggibile: lettura del file, parsing tramite regex, costruzione del DataFrame, analisi e generazione del report sono gestiti da cinque classi separate, ciascuna con una singola responsabilità.

## Funzionalità

- Analizza le righe di log in Common Log Format con un'unica regex compilata
- Categorizza i codici di stato HTTP (Success, Redirect, Client Error, Server Error)
- Categorizza le risorse richieste per estensione del file
- Calcola 5 riepiloghi: stato, metodo HTTP, host principali, tipo di risorsa, traffico orario
- Genera un report testuale (a schermo e/o su file) e un grafico a barre matplotlib del traffico orario
- Configurabile tramite `argparse`, nessun input interattivo richiesto
- Gestisce file mancanti e log malformati senza crashare, con messaggi di avviso chiari

## Demo

Input e output di esempio sono nella cartella `examples/` (`sample_log.txt`, `hourly_chart.png`).

Eseguilo:

```bash
python main.py --file examples/sample_log.txt
```

Grafico del traffico orario:

![Hourly traffic chart](examples/hourly_chart.png)

Estratto del report testuale:

```
Status summary
Success         5
Redirect        2
Client Error    2
Server Error    1

Method summary
GET     9
POST    1

Host summary
burger.letters.com       2
netcom17.netcom.com      2
unicomp6.unicomp.net     1
199.120.110.21           1
205.212.115.106          1
d104.aa.net              1
piweba3y.prodigy.com     1
alyssa.prodigy.com       1

Resource summary
Directory        3
html             3
gif              1
jpeg             1
No extension     1
jpg              1

Hourly summary
0     3
1     1
2     1
10    1
14    2
20    1
23    1
```

## Installazione

Richiede Python 3.10 o successivo (usa gli hint di tipo union `X | Y`).

```bash
git clone https://github.com/boccassinisergio-afk/Traceweave.git
cd Traceweave
pip install pandas matplotlib
```

## Utilizzo

```bash
python main.py --file log.txt
```

Argomenti opzionali:

```bash
python main.py --file log.txt --export report.txt --chart hourly_chart.png
```

| Argomento  | Obbligatorio | Default              | Descrizione                     |
|------------|----------|----------------------|----------------------------------|
| `--file`   | Sì      | -                    | Percorso del file di log da analizzare |
| `--export` | No       | `report.txt`         | Percorso dove salvare il report testuale |
| `--chart`  | No       | `hourly_chart.png`   | Percorso dove salvare il grafico orario |

## Architettura della pipeline

```
FileReader -> LogParser -> DataFrameBuilder -> Analyzer -> ReportGenerator
```

- **FileReader**: legge il file di log grezzo dal disco, riga per riga
- **LogParser**: analizza ogni riga grezza in un oggetto `HTTPRequest` usando la regex CLF, raccogliendo le righe non analizzabili separatamente invece di fallire su di esse
- **DataFrameBuilder**: converte la lista di oggetti `HTTPRequest` analizzati in un DataFrame pandas
- **Analyzer**: aggiunge colonne derivate (categoria di stato, categoria della risorsa, datetime analizzato) e calcola i 5 riepiloghi
- **ReportGenerator**: formatta i riepiloghi in un report testuale e un grafico a barre

## Analisi della regex

```
unicomp6.unicomp.net - - [01/Jul/1995:00:00:06 -0400] "GET /shuttle/countdown/ HTTP/1.0" 200 3985
│                    │   │                              │     │                 │         │    │
│                    │   │                              │     │                 │         │    └── Byte trasferiti
│                    │   │                              │     │                 │         └─────── Stato HTTP
│                    │   │                              │     │                 └───────────────── Protocollo
│                    │   │                              │     └─────────────────────────────────── Risorsa richiesta
│                    │   │                              └───────────────────────────────────────── Metodo HTTP
│                    │   └──────────────────────────────────────────────────────────────────────── Timestamp
│                    └──────────────────────────────────────────────────────────────────────────── identd / userid (ignorato)
└───────────────────────────────────────────────────────────────────────────────────────────────── Host/IP client
```

## Roadmap

Non ancora implementato, pianificato per iterazioni future:

- Logging (attualmente usa `print` per gli avvisi)
- Test automatizzati
- Output del report in HTML
- Packaging per la distribuzione (`pyproject.toml`, PyPI)
- Possibile refactor da un singolo `main.py` a moduli separati (`parser.py`, `analyzer.py`, `report_generator.py`, ...), stesso comportamento, struttura più pulita

## Stack tecnologico

Python, pandas, matplotlib, `re`, `argparse`

## Autore

Sergio Boccassini

- GitHub: [boccassinisergio-afk](https://github.com/boccassinisergio-afk)
- LinkedIn: [sergio-boccassini](https://www.linkedin.com/in/sergio-boccassini)
- X: [@boccassini_ai](https://x.com/boccassini_ai)

<br><br>

---
---

<a name="english"></a>

# Traceweave

**[🇮🇹 Italiano](#traceweave) | 🇬🇧 English**

A command-line HTTP log analyzer built in Python. Parses Common Log Format (CLF) files, computes traffic summaries with pandas, and generates a text report and an hourly traffic chart.

Built and validated against the NASA HTTP Logs dataset, but works with any log file in Common Log Format.

## Overview

Traceweave takes a raw HTTP access log and turns it into a structured analysis: status codes, HTTP methods, top hosts, resource types, and hourly traffic distribution. It is a single-file CLI tool designed to show a clean, readable pipeline architecture: file reading, regex parsing, DataFrame construction, analysis, and report generation are handled by five separate classes, each with one responsibility.

## Features

- Parses Common Log Format log lines with a single compiled regex
- Categorizes HTTP status codes (Success, Redirect, Client Error, Server Error)
- Categorizes requested resources by file extension
- Computes 5 summaries: status, HTTP method, top hosts, resource type, hourly traffic
- Generates a text report (screen and/or file) and a matplotlib bar chart of hourly traffic
- Configurable via `argparse`, no interactive input required
- Handles missing files and malformed logs without crashing, with clear warning messages

## Demo

Sample input and output are in the `examples/` folder (`sample_log.txt`, `hourly_chart.png`).

Run it:

```bash
python main.py --file examples/sample_log.txt
```

Hourly traffic chart:

![Hourly traffic chart](examples/hourly_chart.png)

Text report excerpt:

```
Status summary
Success         5
Redirect        2
Client Error    2
Server Error    1

Method summary
GET     9
POST    1

Host summary
burger.letters.com       2
netcom17.netcom.com      2
unicomp6.unicomp.net     1
199.120.110.21           1
205.212.115.106          1
d104.aa.net              1
piweba3y.prodigy.com     1
alyssa.prodigy.com       1

Resource summary
Directory        3
html             3
gif              1
jpeg             1
No extension     1
jpg              1

Hourly summary
0     3
1     1
2     1
10    1
14    2
20    1
23    1
```

## Installation

Requires Python 3.10 or later (uses `X | Y` union type hints).

```bash
git clone https://github.com/boccassinisergio-afk/Traceweave.git
cd Traceweave
pip install pandas matplotlib
```

## Usage

```bash
python main.py --file log.txt
```

Optional arguments:

```bash
python main.py --file log.txt --export report.txt --chart hourly_chart.png
```

| Argument   | Required | Default             | Description                     |
|------------|----------|----------------------|----------------------------------|
| `--file`   | Yes      | -                    | Path to the log file to analyze |
| `--export` | No       | `report.txt`         | Path where the text report is saved |
| `--chart`  | No       | `hourly_chart.png`   | Path where the hourly chart is saved |

## Pipeline architecture

```
FileReader -> LogParser -> DataFrameBuilder -> Analyzer -> ReportGenerator
```

- **FileReader**: reads the raw log file from disk, line by line
- **LogParser**: parses each raw line into an `HTTPRequest` object using the CLF regex, collecting unparsed lines separately instead of failing on them
- **DataFrameBuilder**: converts the list of parsed `HTTPRequest` objects into a pandas DataFrame
- **Analyzer**: adds derived columns (status category, resource category, parsed datetime) and computes the 5 summaries
- **ReportGenerator**: formats the summaries into a text report and a bar chart

## Regex breakdown

```
unicomp6.unicomp.net - - [01/Jul/1995:00:00:06 -0400] "GET /shuttle/countdown/ HTTP/1.0" 200 3985
│                    │   │                              │     │                 │         │    │
│                    │   │                              │     │                 │         │    └── Bytes transferred
│                    │   │                              │     │                 │         └─────── HTTP status
│                    │   │                              │     │                 └───────────────── Protocol
│                    │   │                              │     └─────────────────────────────────── Requested resource
│                    │   │                              └───────────────────────────────────────── HTTP method
│                    │   └──────────────────────────────────────────────────────────────────────── Timestamp
│                    └──────────────────────────────────────────────────────────────────────────── identd / userid (ignored)
└───────────────────────────────────────────────────────────────────────────────────────────────── Host/IP client
```

## Roadmap

Not yet implemented, planned as future iterations:

- Logging (currently uses `print` for warnings)
- Automated tests
- HTML report output
- Packaging for distribution (`pyproject.toml`, PyPI)
- Possible refactor from a single `main.py` into separate modules (`parser.py`, `analyzer.py`, `report_generator.py`, ...), same behavior, cleaner structure

## Tech stack

Python, pandas, matplotlib, `re`, `argparse`

## Author

Sergio Boccassini

- GitHub: [boccassinisergio-afk](https://github.com/boccassinisergio-afk)
- LinkedIn: [sergio-boccassini](https://www.linkedin.com/in/sergio-boccassini)
- X: [@boccassini_ai](https://x.com/boccassini_ai)