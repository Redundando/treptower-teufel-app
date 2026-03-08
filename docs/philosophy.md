# Philosophical Foundation

**Treptower Teufel Club App / Member Backend**  
*What we are building and why.*

---

## 1. Purpose of This Document

This document captures the **why** behind the project: the product idea, architectural philosophy, and the principles that guide technical and product decisions. It serves as a long-term reference so that:

- The rationale for past decisions remains clear
- The overall system intent is understood
- What is deliberately **not** finalised yet stays explicit

---

## 2. Starting Point: The Current Landscape

The tennis club today relies on several **separate systems** that do not talk to each other:

### NetXP (Verein)

Used for classic club administration:

- Member data
- Accounting
- Invoicing
- Direct debit / collections

There is dissatisfaction with NetXP. Replacing it with a better tool later is a real option.

### eBuSy

Used for day-to-day operations:

- Court bookings
- Hall bookings
- Group training sessions

**Upside:** eBuSy works well and exposes a good API.  
**Downside:** In some areas, both frontend and backend are not informative enough.

### Website

The current public site is a static WordPress installation.

---

## 3. Target Vision

We are building **our own application** that:

- **Aggregates** information from existing systems
- **Adds** its own logic and data models
- **Improves** admin interfaces and member-facing information
- **Exposes** APIs for the website or future app

In short:

> **An integration, analysis, and application layer on top of NetXP (or a future replacement) and eBuSy.**

We are not rebuilding everything from scratch. We are building the layer that makes the best use of what already exists and fills the gaps.

---

## 4. Core Architectural Principle

**Do not replace NetXP and eBuSy overnight.**

Instead, proceed in phases:

### Phase 1: Overlay / Integration Layer

Our system sits **on top** of the existing systems. It:

- **Reads** data from them
- **Stores** its own supplementary data where needed
- **Provides** better views and workflows

### Phase 2: Own Workflows

We add workflows that the current tools do not support well, for example:

- Digital recording of voluntary work hours
- Approval workflows for admins
- Trainer views for group participants
- Reports and analytics
- Better member-facing views

### Phase 3: Own Source of Truth (Selected Areas)

Over time, we can make our system the **authoritative** source for specific domains, such as:

- Work hours
- Membership applications
- Internal roles and status
- Course and group-training logic

### Phase 4: Partial or Full Replacement (Much Later)

Only in a later stage might we consider:

- Replacing NetXP in part or entirely
- Complementing or partly replacing eBuSy in certain areas

This is explicitly **not** the short-term goal.

---

## 5. Why These First Use Cases

Two early use cases were chosen as high-value, low-risk starting points:

### Work-Hours Module

Members must complete a defined number of voluntary work hours per year (e.g. 5). We want to:

- Record hours digitally
- Let members see their status online
- Let admins review and approve hours

**Why this first:** Clear process, clear benefit, low risk, and a good place to own real business logic.

### Trainer View for Group Trainings

Trainers should see exactly who has booked which group trainings in eBuSy.

**Why this first:** High operational value, close to the eBuSy API, limited scope, and immediate improvement for daily work.

---

## 6. Technical Philosophy

### Not WordPress as the App Core

- **WordPress** stays for: public website, content CMS, static/editorial content.
- **The new app** is: a separate application on a subdomain, with its own API, database, and frontend.

### Backend: FastAPI

- API-first
- Python-based
- Clear data models
- Good fit for roles, permissions, and admin workflows
- Straightforward integrations with external systems
- Suitable for growing business logic

### Database: PostgreSQL

Club data is highly relational (members, status, groups, bookings, trainers, work hours, approvals, roles, billing). Therefore:

- **SQL:** yes  
- **PostgreSQL:** yes  
- **NoSQL as primary database:** no  

### Frontend: Svelte or SvelteKit

- Not WordPress as the app platform.
- WordPress plugins are acceptable only for small widgets or displays.
- For the real app: **Svelte or SvelteKit**, decoupled from the backend. The exact choice (plain Svelte + Vite vs SvelteKit) is intentionally left open for the first iteration.

### No Docker Requirement

Docker is **not** mandatory. A simple stack is acceptable:

- Ubuntu, systemd, FastAPI, PostgreSQL, Node, reverse proxy, deploy scripts.  
Docker can be added later if needed.

---

## 7. Hosting Philosophy

### European / German Control

It was explicitly agreed:

> **The club’s systems should, as far as possible, remain in European / German hands.**

That is why **Hetzner** was chosen: control, clarity, and alignment with this requirement.

### Staging Before Production

We agreed:

> **Do not build production first; set up staging properly first.**

This allows us to:

- Practice hosting and deployment
- Validate backend and frontend structure
- Establish a clear path: **local → staging → production**

### Simplicity on Staging

Staging is kept deliberately simple: one server, no complex release model, no unnecessary moving parts. A more rigorous production architecture can follow later.

---

## 8. How We Operate

- **Infrastructure** (OS, packages, DB, users, firewall, directories) is set up **manually** on the server.
- **Application** (backend, frontend, configs, scripts) is developed **locally**, versioned in Git, and brought to the server **via deploy**.

So: **server for infrastructure; app via Git and deploy.**

---

## 9. Summary Principles

| Area        | Principle |
|------------|-----------|
| **Architecture** | Do not replace NetXP and eBuSy immediately; build an overlay and integration layer first; add own workflows in small, high-value areas. |
| **Product**      | Work-hours module and trainer view are strong MVP building blocks. |
| **Tech**         | FastAPI, PostgreSQL, no WordPress as app core, Docker optional. |
| **Hosting**      | Hetzner; European/German infrastructure; staging first, kept simple. |
| **Operations**   | Infra on server; application developed locally and deployed. |

---

*This document reflects the philosophical foundation as of project start. Decisions about staging and production are documented in separate, more technical documents.*
