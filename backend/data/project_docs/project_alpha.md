---
account: ABC Corp
department: engineering
access_level: internal
allowed_roles: engineer,account_manager
allowed_users: 
---

# Project Alpha

**Customer:** ABC Corp  
**Project Manager:** Sarah Johnson  
**Current Status:** In Progress  
**Promised Delivery Date:** September 25, 2026  

## Project Overview
Project Alpha is focused on delivering a secure, scalable payment gateway integration and multi-currency billing portal for ABC Corp.

## Scope & Deliverables
- Payment Gateway Integration (Stripe & Credit Card processing)
- Multi-currency billing engine supporting USD, EUR, and GBP
- Merchant onboarding portal with OAuth2 authentication
- Automated refund and callback notification webhook system

## Key Milestones
- **July 15, 2026:** Design and security review completed.
- **August 20, 2026:** Core API backend integration completed.
- **September 20, 2026:** Final User Acceptance Testing (UAT).
- **September 25, 2026:** Production delivery and customer sign-off.

## Technical Decisions
- Backend built with Python FastAPI and PostgreSQL.
- Payment webhooks handled asynchronously using Celery background workers.
- Encryption at rest for merchant keys using AES-256.
