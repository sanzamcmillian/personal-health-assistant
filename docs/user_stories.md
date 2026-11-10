# Personal Health Assistant: User Stories & Specifications (v2.0)

## Product Vision & Principles
A **zero-friction, privacy-first symptom assessment assistant** designed for users needing quick health guidance at home or anywhere when away from a healthcare provider. Users complete an ultra-fast onboarding (Age, Biological Sex, and optional Country), describe their symptoms in everyday language, receive targeted conversational follow-up questions (medications, allergies, pregnancy status if applicable, chronic conditions, and onset/severity), optionally attach medical documents (PDF only) for direct in-context analysis, and receive intelligent triage suggestions on potential causes. 

If critical or emergency symptoms appear, the system immediately presents an emergency alert with a one-touch call button (`tel:911` / local emergency number), followed by nearby 24/7 facilities using free OpenStreetMap data.

### Foundational Engineering & Safety Principles
1. **Deterministic-First Safety**: Deterministic red-flag rules run on *every* message prior to any LLM call, guaranteeing zero-latency emergency escalation independent of model availability, rate limits, or safety filters.
2. **Sticky Escalation Floor**: The system retains the highest triage level reached (`highest_triage_level`). Once an emergency or high-urgency level is triggered, subsequent messages cannot downgrade it. The final level is `max(rules, LLM, highest_triage_level)`.
3. **Session-Independent Emergency Fallback**: Emergency numbers and emergency facility lookups work without an active session so that locked-out users or capacity-limited users can always access urgent emergency care.
4. **Direct Context Ingestion (No Heavy RAG)**: PDFs are processed in-memory via streamed byte chunks (zero `/tmp` disk writes) and injected directly into Gemini's 1M context window, preserving complete lab tables and reference ranges without chunking artifacts.
5. **Zero-Retention & Zero-PHI Logging**: No permanent database, no PII/PHI stored on disk. Session IDs are cryptographically random and stored strictly in `HttpOnly; SameSite=Strict; Secure` cookies that refresh on every request. Server logs capture only operational metrics.

---

## Target Persona
* **Alex (At-Home / Remote Patient)**: An individual feeling unwell or experiencing new symptoms while at home or away from their regular healthcare provider. Alex wants quick, reliable preliminary triage without having to create an account or provide permanent credentials. Alex completes an ultra-fast onboarding (Age, Sex, Country), describes their discomfort, answers conversational follow-up questions (medications, allergies, pregnancy status if applicable), and can upload a lab test PDF to get tailored health guidance.

---

## Epic 1: Frictionless Onboarding & Ephemeral Session Lifecycle

### US-1.1: Ultra-Fast Guest Onboarding with Secure Rolling Cookie
* **As a** person feeling unwell,
* **I want to** start using the assistant immediately by providing my age, biological sex, and country,
* **So that** I am not delayed by lengthy registration forms when seeking health guidance.
* **Acceptance Criteria**:
  - The welcome screen asks for:
    - Age: years ($0–125$) and optional months for infants under 2 years ($0–23$ months).
    - Biological Sex: `Male`, `Female`, `Other / Prefer not to say`.
    - Country: Dropdown or locale detection (e.g. `"US"`, `"GB"`, `"ZA"`, `"AU"`, `"CA"`), used to resolve local emergency dispatch numbers.
    - Name/Alias: Optional; never transmitted to the LLM.
  - Generates a cryptographically secure 32-byte session token stored exclusively in an `HttpOnly`, `SameSite=Strict`, `Secure` cookie.
  - The session ID is omitted from the JSON response body to prevent XSS leakage.
  - The cookie's rolling TTL is refreshed to 30 minutes on every authenticated request.

### US-1.2: Session Expiry Visibility & Keep-Alive
* **As a** user in the middle of describing complex symptoms,
* **I want** to see how much time remains in my session and extend it if needed,
* **So that** my session doesn't abruptly vanish while I am typing.
* **Acceptance Criteria**:
  - `GET /api/v1/session/status` returns `expires_at` and `seconds_remaining` *without* refreshing the TTL.
  - When less than 5 minutes remain, the UI presents a "Session Expiring Soon" prompt with an "Extend Session" button.
  - Clicking "Extend Session" invokes `POST /api/v1/session/keep-alive` to add 30 minutes.

### US-1.3: Immediate In-Flight Cancellation & Idempotent Session Wipe
* **As a** privacy-conscious user,
* **I want** clicking "End Session" to instantly cancel any running work and wipe my data,
* **So that** I don't have to wait for slow background LLM calls to finish before my session is cleared.
* **Acceptance Criteria**:
  - `POST /api/v1/session/end` sets `session.terminated = True`, cancels in-flight background tasks for that session, purges RAM, and clears the cookie.
  - Late LLM completions detect `terminated` and immediately discard their results.
  - Endpoint is idempotent: calling it on an already-expired session returns `200 OK`.

---

## Epic 2: Conversational Symptom Intake & Assessment

### US-2.1: Multi-Turn Deterministic Red-Flag Safety Check
* **As a** user who may develop critical symptoms during a conversation,
* **I want** the system to evaluate emergency red flags on *every single message* I send,
* **So that** sudden escalations (e.g., *"actually it's spreading to my jaw"*) trigger immediate emergency help without delay.
* **Acceptance Criteria**:
  - Deterministic keyword and regex rules run on *every user turn* BEFORE invoking Gemini.
  - If a red flag is detected, returns an immediate `RED` response without waiting for Gemini.

### US-2.2: Contextual Follow-Up Intake (Medications, Allergies, Pregnancy Status, Chronic Conditions)
* **As a** user who has described my symptoms,
* **I want** the assistant to ask tailored conversational follow-up questions about my medications, allergies, pregnancy status, and chronic conditions,
* **So that** the assessment accounts for crucial contraindications and risk factors.
* **Acceptance Criteria**:
  - The assistant conversationally checks:
    - **Pregnancy Status**: Conditionally prompted if female or other aged 12–55. (An answer of "unsure" is treated conservatively as `possible`).
    - **Current Medications**: Distinguishes "takes no medications" from "medications listed" or "unknown", with negation handling (e.g., recognizing *"I'm not taking ibuprofen"*).
    - **Known Allergies**: Distinguishes "no allergies" from "allergies listed" or "unknown".
    - **Chronic Conditions**: Distinguishes "none" from "listed" (e.g. diabetes, hypertension, asthma).
    - **Symptom Dynamics**: Onset, duration, and pain score (1–10).
  - List sizes are capped at 10 items, with max 50 chars per item to prevent prompt ballooning.

### US-2.3: Structured Triage Assessment & Sticky Escalation Floor
* **As a** user,
* **I want** the assistant to provide a structured triage recommendation that adheres to clinical safety guardrails,
* **So that** I receive reliable, non-conflicting medical guidance.
* **Acceptance Criteria**:
  - Output conforms to OpenAPI-compliant JSON with:
    - `triage_level`: `GREEN`, `YELLOW`, `RED`.
    - `disposition`: `CALL_AMBULANCE_NOW`, `EMERGENCY_ROOM_IMMEDIATELY`, `URGENT_CARE_TODAY`, `PRIMARY_CARE_48H`, `SELF_CARE_MONITOR`.
    - `assessment_status`: `NEEDS_MORE_INFO` (if still conducting intake) or `FINAL`.
    - `possible_causes`: Array of objects with `name` and `explanation`.
    - `warning_signs`: Array of specific red flags that mandate immediate emergency evaluation if they develop.
  - **Sticky Escalation Floor**: Final triage level = `max(rules, LLM, session.highest_triage_level)`.
  - **Medication Guardrail**: Output is audited; statements directing the patient to *"stop taking [medication]"* or giving specific pharmaceutical dosage adjustments are rejected and sanitized.

### US-2.4: Severe Vignette Calibration
* **As a** patient reporting severe acute abdominal pain (7/10),
* **I want** the system to triage this as an immediate emergency rather than a routine visit,
* **So that** life-threatening surgical conditions (appendicitis, ectopic pregnancy, ovarian torsion) are evaluated same-day in an emergency department.
* **Acceptance Criteria**:
  - Acute lower abdominal pain rated $\ge 7/10$ in reproductive-aged patients triages to `RED` / `EMERGENCY_ROOM_IMMEDIATELY`.

---

## Epic 3: Optional In-Memory Document Ingestion & Verified Citations

### US-3.1: Streaming In-Memory PDF Upload with Threadpool Extraction
* **As a** user uploading a medical report (lab test, prescription, doctor note),
* **I want** my document processed securely in memory without blocking the server,
* **So that** large uploads don't freeze the application or leave disk traces.
* **Acceptance Criteria**:
  - Enforces the 10MB limit *while streaming* bytes, terminating early if exceeded (`413 FILE_TOO_LARGE`).
  - PyMuPDF opens the in-memory stream in a threadpool (`asyncio.to_thread`) with an `asyncio.Semaphore(3)` capping concurrency.
  - Inspects page count before text extraction; rejects PDFs $> 10$ pages (`400 PAGE_LIMIT_EXCEEDED`).
  - Detects scanned PDFs by requiring an average of $\ge 50$ characters per page across the document (`422 SCANNED_DOCUMENT`).
  - Filenames are sanitized (stripped of directory separators, HTML/XML tags).

### US-3.2: Document Removal
* **As a** user who uploaded the wrong document,
* **I want** to delete an attached PDF from my session,
* **So that** I can remove it without restarting my entire conversation.
* **Acceptance Criteria**:
  - `DELETE /api/v1/documents/{document_id}` removes the document from the active session.

### US-3.3: Direct-to-Context Ingestion & Server-Side Citation Verification
* **As a** user referencing an uploaded medical report,
* **I want** the assistant to cite exact snippets and page numbers verified by the server,
* **So that** hallucinated page numbers or phantom quotes are never displayed.
* **Acceptance Criteria**:
  - Text is injected directly into Gemini's context window under `<user_provided_document filename="..." page="...">`.
  - Server verifies that `citation.snippet` literally exists as a case-insensitive substring on the cited page of the specified document. Citations failing this check are discarded.

---

## Epic 4: Session-Independent Emergency Escalation & Geolocation

### US-4.1: Instant Emergency Alert & Static Fallback Numbers
* **As a** user in a medical emergency,
* **I want** emergency numbers and one-touch call buttons to display immediately, even if the server is at full capacity,
* **So that** I am never locked out of emergency guidance.
* **Acceptance Criteria**:
  - Emergency phone numbers and a "Call Now" button are statically bundled in the frontend and dynamically backed by the server's country table (`911` for US/CA, `999/112` for UK, `10177/112` for ZA, `000` for AU, `112` global).
  - Displays immediately when `triage_level == RED` without waiting for external API calls.

### US-4.2: Decoupled Emergency Facility Query with Spatial Caching
* **As a** user needing an emergency room,
* **I want** to find nearby 24/7 facilities without requiring an active session,
* **So that** facility lookup is fast and universally available.
* **Acceptance Criteria**:
  - `POST /api/v1/emergency/facilities` accepts coordinates (`latitude`, `longitude`) or location search (`city`, `postal_code`, `country_code`).
  - Coordinates are rounded server-side to 2 decimal places ($\approx 1.1\text{km}$) before querying.
  - Results from OpenStreetMap Overpass are cached in memory for 1 hour per $0.05^\circ \times 0.05^\circ$ grid cell.
  - Response distinguishes facility types (`hospital`, `urgent_care`), flags `has_emergency_department`, sets `hours_verified: false`, and includes straight-line distance.
