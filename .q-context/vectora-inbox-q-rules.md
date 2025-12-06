# Vectora Inbox – Q Rules

You (Amazon Q Developer) are working in the `vectora-inbox` repository.
Your goal is to help build a **simple, robust MVP** that works end-to-end, not an over-engineered system.

The human owner is a solo founder/consultant.
Vectora Inbox must stay **simple, configurable and maintainable** by one person.

---

## 1. Global AWS context

- **Region (mandatory)**: `eu-west-3` (Paris)  
  Do not use any other region unless the human explicitly asks for it.

- **AWS CLI profile (default)**: `vectora-inbox`  
  When you propose CLI commands, assume:
  - `--profile vectora-inbox`
  - `--region eu-west-3`

- **Environment for the MVP**:
  - Use a single environment: `mvp`
  - We are not setting up dev/stage/prod yet. Keep it flat and simple.

---

## 2. Naming rules (very important)

All AWS resources you create must follow these rules:

- **General prefix**:  
  - Start names with `vectora-inbox-` whenever possible.
  - Respect AWS naming rules (lowercase for buckets, etc.).

- **S3 buckets (fixed names for the MVP)**:
  - `vectora-inbox-config`
    - Purpose: canonical scopes and client config files.
  - `vectora-inbox-data`
    - Purpose: raw, normalized and matched items.
  - `vectora-inbox-newsletters`
    - Purpose: rendered newsletters (Markdown first, later HTML/PDF).

- **CloudFormation stacks (when used)**:
  - Use names like:
    - `vectora-inbox-s0-core`
    - `vectora-inbox-s0-iam`
    - `vectora-inbox-s1-engine`
  - Do not invent extra stacks unless explicitly asked.

- **Lambda functions**:
  - Main engine Lambda name: `vectora-inbox-engine`
  - Do not create additional Lambdas unless:
    - there is a business contract file in `/contracts/lambdas/`,
    - and the human has explicitly requested it.

- **IAM roles**:
  - Prefer not to hardcode `RoleName` in CloudFormation.
  - If a RoleName is needed, prefix it with `vectora-inbox-` and keep it short.
  - Example pattern: `vectora-inbox-engine-role`.

- **CloudWatch Logs**:
  - For Lambdas, use default AWS naming (e.g. `/aws/lambda/vectora-inbox-engine`).

---

## 3. Repository map (what goes where)

You must respect this mental map of the repository:

- `/infra`
  - Infrastructure-as-code only (CloudFormation/SAM/CDK).
  - No business logic here.
  - Example stacks: `s0-core` (buckets), later `s1-engine` (Lambda).

- `/src`
  - Runtime code (Lambda functions, helpers).
  - For the MVP: **a single engine Lambda** that:
    - reads normalized items from S3,
    - reads client config from S3,
    - applies matching + scoring,
    - writes a newsletter to S3.

- `/canonical`
  - Canonical, shared **business knowledge**:
    - company scopes,
    - molecule scopes,
    - technology keywords,
    - indication keywords,
    - exclusion keywords,
    - event type patterns.
  - No client-specific logic here.

- `/client-config-examples`
  - Example YAML files for client configuration.
  - They show how a real client file in S3 should look.

- `/contracts`
  - Business contracts for Lambdas and components, written in Markdown.
  - Before adding or changing a Lambda, there must be a contract here.

- `/docs`
  - Human-readable documentation (architecture, workflow, explanations).

- `/.q-context`
  - Guidance files for you (Q Developer):
    - `vectora-inbox-overview.md`
    - `vectora-inbox-q-rules.md`
    - `blueprint-draft-vectora-inbox.yaml`

---

## 4. Fundamental business rules (must always hold)

- **No client-specific logic hardcoded in code.**
  - Client-specific behavior must always come from:
    - canonical scopes (shared),
    - + client config stored in S3.

- **Canonical vs client config**:
  - Canonical = universal lists & patterns:
    - companies, molecules, technologies, indications, exclusions, event types.
  - Client config = selection + additions:
    - chooses which canonical scopes to activate,
    - can add extra companies, molecules or keywords.
  - Do not duplicate lists between canonical and client config.

- **Normalized items are the core**:
  - Every item used by the engine must have a normalized JSON structure:
    - `source_type`, `title`, `summary`, `url`, `date`,
    - `companies_detected`, `molecules_detected`,
    - `technologies_detected`, `indications_detected`,
    - `event_type`, etc.

- **Single engine Lambda principle**:
  - The MVP must work with one main Lambda:
    - `vectora-inbox-engine`.
  - This Lambda:
    - reads client config from `vectora-inbox-config`,
    - reads normalized items from `vectora-inbox-data`,
    - applies matching and scoring based on scopes,
    - assembles the newsletter and writes it to `vectora-inbox-newsletters`.

- **S3 structure (high-level)**:
  - Config + canonical:
    - `s3://vectora-inbox-config/canonical/...`
    - `s3://vectora-inbox-config/clients/...`
  - Data:
    - `s3://vectora-inbox-data/raw/<client>/<source>/<YYYY>/<MM>/<DD>/...`
    - `s3://vectora-inbox-data/normalized/<client>/<YYYY>/<MM>/<DD>/items.json`
    - `s3://vectora-inbox-data/matched/<client>/<YYYY>/<MM>/<DD>/items.json`
  - Newsletters:
    - `s3://vectora-inbox-newsletters/<client>/<YYYY>/<MM>/<DD>/newsletter.md`

---

## 5. What you must NOT do (guardrails against complexity)

- Do **not**:
  - introduce new AWS services (DynamoDB, RDS, Step Functions, EventBridge, Bedrock KB, etc.)
  - unless the human explicitly asks for it.

- Do **not**:
  - create more than one Lambda for the MVP without a clear Markdown contract in `/contracts/lambdas/`
  - and explicit confirmation from the human.

- Do **not**:
  - create resources in regions other than `eu-west-3`.

- Do **not**:
  - duplicate business logic that already lives in canonical scopes or client config.

---

## 6. How to think about the MVP

- The priority is:
  1. Make a **small but complete** engine work end-to-end.
  2. Keep the architecture minimal and understandable by a solo founder.
  3. Favor configuration-over-code for client-specific behavior.

- It is better to have:
  - one simple Lambda + three S3 buckets that really work,
  - than a complex multi-service system that is hard to debug.

Always optimize for clarity, simplicity and maintainability.
