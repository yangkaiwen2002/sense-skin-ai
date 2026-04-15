# SenseSkin AI

SenseSkin AI is an applied AI system that analyzes CS:GO/CS2 skins and provides intelligent insights for trading and valuation.

## Overview
This project is built as an exploration of applied AI in virtual economies. Instead of simply displaying market data, SenseSkin AI acts as an intelligent assistant that evaluates skins, explains their value, and helps users make better decisions.

## Core Idea
Traditional skin markets only show prices. SenseSkin AI goes further by answering:

- Is this skin actually worth buying?
- How rare or desirable is this pattern?
- Is the current price undervalued or overpriced?
- What factors are driving this skin’s value?

## Features
- AI-driven scoring system (float, pattern, rarity, demand)
- Retrieval-Augmented Generation (RAG) for knowledge-based answers
- Natural language Q&A ("Is this skin worth it?")
- Market signal analysis (events, updates, trends)
- Interactive UI for exploration and decision support

## My Contributions
- Designed an AI-driven evaluation system for virtual assets
- Implemented a retrieval + reasoning pipeline for answering user queries
- Built a scoring model combining multiple signals (market + intrinsic features)
- Developed frontend components for interactive analysis
- Integrated structured knowledge with LLM-based responses

## Tech Stack
- Frontend: React
- Backend: Python / FastAPI
- AI: LLM (Claude API), RAG pipeline, scoring models
- Data: Steam API + external market sources
- Infra: Local vector search / TF-IDF retrieval

## Project Structure
- `/frontend` – UI and interaction layer
- `/backend/app/rag` – retrieval and reasoning logic
- `/backend/data` – knowledge base
- `/components` – reusable UI modules

## Future Work
- Real-time market monitoring and alerts
- Personalized recommendations based on user behavior
- More advanced ML models for price trend prediction
- Multi-agent system (analysis agent + trading assistant)

## Why This Project Matters
Digital item markets behave like real financial systems but lack structured intelligence tools. This project demonstrates how applied AI can augment decision-making in such markets by combining data, reasoning, and natural language interaction.

## Notes
This is an ongoing project focused on bridging AI systems with real-world decision-making scenarios.
