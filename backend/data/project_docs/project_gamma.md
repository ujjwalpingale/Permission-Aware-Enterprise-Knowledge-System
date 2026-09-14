# Project Gamma

**Customer:** Nexus Logistics  
**Project Manager:** Emily Rodriguez  
**Current Status:** In Progress  
**Promised Delivery Date:** October 10, 2026  

## Project Overview
Project Gamma is an IoT-powered real-time fleet tracking and notification engine designed to monitor over 5,000 active delivery vehicles for Nexus Logistics.

## Scope & Deliverables
- Real-time vehicle telemetry tracking (speed, location, fuel usage)
- Instant SMS and push notifications for route deviations
- Driver mobile app for Android and iOS
- Live interactive map dashboard for dispatch operators

## Key Milestones
- **August 15, 2026:** Driver mobile application MVP completed.
- **September 10, 2026:** GeoJSON map rendering and WebSockets telemetry pipeline completed.
- **October 01, 2026:** Load testing under 10,000 concurrent WebSocket connections.
- **October 10, 2026:** Final deployment to Nexus Logistics cloud environment.

## Technical Decisions
- GeoJSON map markers using Leaflet and Mapbox APIs.
- Redis pub/sub cluster for real-time driver telemetry broadcast.
- WebSockets fallback to HTTP long-polling for low-bandwidth cellular connections.
