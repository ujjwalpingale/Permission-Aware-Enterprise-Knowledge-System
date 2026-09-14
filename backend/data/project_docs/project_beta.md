# Project Beta

**Customer:** Acme Global  
**Project Manager:** Michael Chen  
**Current Status:** Planning  
**Promised Delivery Date:** November 15, 2026  

## Project Overview
Project Beta aims to build an executive Cloud Analytics Dashboard with real-time metric collection, data visualization, and scheduled automated CSV/PDF report generation.

## Scope & Deliverables
- Real-time cloud metrics dashboard
- Customizable widget grid for executive user roles
- Scheduled export runner (Daily, Weekly, Monthly reports)
- High-volume log data ingestion pipeline

## Key Milestones
- **August 30, 2026:** Requirement gathering and data schema specification completed.
- **September 25, 2026:** System architecture and database design sign-off.
- **October 30, 2026:** Beta release for internal dogfooding.
- **November 15, 2026:** General Availability (GA) delivery for Acme Global.

## Technical Decisions
- React 18 frontend with Recharts visualization library.
- PostgreSQL analytical store with indexed `created_at` timestamp metrics.
- Apache Spark batch job processor for aggregated historical reports.
