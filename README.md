# SenseSkin AI — AI-Powered Market Analysis System

SenseSkin AI is a production-oriented AI system that integrates real-time market data with large language models to generate structured, actionable insights for CS2 skin trading.

The system combines API-based data ingestion, retrieval-augmented generation (RAG), and modular AI pipelines to analyze pricing trends, evaluate item value, and support decision-making.

---

## 🚀 Key Features

- Real-time market data integration (Steam Market API)
- Retrieval-Augmented Generation (RAG) for grounded reasoning
- Multi-factor scoring system (rarity, trend, liquidity, demand, valuation)
- Structured AI outputs for consistent analysis
- Low-latency pipeline with caching and optimized requests

---

## 🏗 System Architecture

The system is designed as a modular AI pipeline:

### 1. Data Layer
- Fetches real-time pricing and metadata via external APIs  
- Supports cached data retrieval to reduce latency  

### 2. Retrieval Layer (RAG)
- Stores and retrieves relevant market context  
- Injects structured data into LLM prompts  
- Reduces hallucination and improves response accuracy  

### 3. AI Processing Layer
- Splits tasks into:
  - Pricing analysis  
  - Trend detection  
  - Value evaluation  
- Uses structured prompting for consistent outputs  

### 4. Output Layer
- Generates:
  - Market insights  
  - Scoring breakdowns  
  - Buy / hold / avoid recommendations  

---

## 📊 Scoring System

SenseSkin AI evaluates items using a multi-factor scoring model:

- Rarity
- Condition / Wear
- Market Trend
- Liquidity
- Demand Signals
- Relative Valuation

Each factor contributes to a final score and explanation, enabling interpretable AI-assisted decisions.

---

## 🧠 AI Design

- Retrieval-augmented prompting to improve reasoning reliability  
- Structured outputs to reduce variability across responses  
- Modular pipeline to support extensibility and future agent-based workflows  

---

## ⚙️ Tech Stack

**Backend**
- Python
- FastAPI

**AI / Data**
- Claude API (LLM)
- scikit-learn (TF-IDF retrieval)
- Custom scoring engine

**Frontend**
- React (Vite)

**Infrastructure**
- REST APIs
- Local caching layer

---

## 📈 Results

- Built a scalable pipeline for real-time market analysis  
- Improved reasoning consistency through structured prompting  
- Reduced hallucination using retrieval-based context injection  
- Designed a reusable framework for AI-driven decision systems  

---

## 🖥 Example Workflow

1. User queries a CS2 skin  
2. System fetches real-time market data  
3. Retrieval layer gathers relevant context  
4. LLM analyzes pricing + trends  
5. Scoring engine evaluates item value  
6. Output includes insights + recommendation  

---

## 🔮 Future Improvements

- Agent-based multi-step reasoning workflows  
- Integration with additional marketplaces (BUFF, Youpin)  
- Advanced trend prediction using historical data  
- Portfolio tracking and personalized recommendations  

---

## 📌 Motivation

This project explores how AI systems can move beyond simple chat interfaces and operate as structured, data-driven decision engines.

The goal is to bridge real-time data, retrieval systems, and LLM reasoning into a cohesive, production-oriented workflow.

---

## 👤 Author

David Yang  
Applied AI Engineer  

- Focus: LLM systems, RAG pipelines, and real-world AI applications  
- GitHub: https://github.com/yangkaiwen2002  
