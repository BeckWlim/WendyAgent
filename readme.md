# Wendy-Agent

## Introduction

This project is a **Spring Cloud–based intelligent agent backend**, designed to support distributed microservices, modular deployment, and AI-driven decision-making.

It provides foundational infrastructure for agent management, authentication, WebSocket communication, and inter-service coordination—enabling scalable, intelligent backend systems.

---

## Features

- ⚙️ **Spring Cloud Architecture** — Modular microservices with unified configuration and service discovery.
- 🔐 **JWT Authentication** — Centralized identity management and secure token-based authentication.
- 🌐 **Gateway Routing** — API routing and global access control via Spring Cloud Gateway.
- 💬 **WebSocket Communication** — Real-time bidirectional interaction for agent coordination and event streaming.
- 🧩 **Common Service Layer** — Shared utilities for persistence, caching, and message handling.
- 🤖 **Agent Core Module** — Implements agent lifecycle, task logic, and distributed coordination.

## Startup

```shell
mvn clean package
mvn spring-boot:run
```
