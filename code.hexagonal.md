# Hexagonal Architecture
![[hexagonal_arch.png]]

The input request DRIVES the application to do something.
- Driving adapters are external agents (like a user via a web browser) that 'drive' the application to perform an action.
- Driving ports define how the app is used
The output response IS DRIVEN by the application itself.
 - Driven ports define how the app uses external services.

To 'wire' together the adapters and the domain services:
- The entry point of the application is where concrete adapters are instantiated and injected into domain services.

Mapping ensures the Domain remains 'clean' and only interacts with objects it defines, regardless of the underlying database technology.
The Application Service orchestrates business flow; by using a Port for the Unit of Work, it can control transactions without knowing the DB details.
The Domain should only know about business-related errors (e.g., `StorageServiceUnavailable`); the Adapter translates technical failures into these.
Using protocols instead of abc: This further decouples the Adapter from the Domain, as the Adapter only needs to implement the required methods to satisfy the type checker.
As the number of adapters grows, a DI container helps manage their lifecycles and dependencies in one single place (the Composition Root).
Complex state logic for an entity belongs within the Domain Entity itself or a Domain Service, not the Application Service.
Application Services act as the entry point to the core, coordinating how repositories are called and how entities are manipulated to satisfy a user request.
By encapsulating validation inside the Value Object, you ensure that the Domain logic only ever operates on 'valid' data, regardless of where it came from.
Value Objects should still be mapped by an adapter; their primary goal is business logic, not persistence.
-  They reduce 'Primitive Obsession' and ensure validation logic stays within the Domain. 
Using events allows the domain to signal that 'something happened' without knowing who responds to it or how (e.g., email, SMS, or logging).
- The Domain emits an event that is handled by a separate Outbound Port (e.g., an EventDispatcher).
Separating abstractions from concrete implementations in the module hierarchy is the standard Pythonic way to resolve dependency loops.
By mocking the Port, you test that the Service interacts with the interface correctly without needing a real network connection or a real API key.
Where should input validation for a web request (e.g., checking if a 'username' field is missing) ideally occur in a Hexagonal Python app?
- Inside the Driving Adapter (e.g., using a Pydantic schema in a FastAPI route). The adapter's job is to translate external input into a format the domain understands, which includes ensuring the input is well-formed.
What is the primary risk of passing a 'Session' or 'Transaction' object from an ORM directly into a Domain Service method?
- It violates the dependency rule by coupling the Domain to a specific infrastructure library. If the Domain knows about a 'SQLAlchemy Session', you can no longer test the domain or switch databases without changing the core logic.
In the context of Port signatures, why is it better to return a 'Domain Entity' instead of a 'Dictionary' from a Repository Port?
- Entities encapsulate both data and business behavior, ensuring logic isn't scattered. Domain Entities provide a rich model where business rules (methods) and data live together, preventing 'anemic' domain models.
When using a 'Fake' implementation (e.g., InMemoryUserRepository) for testing, which layer is responsible for defining this class?
- The Tests folder or a specific 'Adapters' test module. Fakes and Mocks are specialized adapters used during testing to satisfy the Port requirements without external side effects.
How should a Domain Service handle multiple sequential calls to different Outbound Ports (e.g., save to DB, then send to Kafka)?
- Using an orchestrated Use Case that manages a 'Unit of Work' to ensure consistency. A Unit of Work (UoW) ensures that all operations either succeed together or fail together, maintaining system integrity.
What is the benefit of making Domain Entities 'Persistence Ignorant'?
- It ensures the business logic doesn't change when you upgrade your database driver or switch to a Cloud API. By keeping SQL or API-specific code out of the Entity, you protect the most valuable part of your code from technology churn.
If you need to switch your application from a REST API to a Command Line Interface (CLI), which part of a Hexagonal app requires the most change?
- The Driving Adapters. You would replace the FastAPI/Flask controllers (Driving Adapters) with a library like `click` or `argparse` (new Driving Adapters).
Which pattern is commonly used to translate between Domain Entities and Infrastructure models (like SQLAlchemy classes)?
- The Mapper (or Data Mapper) Pattern. Mappers are responsible for moving data between two different objects (e.g., `from_domain` and `to_domain` methods).



### The 3 Key Parts:

1. **Domain/Core (Center)**
    - Pure business logic
    - No framework/database code here
    - Contains entities and business rules
2. **Ports (Interfaces)**
    - Define _what_ your application needs
    - Example: "I need to save users" (interface/abstract class)
    - Two types: **Input** (driving) and **Output** (driven)
3. **Adapters (Plugins)**
    - Implement _how_ things work
    - Example: "Here's how to save users to PostgreSQL"
    - Swappable implementations


In hexagonal architecture, the same concepts exist but are organized differently:

| Layered Architecture      | Hexagonal Architecture     | Location in Codebase   |
| ------------------------- | -------------------------- | ---------------------- |
| Controller                | Adapter (Primary/Driving)  | _api/_routes/          |
| Service                   | Domain/Integration         | _domain/_integrations/ |
| Repository Interface      | Port                       | _domain/_ports/        |
| Repository Implementation | Adapter (Secondary/Driven) | _adapters/             |

```
1. HTTP Request arrives
   ↓
2. API Route (_api/_routes/_work_order/_wms_perform_material_issue_routes.py)
   - Validates HTTP payload
   - Converts to domain format
   ↓
3. Domain Integration (_domain/_integrations/.../_wms_to_oracle_material_issue.py)
   - Contains business logic
   - Calls port interface (doesn't know it's Oracle!)
   ↓
4. Adapter (_adapters/_oracle_fusion_cloud_actions/.../_oracle_material_issue_action.py)
   - Implements the port interface
   - Makes HTTP call to Oracle
   - Returns domain model
   ↓
5. Response flows back up
```

