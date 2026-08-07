# Architecture Diagrams

Mermaid diagrams for the Contract Lifecycle Management (CLM) system. Each
diagram reflects the current implementation.

---

## 1. System Architecture

```mermaid
flowchart TB
    subgraph Users
        Desk[Frappe Desk<br/>System Manager · Contract Manager · Approvers]
        CP[Counterparty User<br/>External]
    end

    Desk -->|frappe.ui.form + workflow| Web[Frappe Web / Desk]
    CP -->|browser| PortalLogin[Portal Login<br/>/portal/login]
    CP -->|browser| Portal[Portal SPA<br/>/portal]

    PortalLogin -->|/api/method/login| Framework[Frappe Framework]
    Portal -->|/api/method/...portal_api.*| Framework

    Framework --> Desk
    Framework --> Web
    Web --> DocControllers[Doctype Controllers<br/>Contract · Contract Version · Approval · Signature Request]
    DocControllers -->|whitelisted methods| Services[Service Layer<br/>Contract · ContractVersion · Approval · Signature<br/>Workflow · Notification]
    Services -->|webhook dispatch| WebhookAPI[Webhook Endpoint<br/>api/documenso_webhook]
    Services --> PortalApi[portal_api.py<br/>get_session_info · get_dashboard · get_contract_detail<br/>download_document · review_contract]
    WebhookAPI -->|handle_webhook| WebhookService[WebhookService<br/>Auth · Dispatcher]
    WebhookService --> SignatureService[SignatureService<br/>process_document_completed]

    Services --> Provider[DocumensoProvider<br/>docusign_integration app]
    Provider --> HttpClient[DocumensoHttpClient]
    HttpClient -->|REST /api/v2| Documenso[Documenso API]

    Documenso -->|webhook POST| WebhookAPI
    Framework --> MariaDB[(MariaDB)]
    Framework --> Redis[(Redis)]

    PortalApi --> Framework
    SignatureService --> Framework
```

---

## 2. Database Relationships

```mermaid
erDiagram
    COUNTERPARTY ||--o{ CONTRACT : "owns"
    CONTRACT ||--o{ CONTRACT_VERSION : "has versions"
    CONTRACT ||--o{ COLLABORATOR : "has collaborators (child)"
    CONTRACT ||--o{ APPROVAL : "has approvals"
    CONTRACT_VERSION ||--o{ SIGNATURE_REQUEST : "targets"
    SIGNATURE_REQUEST ||--o{ SIGNATURE_RECIPIENT : "has recipients (child)"
    APPROVAL }o--|| CONTRACT_VERSION : "decides on"
    COUNTERPARTY {
        string name PK "CP-#####"
        string counterparty_name
        string counterparty_type
        string email
        string portal_user FK
        bool portal_enabled
    }
    CONTRACT {
        string name PK "CTR-YYYY-#####"
        string contract_title
        string counterparty FK
        string status
        date effective_date
        date expiration_date
    }
    CONTRACT_VERSION {
        string name PK "CTV-YYYY-#####"
        string contract FK
        int version_number
        bool is_current
        string document
        string status "workflow field"
    }
    COLLABORATOR {
        string user FK
        string role
        string review_status
    }
    APPROVAL {
        string name PK "APR-YYYY-#####"
        string contract FK
        string contract_version FK
        string approver FK
        string status
        string remarks
    }
    SIGNATURE_REQUEST {
        string name PK "SIG-YYYY-#####"
        string contract_version FK
        string status
        string envelope_id
        string signing_url
    }
    SIGNATURE_RECIPIENT {
        string signer FK
        string email
        int signing_order
        string status
        datetime signed_on
        string documenso_recipient_id
    }
```

---

## 3. Approval Workflow

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> UnderReview: Submit for Review
    UnderReview --> Approved: all approvals Approved
    UnderReview --> Rejected: any approval Rejected
    Rejected --> Draft: Revise
    Approved --> SignatureRequested: Request Signature
    Approved --> Superseded: Supersede
    SignatureRequested --> Executed: Complete Signing
    SignatureRequested --> Approved: Cancel Signature
    Executed --> [*]
    Superseded --> [*]
```

> Note: the version only enters `Approved` when **every** Approval record for
> the version is Approved; any single rejection sends the version to
> `Rejected`.

---

## 4. Signature Workflow

```mermaid
sequenceDiagram
    participant CM as Contract Manager (Desk)
    participant SR as Signature Request
    participant SV as SignatureService
    participant DV as Contract Version
    participant DP as DocumensoProvider
    participant D as Documenso API

    CM->>SR: Create Signature Request (Draft)
    CM->>SR: Send for Signature
    SR->>SV: send_signature_request(name)
    SV->>SV: validate version Approved + current
    SV->>SV: validate PDF {{signature,rN}} placeholders
    SV->>DP: create_document(payload, pdf)
    DP->>D: POST /api/v2/envelope/create
    D-->>DP: envelope {id}
    SV->>SR: persist envelope_id
    SV->>DP: distribute_document(envelopeId)
    DP->>D: POST /api/v2/envelope/distribute
    D-->>DP: recipients {recipientId, signingUrl}
    SV->>SR: persist recipient ids + signing_url
    SV->>DV: transition → Signature Requested
    SV->>SR: status → Pending
    Note over SR: Recipients receive signing invitations
    D-->>D: recipients sign
    D-->>SV: webhook DOCUMENT_COMPLETED
    SV->>SR: mark recipients Signed
    SV->>DV: Complete Signing → Executed
    SV->>SR: status → Completed
```

---

## 5. Counterparty Portal Flow

```mermaid
flowchart LR
    A[Counterparty opens /portal/login] --> B{Authenticate<br/>/api/method/login}
    B -- failure --> A
    B -- success --> C{Is portal user?<br/>portal_enabled + portal_user}
    C -- no --> A
    C -- yes --> D[Portal SPA /portal]
    D --> E[get_session_info]
    D --> F[get_dashboard]
    F --> G[Dashboard<br/>stat cards + contract list]
    G --> H[Contract Detail<br/>get_contract_detail]
    H --> I{current version state}
    I -- Under Review<br/>+ pending approval --> J[ApprovalCard<br/>review_contract approve/reject]
    I -- Signature Requested<br/>+ own recipient Pending --> K[SignatureCard<br/>open signing_url]
    J --> H
    K --> H
    K -.returns from Documenso tab.-> H
    H --> L[download_document]
```

---

## 6. Documenso Integration

```mermaid
sequenceDiagram
    participant SS as SignatureService
    participant P as DocumensoProvider
    participant H as DocumensoHttpClient
    participant D as Documenso API

    SS->>P: create_document(payload, pdf_content)
    P->>H: post("/api/v2/envelope/create", data, files)
    H->>D: POST /api/v2/envelope/create
    D-->>H: 200 {id, ...}
    H-->>P: parsed JSON
    P-->>SS: response dict

    SS->>P: distribute_document(envelope_id)
    P->>H: post("/api/v2/envelope/distribute", {envelopeId})
    H->>D: POST /api/v2/envelope/distribute
    D-->>H: 200 {recipients:[{recipientId, signingUrl, email}]}
    H-->>P: parsed JSON
    P-->>SS: response dict

    note over SS: metadata persisted on Signature Request
```

Configuration (`Documenso Settings`): `enabled`, `base_url`, `api_token`
(Password), `request_timeout`, `retry_count`, `retry_backoff`, `webhook_secret`
(Password).

---

## 7. Webhook Flow

```mermaid
flowchart TB
    W[Documenso webhook POST] -->|JSON body| EP[handle_webhook<br/>allow_guest POST]
    EP -->|parse + validate JSON| AUTH{WebhookAuthenticator<br/>X-Documenso-Secret<br/>hmac.compare_digest}
    AUTH -- config missing --> ERR1[raise DocumensoConfigurationError]
    AUTH -- secret mismatch/missing --> ERR2[401 Unauthorized]
    AUTH -- valid --> WS[WebhookService.handle]
    WS --> WD{WebhookDispatcher.dispatch<br/>event = payload.event}
    WD -- DOCUMENT_COMPLETED --> DC[_handle_document_completed]
    DC --> SP[SignatureService.process_document_completed]
    SP -->|externalId → Signature Request| LOAD{found?}
    LOAD -- no --> SKIP1[log warning, return]
    LOAD -- yes --> IDEM{status Completed / Cancelled / Expired?}
    IDEM -- yes --> SKIP2[log, return]
    IDEM -- no --> MARK[mark matched recipients Signed]
    MARK --> TX{can_transition → Executed}
    TX -- no --> THROW[frappe.ValidationError]
    TX -- yes --> APPLY[apply_system_action Complete Signing<br/>→ version Executed]
    APPLY --> SR[Signature Request → Completed]
    WD -- other events --> LOG[log not-yet-handled TODO]
    SR --> OK[ack status ok]
```

---

## Appendix — Desk Report / Dashboard composition

```mermaid
flowchart LR
    subgraph Reports
        R1[Contract Summary]
        R2[Expiring Contracts]
        R3[Pending Approvals]
        R4[Pending Signature Requests]
    end
    subgraph Dashboard
        N1[Total Contracts]
        N2[Executed Contracts]
        N3[Pending Approvals]
        N4[Active Signature Requests]
        N5[Executed Expiring in 30 Days]
        C1[Approvals by Status]
        C2[Contracts by Status]
        C3[Contracts Expiring Over Time]
        C4[Signature Requests by Status]
    end
    R1 -->|ref Contract| DB[(MariaDB)]
    R2 -->|ref Contract| DB
    R3 -->|ref Approval| DB
    R4 -->|ref Signature Request| DB
    N1 -->|Contract| DB
    N2 -->|Contract| DB
    N3 -->|Approval| DB
    N4 -->|Signature Request| DB
    N5 -->|Contract| DB
    C1 -->|Approval| DB
    C2 -->|Contract| DB
    C3 -->|Contract| DB
    C4 -->|Signature Request| DB
```