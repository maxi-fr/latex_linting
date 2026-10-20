---
name: thesis-writing
description: Guidelines and restrictions for writing.
disable-model-invocation: true
---

# Thesis writing

When drafting or editing a text, adhere to the following rules and restrictions.

## Structure

### STRUC-04: Narrative problem-solving arc

Tell the story of the problem and its solution rather than dumping an inventory of technical facts like a status report or codebase documentation.

### STRUC-05: Mandatory section transitions

Bridge every section into the next with bidirectional transitions: provide an opening transition that links to the previous section or overarching goal so the reader understands why each section follows the preceding one, and a consistent closing transition summarizing the section's contribution and linking to the next section or overarching objective.

## Prose and style

### PROSE-01: Concise and active prose (POEM principle)

Write according to POEM: Prägnanz (conciseness), Ordnung (logical order), Einfachheit (simplicity), Motivation (purpose). Clarity beats stylistic ornamentation. Split sentences exceeding 35 words or containing multiple nested clauses.

### PROSE-05: Consistent terminology

Always use the identical technical term for the same concept, variable, or component throughout the entire thesis. Do not cycle synonyms (such as alternating between "setpoint", "reference signal", and "command variable") for literary variety.

### PROSE-08: Eliminate AI tells and slop

Remove promotional rhetoric ("pivotal", "delve", "crucial", "testament"), generic chatbot transitions, and robotic boilerplate.

### PROSE-09: Eliminate conceptual repetition

State each concept, premise, or finding once in its dedicated context. Do not re-explain, paraphrase, or summarize previously established points across subsequent paragraphs or sections; every sentence must introduce new information or advance the argument.

### PROSE-10: Ensure cohesion and narrative flow

Avoid writing paragraphs as sequences of loosely connected, self-contained statements. Instead, develop ideas as a continuous explanation in which each sentence builds naturally on the preceding one.

- Connect related concepts: Make logical, causal, or functional relationships between ideas clear rather than merely stating facts in succession.
- Maintain thematic continuity: Introduce new concepts through their relationship to previously established ideas instead of abruptly switching subjects.
- Integrate information: Where appropriate, combine closely related statements into a unified explanation rather than treating each detail as an independent point.
- Vary sentence structure naturally: Avoid repetitive sentence patterns that create a mechanical, staccato rhythm.

## Claims and citations

### CITE-01: Universal substantiation of claims

Back every technical claim, empirical premise, or numerical parameter choice with a citation, formal proof, or experimental data. Standard mathematical steps need only a recognized keyword (such as "follows by integration by parts"). Paraphrase sources rather than using direct quotations.

### CITE-05: Common knowledge boundary

Apply the MIT common knowledge test: would a peer in your field at your academic stage know this fact without looking it up? Foundational facts (basic calculus, Ohm's law) need no citation.

## Mathematics and notation

### MATH-05: Complete relations over bare expressions

State every displayed formula as a complete relation with an operator ($=$, $\le$, $\approx$), never as a bare floating expression (write $v(t) = gt$, not just $gt$).

### MATH-10: Introduce every variable in surrounding text

Define every variable, parameter, vector element, and dummy function argument in the text immediately before or after the formula where it first appears. Defining a variable or parameter includes stating its mathematical space or domain (e.g., $A \in \mathbb{R}_{>0}$, $t \ge 0$) and dummy function arguments.
