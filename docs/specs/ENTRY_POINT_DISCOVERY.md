# Entry Point Discovery Plan

## **Executive Summary**

Implement intelligent discovery of transactional "entry points" in codebases - the logical starting points for navigating user-action-driven logic flows. Focus on server technologies (Node.js/JavaScript, C#, potentially others) with pattern-based recognition and semantic overlays.

## **Core Concepts**

### **Entry Points Defined**
System entry points are code elements that:
- Represent **user-triggered actions** (API requests, button clicks, form submissions)
- Initiate **transactional workflows** (database operations, business logic)
- Serve as **navigation starting points** for understanding "what happens when"
- Enable **CQRS-style analysis** (Command/Query separation)

### **Discovery Strategy Levels**

#### **1. Declarative Configuration (Manual/Hybrid)**
Human-curated semantic definition of known entry points. Fastest to implement, high value.

#### **2. Pattern Recognition (Automatic)**
AST-grep based pattern matching for common server idioms. Scalable but language-specific.

#### **3. Hybrid Approach (Recommended)**
Pattern discovery + manual curation for quality and coverage.

---

## **Phase 1: JavaScript/Node.js Support**

### **Pattern Recognition Rules**

#### **Web Framework Routes (Express, Fastify, Hapi)**
```javascript
// Pattern: method(...) as route handlers
ast-grep -p 'app.$METHOD("/$PATH", $HANDLER)' -l js --lang js
ast-grep -p 'router.$METHOD("/$PATH", ($PARAMS) => { $$$ })' -l js

// Results:
// - Identified as entry points with paths and methods
// - Extract HTTP verb + URL pattern
// - Infer transaction semantics from path structure
```

#### **API Controller Patterns**
```javascript
// Class-based controllers
ast-grep -p 'class $CONTROLLER { $METHOD($REQ, $RES) { $$$ } }' -l js

// CQRS-style command handlers
ast-grep -p '@CommandHandler($COMMAND) async handle($CMD) { $$$ }' -l ts

// Service method patterns
ast-grep -p 'async $METHOD($REQUEST) { await this.$DOMAIN_OPERATION($REQUEST); }' -l js
```

#### **Transactional Microservices**
```javascript
// Service boundaries
ast-grep -p 'export const $SERVICE = { $METHOD: async ($PARAMS) => { $$$ } }' -l js

// Message queue handlers (RabbitMQ, SQS)
ast-grep -p '$QUEUE.consume('$QUEUE_NAME', async ($MSG) => { $$$ })' -l js
```

### **Semantic Classification**

#### **Command Patterns** 🟡
- Database writes (`INSERT/UPDATE/DELETE`)
- Side effects (emails, notifications)
- State mutations
- External API calls with side effects

#### **Query Patterns** 🔵
- Database reads (`SELECT`)
- External API calls (read-only)
- Data aggregation/computation
- Non-mutating operations

#### **Event Patterns** 🟣
- Asynchronous operations
- Pub/Sub messaging
- Event sourcing patterns

---

## **Phase 2: C# Support (.NET Core/WebAPI/WCF)**
**Note:** We'll expand to F# and VB.NET later if needed.

### **Pattern Recognition Rules**

#### **WebAPI Controllers**
```csharp
// ASP.NET Core controllers
ast-grep -p '[Http$VERB("$URL")] public async Task<IActionResult> $ACTION($PARAMS)' -l csharp

// API action methods with routing
ast-grep -p 'public IActionResult $METHOD([From$SOURCE] $MODEL model)' -l csharp
```

#### **WCF Services**
```csharp
// WCF contract interface + implementation
ast-grep -p '[ServiceContract] interface $CONTRACT' -l csharp
ast-grep -p '[OperationContract] $METHOD($PARAMS);' -l csharp

// Implementation pattern
ast-grep -p 'public class $SERVICE : $CONTRACT { public async Task $METHOD($PARAMS) }' -l csharp
```

#### **Azure Functions**
```csharp
// Function triggers
ast-grep -p '[FunctionName("$NAME")] public static async Task<IActionResult> Run([HttpTrigger]$AUTH Type auth)' -l csharp
ast-grep -p '[QueueTrigger("$QUEUE")] public static void ProcessMessage($MSG msg)' -l csharp
```

#### **CQRS with MediatR**
```csharp
// MediatR request handlers
ast-grep -p 'public class $HANDLER : IRequestHandler<$REQUEST, $RESPONSE>' -l csharp

// Command vs Query separation
ast-grep -p 'public record $COMMAND : IRequest' -l csharp  // Command
ast-grep -p 'public record $QUERY : IRequest' -l csharp    // Query
```

### **Transactional Inference**

#### **EF Core Transaction Scope Detection**
```csharp
ast-grep -p 'using var transaction = await _context.Database.BeginTransactionAsync(); $$$ await _context.SaveChangesAsync()' -l csharp

// Repository pattern transactions
ast-grep -p 'await _repository.SaveAsync($ENTITY);' -l csharp
```

---

## **Phase 3: UI/State Management Integration**

### **Entry Point Model**

```typescript
interface EntryPoint {
  id: string;
  name: string;
  description?: string;
  type: 'api' | 'command' | 'query' | 'event' | 'service';
  language: string;
  filePath: string;
  startLine: number;
  category: 'auth' | 'payment' | 'cart' | 'user' | 'notification' | 'admin';
  importance: 'critical' | 'important' | 'normal' | 'optional';

  // SMART metadata (inferred/discovered)
  httpMethod?: HttpMethod; // GET, POST, PUT, DELETE
  urlPattern?: string;     // /api/users/{id}
  transactionType?: TransactionSemantic; // read, write, mixed
  dependencies: string[];  // Linked graph node IDs
  callChain: string[];     // Precomputed main flow
}

// UI State Management
interface EntryPointStore {
  entryPoints: EntryPoint[];
  categories: CategoryStats[];
  discoveryStatus: 'idle' | 'discovering' | 'complete';
  selectedCategory?: string;
  searchQuery: string;

  // Actions
  discoverEntryPoints(): Promise<void>;
  setCategory(category: string): void;
  searchPoints(query: string): void;
}

// Visualization
interface NavigationFlow {
  entryPoint: EntryPoint;
  steps: NavigationStep[];
  transactionSemantics: TransactionSemantic[];
}

interface NavigationStep {
  nodeId: string;
  action: string; // "process_payment" -> "validate_card" -> "charge_issuer"
  type: 'sync' | 'async' | 'conditional' | 'error';
  confidence: number; // 0-1 based on call chain analysis
}
```

### **Discovery Pipeline**

```typescript
// Phase 1: Pattern-based discovery
class EntryPointDiscovery {
  async discover(lang: SupportedLanguage, config: DiscoveryConfig) {
    // AST-grep pattern matching
    const rawPatterns = await this.runAstGrep(lang, config);
    const structuredPoints = this.parseHighLevel(rawPatterns);

    // Phase 2: Graph correlation
    const correlatedPoints = await this.correlateWithGraph(structuredPoints);

    // Phase 3: Transaction classification
    const classifiedPoints = this.classifyTransactions(correlatedPoints);

    // Store in Pinia store
    this.store.applyDiscoveredPoints(classifiedPoints);

    return classifiedPoints;
  }
}
```

---

## **Technical Implementation**

### **AST-Grep Integration**

#### **Language Support Matrix**
| Language | Status | Patterns | Confidence |
|----------|---------|----------|------------|
| JavaScript | ✅ Phase 1 | Web frameworks, Express | High |
| TypeScript | ✅ Phase 1 | Generic JS patterns | Medium |
| C# | 🔄 Phase 2 | ASP.NET, WCF, Azure | High |
| Python | 📋 Future | Django, FastAPI | Medium |
| Java | 📋 Future | Spring Boot | Medium |

#### **Pattern Execution**
```bash
# Discover Express routes in project
ast-grep -p 'router.$METHOD("$PATH", ($PARAMS) => { $$$ })' \
  -l js \
  -r '{"type": "api_route", "method": "$METHOD", "path": "$PATH"}' \
  --format json \
  ./src > api_routes.json

# Find CQRS commands
ast-grep -p 'class $COMMAND : IRequest' -l csharp \
  -r '{"type": "cqrs_command", "name": "$COMMAND"}' \
  ./src > cqrs_commands.json
```

### **Configuration Overlay System**

#### **Semantic Enhancement**
```json
{
  "entry_points": {
    "/api/orders": {
      "type": "api_route",
      "category": "ecommerce",
      "importance": "critical",
      "description": "Order placement transaction",
      "transaction_semantic": "write_payment",
      "business_context": "Revenue generation"
    },
    "/api/users/register": {
      "type": "api_route",
      "category": "auth",
      "importance": "critical",
      "description": "User account creation",
      "transaction_semantic": "write_userdata",
      "compliance_requirements": ["gdpr", "privacy_policy"]
    }
  },

  "categories": {
    "ecommerce": {
      "display_name": "E-commerce",
      "priority": 1,
      "icon": "🛍️"
    },
    "auth": {
      "display_name": "Authentication",
      "priority": 2,
      "icon": "🔐"
    }
  }
}
```

#### **Dynamic Configuration**
- **Project-specific overlays** loaded from `.codegraph/config.json`
- **User preferences** stored in browser localStorage
- **AI-enhanced** descriptions and categorizations
- **Team-shared** business context annotations

---

## **UI Components**

### **Entry Point Browser**
```html
<!-- Entry points grouped by category -->
<div class="entry-point-browser">
  <!-- Category tabs -->
  <div class="categories-nav">
    <button class="tab" data-category="auth" data-count="3">
      🔐 Auth (3)
    </button>
    <button class="tab active" data-category="ecommerce" data-count="12">
      🛍️ E-commerce (12)
    </button>
  </div>

  <!-- Entry point grid -->
  <div class="entry-points-grid">
    <div class="entry-point-card" onclick="explore(this)">
      <div class="card-header">
        <h3>POST /api/orders</h3>
        <span class="badge badge-critical">Critical</span>
      </div>
      <p>Customer order placement with payment processing</p>
      <div class="card-footer">
        <span class="language">JavaScript</span>
        <span class="method">Write Transaction</span>
      </div>
    </div>
  </div>
</div>
```

### **Transactional Flow Visualizer**
```html
<!-- Visualize transaction flow from entry point -->
<div class="transaction-flow">
  <div class="flow-header">
    <h2>Order Payment Transaction Flow</h2>
    <p class="transaction-semantic">Revenue-critical write operation</p>
  </div>

  <div class="flow-steps">
    <div class="step" data-type="api">
      <span class="step-icon">🌐</span>
      <div class="step-content">
        <h4>API Request</h4>
        <p>POST /api/orders with payment data</p>
      </div>
    </div>
    <div class="step" data-type="validation">
      <span class="step-icon">✅</span>
      <div class="step-content">
        <h4>Payment Validation</h4>
        <p>Validate card details, check fraud</p>
      </div>
    </div>
    <div class="step" data-type="db-write">
      <span class="step-icon">💾</span>
      <div class="step-content">
        <h4>Order Persistence</h4>
        <p>Save order + payment record atomically</p>
      </div>
    </div>
  </div>
</div>
```

---

## **Future Expansions**

### **Markup Languages (XAML, HTML)**
- **UI Action Entry Points**: Form submissions, button clicks
- **Rendering Contexts**: Component initialization, data binding
- **Navigation Triggers**: Route changes, modal opens

### **Advanced Pattern Recognition**
- **Machine Learning Classification** of entry point types
- **Graph Neural Networks** for call chain prediction
- **Natural Language Processing** for documentation correlation

### **Enterprise Features**
- **Data Flow Analysis**: Beyond call graphs to data transformation tracking
- **Security Analysis**: Identify security-sensitive entry points
- **Compliance Mapping**: GDPR, HIPAA data flow tracking

---

**This plan creates intelligent discovery and navigation of transactional workflows, enabling developers to explore "who calls what and how" in complex applications, especially those following CQRS and microservice patterns.**</content>
<parameter name="file_path">docs/entry-point-discovery-plan.md