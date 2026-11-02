Summarizer implementation prompt

> Historical prompt: references to `summarize.md` below now refer to
> [docs/specification.md](../docs/specification.md). The original prompt text is preserved.
> The user subsequently moved the execution record from root `PROGRESS.md` to
> [docs/development-log.md](../docs/development-log.md), superseding the original location requirement.

Implement the local webpage summarizer described in summarize.md.
Act as the coordinator and explicitly delegate suitable work to subagents.

Your goal is a working, maintainable application with tested logic and
evidence-backed verification. The final independent review must report
findings without changing files.

## 1. Scope and priorities

Read summarize.md and applicable AGENTS.md instructions before working.

Apply this override to summarize.md:
- Do not integrate or require a real local LLM yet.
- Implement a clearly labelled mock summarization provider.
- Support deterministic simulated streaming so the complete UI flow can
  be exercised.
- Keep an explicit interface through which a real provider can be added.
- Defer model-specific token budgeting and context-window handling.
  Document these as future provider requirements.
- Do not claim the mock produces meaningful summaries.

Use Python, Gradio, Playwright for Python, and Trafilatura.
Do not add HTTPX, a database, React, a separate API server, or an agent
framework without a concrete requirement.

Priority order:
1. Correct behavior and honest verification.
2. Clear boundaries and maintainability.
3. Appropriate tests.
4. Simplicity.
5. Parallel execution and cost efficiency.

Proceed autonomously with reversible implementation decisions.
Ask only when a missing decision materially blocks correct implementation.
Never invent missing requirements or claim unavailable checks passed.

## Python environment and dependency management

Use uv exclusively for Python environment and dependency management.

- Create a project-local .venv using uv.
- Declare application dependencies in pyproject.toml and development
  dependencies in its dev dependency group.
- Generate and commit uv.lock.
- Install and synchronize dependencies with uv sync.
- Run the application, tests, and quality tools with uv run.
- Never install packages globally, use sudo pip, or modify unrelated
  Python environments.
- Add .venv/ to .gitignore.

Install Playwright’s Chromium browser with:
uv run playwright install chromium

Browser binaries use Playwright’s separate cache by default; Python
packages must remain inside the project’s .venv.

The coordinator owns pyproject.toml, uv.lock, and dependency installation.
Subagents must use the shared environment and request dependency changes
through the coordinator.

Verify that uv run python resolves sys.executable to the project’s .venv.
Document setup, launch, testing, and quality-check commands using uv.

For reproducible verification and CI, use uv sync --locked and
uv run --locked so outdated dependency metadata causes an explicit failure.


## 2. Architecture

Use a lightweight adaptation of Clean Architecture where it provides
useful dependency boundaries. Avoid ceremonial layers and abstractions
that have no concrete purpose.

Separate:
- Presentation: Gradio components, events, and user-facing messages.
- Application: the summarize-page use case and orchestration.
- Core contracts: small typed data structures, provider interfaces,
  and application-level errors.
- Infrastructure: Playwright loading, Trafilatura extraction, and the
  mock summarization provider.
- Composition: configuration and construction of dependencies.

The application layer must not depend on Gradio or concrete adapters.
Pass dependencies explicitly. Keep construction at the composition root.
Use small Protocols or equivalent interfaces at boundaries that need
substitution or isolated testing.

Expected conceptual flow:
URL → load rendered HTML → extract readable text →
mock summarization stream → UI updates.

Choose a simple, coherent sync/async strategy that works with Gradio.
Verify compatibility instead of assuming framework behavior.

Requirements:
- Typed public interfaces and explicit error semantics.
- URL validation for supported HTTP/HTTPS inputs.
- Bounded page-load waits and reliable browser/resource cleanup.
- Clear handling of loading failures and empty extraction.
- Consistent streaming behavior and partial-failure handling.
- Configuration separated from business logic.
- No hidden mutable global application state.
- Page text remains untrusted source material.
- Local-only UI binding by default.
- No unnecessary frameworks, generic repositories, event buses,
  dependency-injection containers, or plugin systems.

Choose the actual package structure after inspection. Explain the
important boundaries and dependency direction briefly.
 2.1 SOLID and replaceability acceptance criteria
The key dependency direction should be:
Gradio UI → Application use case → Core contracts
                                      ↑
                        Concrete adapters implement them

Composition root constructs and connects everything.
For example:
* Replace Playwright: implement the loader interface; extraction and application logic remain unchanged.
* Replace Trafilatura: implement the extractor interface.
* Add the local LLM: implement the summarizer interface.
* Replace Gradio: build another presentation adapter that calls the same application use case.
Replacement stays easy when the new component fits the agreed contract. A fundamentally different capability may require changing that contract.
Add this section to make the requirements explicit:
## SOLID and replaceability acceptance criteria

Apply SOLID pragmatically. Do not introduce interfaces for every class.

Define small, framework-independent contracts for:
- Page loading.
- Content extraction.
- Streaming summarization.

Keep Playwright, Trafilatura, and Gradio types out of application
contracts. Use plain Python data types or application-owned structures.

Adapters must translate library-specific failures into the agreed
application error types. Preserve underlying causes for diagnostics.

Define consistent semantics for streaming, cancellation, cleanup,
and partial failures. The mock must honor the same contract expected
of future real providers.

Keep concrete adapter imports and dependency construction in the
composition root. Application logic must accept dependencies explicitly.

Verify replaceability through application tests using independent
test doubles. Application tests must run without starting Gradio,
launching a browser, or contacting an LLM.

Create reusable summarizer contract tests that run against the mock
now and can run against future providers. Test shared behavior rather
than requiring identical generated text.

During final read-only review, assess each SOLID principle and identify
dependency leaks or changes that would require unrelated modules to
be edited. Support findings with file and symbol references.

## 3. Planning and contracts before parallel work

Before delegating implementation:
1. Inspect the repository and record existing code and tests.
2. Turn the requirements into identifiable acceptance criteria.
3. Define module contracts: signatures, data types, error behavior,
   streaming semantics, resource ownership, and cancellation behavior.
4. Define file ownership and the task dependency graph.
5. Identify which checks provide evidence for each acceptance criterion.

Keep this documentation concise and reviewable.
Do not spend excessive time planning before producing working code.

The coordinator owns shared configuration, dependency files, contracts,
composition, UI integration, and conflict resolution unless explicitly
assigned otherwise.

Changes to an agreed contract require coordinator approval and
notification to affected workers before dependent implementation proceeds.

## 4. Agent orchestration

Use a coordinator/worker pattern.

Suggested assignments:
A. Web-content worker:
   Playwright loading and Trafilatura extraction, including tests.

B. Mock-provider worker:
   Mock summarizer and deterministic streaming behavior, including tests.

C. Coordinator:
   Shared contracts, application use case, Gradio UI, configuration,
   integration, documentation, and their tests.

D. Independent reviewer:
   A fresh agent after implementation and verification, with a
   read-only assignment.

Adapt this split if repository evidence suggests a simpler division.

Parallelize independent work after contracts are established.
Respect dependencies; do not parallelize tasks that require unsettled
interfaces or concurrent edits to the same files.

Use exclusive file ownership in a shared workspace. If isolated
worktrees are available and worthwhile, coordinate their integration
explicitly. Do not assume agent workspaces are isolated.

Agents must not revert other agents’ changes or edit outside their
assigned scope. Shared-file changes go through the coordinator.

Use existing relevant skills when available. Do not create a skill or
custom agent definition for every one-off task.

## 5. Model selection

Inspect the models and delegation controls actually available.
Do not invent model names, availability, costs, or capabilities.

Select models according to task difficulty:
- Lightweight model: bounded documentation, straightforward fixtures,
  mechanical edits, and simple checks with explicit acceptance criteria.
- Strong general coding model: adapter implementation, application
  logic, integration, and substantive tests.
- Strong reasoning model: architecture, async/resource-lifecycle
  decisions, ambiguous failures, and independent final review.

Use the lowest-cost available model reasonably capable of completing
each task reliably. Do not use a weak model for critical decisions only
to minimize cost, or the strongest model for every trivial task.

If model selection is unavailable, use the available model and state
that limitation. Escalate when a worker encounters ambiguity, repeated
failures, or risks beyond its assigned scope.

Keep a brief record of each delegated task, selected model when known,
and the reason for that choice.

## 6. Subagent task and communication contract

Every delegated task must include:
- Task ID and objective.
- Relevant requirements and context.
- Owned files and prohibited edits.
- Exact interfaces and dependencies.
- Acceptance criteria.
- Required verification.
- Expected handback format.
- Conditions requiring escalation.

Workers must report blockers and proposed contract changes promptly.
They must not silently expand scope or guess a dependency’s behavior.

Require this handback:

Task ID:
Status: complete | partial | blocked
Files changed:
Behavior implemented:
Acceptance criteria addressed:
Checks run:
  - Exact command
  - Result and relevant evidence
Limitations or unverified claims:
Contract changes requested:
Remaining risks or follow-up:

A worker’s completion message is a claim, not independent proof.
The coordinator must inspect changes and verify integration.

## 7. Testing requirements and integrity

Write meaningful tests for each part of the application’s logic:
- URL validation.
- Loading behavior, timeouts, and resource cleanup.
- Main-text extraction and empty-content behavior.
- Mock-provider output, streaming, and failure behavior.
- Application pipeline, error propagation, and orchestration.
- UI event logic and user-visible state transitions.
- End-to-end operation.

Use:
- Unit tests for deterministic logic.
- Adapter/integration tests for real library boundaries.
- Local HTTP fixtures for browser integration, including a page whose
  relevant content is inserted by JavaScript.
- A browser smoke test for the Gradio flow when the environment supports it.

Keep the default suite independent of public websites and real LLMs.
Use controlled fakes at external boundaries, but include integration
coverage that can detect incorrect assumptions about real libraries.
Avoid timing-sensitive sleeps where explicit synchronization works.

Do not test only happy paths or mirror the implementation.
Assert externally meaningful behavior and failure conditions.
For important failure modes, check that the test would fail if the
behavior were broken; use a small temporary mutation when practical,
then restore the implementation.

Test integrity:
- Never delete, skip, weaken, or rewrite assertions merely to make
  failing implementation pass.
- Fix implementation defects before considering test changes.
- A test may change only when evidence shows it contradicts an approved
  requirement, contains a real defect, or is nondeterministic.
- Before changing such a test, record the old expectation, why it is
  wrong, supporting evidence, and the corrected expectation.
- The coordinator must review worker-proposed test changes.
- Preserve regression coverage and report substantive test changes.

Coverage percentages are supporting evidence, not proof of correctness.
If measured, inspect uncovered application logic rather than chasing
a number with trivial tests.

Run the appropriate formatter, linter, type checker, and test suite.
Keep tooling proportionate to the project and document how to run it.

## 8. Evidence and claims

Verify third-party APIs against installed versions and authoritative
documentation where needed. Pin or constrain dependencies coherently.

For each substantive completion claim, provide appropriate evidence:
- File/symbol references for structural claims.
- Exact commands and actual results for execution claims.
- Test names for behavior claims.
- Browser observations or artifacts for UI claims.
- Official documentation references for compatibility decisions.

Distinguish:
- Implemented.
- Verified.
- Assumed.
- Blocked or unverified.

Do not fabricate command output, test results, screenshots, citations,
or model-selection details.

Do not claim “production-ready,” “fully secure,” “all edge cases,” or
similar guarantees that the evidence cannot establish.

If a check cannot run, state the exact limitation and its effect.
A passing mocked suite does not establish that a real adapter works.

## 9. Documentation and comments

Provide:
- Setup and launch instructions.
- Dependency and browser-installation instructions.
- Test and quality-check commands.
- A short architecture explanation.
- Configuration reference.
- A clear explanation of mock behavior.
- Guidance for adding a future local LLM adapter.
- Known limitations.

Use docstrings for public contracts and non-obvious behavior.
Add comments explaining decisions, constraints, lifecycle requirements,
and surprising tradeoffs. Avoid comments that merely restate code.
Use a short decision note for material architectural choices.

## Persistent progress and recovery

Maintain PROGRESS.md at the project root as the durable execution record.
The coordinator owns this file; subagents report updates to the coordinator.

Create it before implementation and update it:
- After establishing the plan and module contracts.
- After each delegated task completes or becomes blocked.
- After integration milestones and verification runs.
- Before final review and after receiving review findings.
- Before stopping or handing control back to the user.

Record:
- Objective, scope overrides, and acceptance criteria.
- Architecture decisions and agreed module contracts.
- Task IDs, dependencies, file ownership, and task status.
- Completed changes with relevant file references.
- Checks run, exact commands, results, and the code revision or state
  they verified.
- Failures, blockers, unresolved questions, and verification limits.
- Test changes and their evidence-based justification.
- Current work in progress and precise next actions.
- Final review status and findings.

Use these task statuses:
pending | in_progress | blocked | implemented | verified

Mark a task verified only when recorded evidence supports its acceptance
criteria. Distinguish implementation completion from verification.

Keep the record concise and current. Do not include secrets, raw page
content, full tool logs, or private reasoning.

Recovery procedure:
1. Read summarize.md, applicable project instructions, and PROGRESS.md.
2. Inspect the current files, Git status, and available diffs.
3. Reconcile actual repository state with the progress record.
4. Treat interrupted tasks and previously running agents as unconfirmed;
   inspect their partial changes before resuming or reassigning work.
5. Reuse valid completed work. Rerun checks when changes or uncertainty
   invalidate previous evidence.
6. Update PROGRESS.md with the reconciled state and resume the next
   unfinished task.

Do not assume PROGRESS.md alone proves completion or that background
agents survived an interrupted session.

During the final read-only review, freeze implementation files.

## 10. Implementation and verification gates

Before final review:
1. Complete implementation.
2. Review subagent changes.
3. Run relevant checks.
4. Fix implementation defects.
5. Rerun checks affected by those fixes.
6. Record the final verification results.
7. Freeze the implementation for independent review.

Do not stop after generating a scaffold or isolated modules.
Deliver an integrated application and its tests.

## 11. Final independent review: feedback only

Spawn a fresh reviewer once the implementation is frozen.

The reviewer must:
- Inspect the specification, overrides, code, tests, and evidence.
- Assess correctness, architecture, abstraction, maintainability,
  error handling, resource cleanup, test quality, and test integrity.
- Identify omissions and unsupported claims.
- Run non-mutating checks when useful.
- Avoid formatters, autofixes, snapshots updates, or commands that
  modify tracked files.
- Make no code, test, configuration, or documentation changes.

The coordinator must not modify the implementation in response to
this final review during this run. Preserve the reviewed state.
Findings are feedback for the user to decide on afterward.

Each finding must include:
- Severity.
- File and line reference.
- Concrete problem and impact.
- Supporting evidence or reproduction.
- Suggested remediation, without applying it.

If no findings are identified, say so while recording remaining
verification limits. Do not interpret that as proof of no defects.

## 12. Final delivery contract

Return a concise report containing:
1. What was implemented and how to launch it.
2. Architecture and main module responsibilities.
3. Agent assignments and actual model choices, when available.
4. Checks run and their results.
5. Acceptance criteria mapped to evidence.
6. Known limitations and unverified behavior.
7. Final independent review findings, unchanged and clearly separated.

State explicitly that the final review made no implementation changes.
