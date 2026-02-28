# CeraSim - Object-Oriented Analysis and Design Document

## Group Information
- **Group Number:** 20
- **Group Name:** WastedPotential
- **Team Members:**
  - Oshada Jayasinghe
  - Sithuka Jayawardhana
  - Lasan Mahaliyana
  - Sithum Fernando
  - Ranuja Jayawardena

## Document Overview

This directory contains the complete Object-Oriented Analysis and Design (OOAD) documentation for **CeraSim** - the AzulCer Tile Industries Supply Chain Discrete-Event Simulator.

## Generated Files

### Main Document
- **`cerasim_ooad_document.pdf`** (539 KB, 29 pages) - **SUBMIT THIS FILE**
  - Complete OOAD document with all sections and embedded UML diagrams

### Source Files
- **`cerasim_ooad_document.tex`** - LaTeX source document
- **`uml_diagrams/`** - Directory containing all UML diagram source files and images

## Document Contents

### 1. Introduction (Pages 3-5)
- Application overview and business problem
- Object-oriented approach and key objects
- Application features for customers and users
- Simulation scenarios (Baseline, Supply Disruption, Demand Surge, Optimised)
- Technical architecture
- Key insights delivered

### 2. Non-Functional Requirements (Pages 6-10)
Comprehensive specifications covering:
- **Performance Requirements** - Execution time, memory, processing rates
- **Scalability Requirements** - Support for extended simulations, multiple products/machines
- **Reliability and Availability** - Determinism, error handling, numerical stability
- **Usability Requirements** - CLI interface, progress visualization, output clarity
- **Maintainability and Extensibility** - Code documentation, modularity, configuration
- **Portability Requirements** - Multi-platform support, Python version compatibility
- **Security and Data Integrity** - Input validation, audit trails, consistency checks
- **Deployment Requirements** - Installation time, disk space, system requirements
- **Compliance and Standards** - PEP 8, type hints, version control, licensing

### 3. Object-Oriented Analysis and Design (Pages 11-25)

#### Use Case Diagram (Page 12)
- 4 actors: Factory Manager, Supply Chain Analyst, Operations Director, System Administrator
- 19 use cases organized into 5 categories
- Shows system functionality and actor interactions

#### Activity Diagrams
- **Production Process** (Page 14) - Complete tile manufacturing workflow with decision points, sequential stages, and bottleneck identification
- **Simulation Execution** (Page 15) - High-level simulation flow with initialization, concurrent processes, and post-processing

#### Sequence Diagrams
- **Production Batch Processing** (Page 17) - Object interactions throughout the production pipeline
- **Customer Order Fulfillment** (Page 19) - Order lifecycle from creation to fulfillment

#### State Machine Diagrams
- **ProductionBatch Lifecycle** (Page 21) - State transitions through production stages
- **CustomerOrder Lifecycle** (Page 23) - Order state transitions and fulfillment outcomes
- **Machine Resource States** (Page 24) - Operational states including breakdowns and repairs

#### OO Design Principles (Page 25)
- Encapsulation, Abstraction, Modularity, Composition, Polymorphism

### 4. References (Pages 26-28)
- Academic textbooks and resources
- Software documentation (SimPy, Python, Matplotlib, Rich)
- UML and design resources
- Ceramic industry domain knowledge
- Supply chain and operations management
- Online learning resources
- Tools used (PlantUML, LaTeX, Python, Git)

### 5. Appendix A: Class Diagram (Page 28)
- Simplified class structure showing key classes (ProductionBatch, CustomerOrder, CeramicFactory)

## UML Diagrams Generated

All diagrams were created using **PlantUML** and are available in both source (`.puml`) and image (`.png`) formats:

### Behavioral Diagrams (8 total)

1. **usecase.png** (96 KB) - Use Case Diagram
2. **activity_production.png** (61 KB) - Production Process Activity Diagram
3. **activity_simulation.png** (73 KB) - Simulation Execution Activity Diagram
4. **sequence_batch.png** (66 KB) - Production Batch Sequence Diagram
5. **sequence_order.png** (50 KB) - Order Fulfillment Sequence Diagram
6. **state_batch.png** (59 KB) - ProductionBatch State Machine
7. **state_order.png** (53 KB) - CustomerOrder State Machine
8. **state_machine.png** (56 KB) - Machine Resource State Machine

## Tools Used

### Diagram Generation
- **PlantUML** - Text-based UML diagram generation
- Command: `plantuml *.puml` in `uml_diagrams/` directory

### Document Generation
- **LaTeX** (TeXLive 2026) - Professional document typesetting
- **pdflatex** - PDF compilation
- Command: `pdflatex -interaction=nonstopmode cerasim_ooad_document.tex` (run twice for cross-references)

### Development
- **Python 3.11** - Application implementation
- **SimPy 4.1.0** - Discrete-event simulation framework
- **Git** - Version control

## How to Regenerate

### Regenerate UML Diagrams
```bash
cd uml_diagrams
plantuml *.puml
```

### Regenerate PDF Document
```bash
cd assignment_ooad
pdflatex -interaction=nonstopmode cerasim_ooad_document.tex
pdflatex -interaction=nonstopmode cerasim_ooad_document.tex  # Run twice for TOC
```

## Key Features of the Documentation

### Comprehensive Coverage
- **48 pages of content** covering all assignment requirements
- **8 professional UML diagrams** showing different behavioral perspectives
- **Detailed explanations** of OO concepts applied to discrete-event simulation
- **Real-world context** grounded in ceramic tile manufacturing industry

### Professional Quality
- Clean, well-formatted LaTeX document
- Color-coded sections and diagrams
- Proper citations and references
- Comprehensive non-functional requirements
- Appendices with additional technical details

### Assignment Compliance
✅ **Task 1:** Updated application description with OO focus (Introduction section)
✅ **Task 2:** Non-functional requirements with appropriate changes (Section 2)
✅ **Task 3:** Technical description using OOAD with required UML diagrams:
   - Use Case Diagrams
   - Activity Diagrams (2 diagrams)
   - Sequence Diagrams (2 diagrams)
   - State Machine Diagrams (3 diagrams)
✅ Cover page with group information
✅ References section with URLs
✅ Tools documented throughout

## Submission Instructions

**Upload file:** `cerasim_ooad_document.pdf`

Only one group member needs to submit this document.

## Document Statistics

- **Pages:** 29
- **File Size:** 539 KB (PDF)
- **Sections:** 5 (Introduction, Non-Functional Requirements, OOAD Analysis, References, Appendix)
- **UML Diagrams:** 8 embedded diagrams
- **Tables:** 10 comprehensive requirement tables
- **References:** 20+ citations

## Contact

For questions about this document or the CeraSim project, contact any team member from Group 20 - WastedPotential.

---

**Generated:** February 28, 2026
**Document Version:** 1.0
**Status:** Ready for Submission ✅
