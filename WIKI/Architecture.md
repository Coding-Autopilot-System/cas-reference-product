# Architecture

The Reference Product shows how to integrate determinism with non-deterministic AI agents securely.

## Identity & Execution Flow

\\\mermaid
graph TD;
    External[External Event] --> Gateway[API Gateway]
    Gateway --> Auth[Managed Identity Auth]
    Auth --> Workflow[Deterministic Core Workflow]
    Workflow --> Contract[Emit CAS-Contract Event]
    Contract --> Foundry[Microsoft Foundry Adapter]
    Foundry --> Agent[Next Gen Agent Invocation]
    Agent -->|Response| DB[(State Store)]
\\\

## Microsoft Foundry Next Gen Agents
By isolating the agent execution through the Foundry Adapter, we ensure that hallucination or failure is contained, and the deterministic core remains pristine.
