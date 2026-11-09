<!-- llm_wiki/raw/AI Operating System/AI Agents/Codex Browser Acceptance Governance.md -->

# Codex Browser Acceptance Governance

## Purpose

This document records the AIOS rationale for the Codex Browser acceptance
governance established after S5-D8. It is explanatory raw Wiki knowledge, not a
second normative procedure. The operational source is:

`SKILLS/codex-browser-acceptance/SKILL.md`

Architecture Center remains the final acceptance authority.

## Why D8 Required Explicit Governance

D8 showed that browser acceptance can produce several different kinds of
evidence: rendered product behavior, unavailable inspection data, normal-user
observations, and behavior specific to the Codex Browser environment. Without
an explicit disposition protocol, an automation symptom can be mistaken for a
CyberLifeBook defect, or unavailable evidence can be treated as proof of
success or failure.

The governance therefore separates product evidence from browser-helper,
sandbox, localhost, automation, and environment symptoms. It also requires
machine and user observations to remain visible when they disagree.

## D8 Browser-History Lesson

D8 recorded a Codex Browser Back/Forward condition in which the URL changed but
the rendered detail remained loading, while an independently observed normal
browser history control rendered the expected Persona and Classifier pages.
That evidence supported `CODEX-SPECIFIC BEHAVIOR`; it did not by itself
authorize a production routing fix or establish a CyberLifeBook routing defect.

This history case is why browser-history anomalies require independent product
evidence before they are classified as `PRODUCT FAIL`.

## D8 Sandbox-Account Lesson

D8 also recorded `CreateProcessWithLogonW failed: 1327` during Codex Browser
startup when the required local sandbox accounts had not been enabled. This is
a known missing-precondition condition. It must be checked before treating a
browser startup symptom as an unexplained infrastructure failure or product
failure.

The host preflight belongs to Андрей in elevated PowerShell. Codex must not
attempt that elevated operation. Once healthy preflight is established, a
subsequent helper or sandbox failure can be classified independently as
infrastructure unless application-failure evidence exists.

## Bounded User Observation

USER-OBSERVED evidence is a bounded ambiguity-resolution mechanism. Codex first
acts autonomously within the authorized acceptance scope and exhausts safe
observations. Андрей is contacted only after an actual unexpected symptom when
one small normal-browser observation can resolve a material PASS-versus-
PRODUCT FAIL ambiguity.

This does not make Андрей an interactive approval gate or a manual test
runner. Ordinary authorized actions such as Delete, Restore, filtering,
navigation, and authorized Refresh remain Codex actions.

## Evidence Discipline

`NOT OBSERVABLE` means required evidence is unavailable. It is not
`PRODUCT FAIL`. A loading symptom is not automatically a product defect. A
browser helper or bridge failure without application-failure evidence is not a
product failure.

The governance preserves the distinction between:

- valid positive browser evidence;
- sufficient product-failure evidence;
- unresolved ambiguity requiring one bounded user observation;
- infrastructure blocking reliable execution;
- unavailable evidence; and
- independently supported Codex-specific behavior.

When machine and user evidence disagree, both remain part of the record and the
discrepancy is classified rather than silently normalized away.

## Canonical Placement

The single normative operational source is:

`SKILLS/codex-browser-acceptance/SKILL.md`

This document supplies rationale and history only. It deliberately does not
copy the complete operational skill. The separation prevents drift between
instructions, preserves D8 as historical evidence, and keeps Architecture
Center's final acceptance role explicit.
