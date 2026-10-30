---
name: notation-design
description: Develop coherent manuscript notation interactively and record the agreed conventions in Markdown.
disable-model-invocation: true
---

# Notation design

Work with the author to harmonize notation across a paper or thesis. Invocation
starts a conversation grounded in the manuscript; the deliverable is a Markdown
notation agreement when the author asks to gather, finish, or export the decisions.
Edit manuscript sources only when separately requested.

## Establish the evidence

Read the manuscript root and its included chapters, notation tables, relevant
macros, and mathematical figure sources. If the manuscript or requested scope is
missing, ask for it. Record inaccessible or unfinished sections as coverage limits.
For supplied excerpts, use the excerpt as evidence and state its limited scope;
cite file locations only when available, without inventing filenames or lines.

Read [thesis-review](../thesis-review/SKILL.md) and its
[thesis-writing](../thesis-writing/SKILL.md) reference as rule documents, without
starting their separate workflows. Apply their relevant criteria to proposals:
mathematical type and typography, index typography, local definitions and domains,
complete displayed relations, consistent terminology, and readable expressions.
Keep the rules in those sources rather than copying their wording here.
When the author's chosen convention differs from a rule, identify the exact rule
and record the author's decision as a scoped exception. Preserve prior decisions.

Build a working inventory of each symbol's meaning, domain or shape, units,
selectors, transformations, and source locations. Trace the same concept across
chapters before equating or separating symbols. Equal numerical values do not
establish conceptual identity.

This pass is ready for discussion when each suspected conflict has actual source
examples and the conceptual distinction at stake can be explained. Show a few
useful examples, not the entire inventory.

## Harmonize through concrete rounds

In each round:

1. Bring a demonstrated flaw or unresolved design choice, citing source locations
   and explaining what a reader could misunderstand. Distinguish a conflict from
   harmless local reuse or an explicitly defined convention.
2. Offer concrete alternatives with a recommendation and their tradeoffs. Change
   the organizing convention when that solves the problem better than renaming
   individual symbols. Consider removing unnecessary notation as an alternative.
3. Work through representative equations under the proposal. Check shapes,
   physical units, time origins, selector roles, and related usages elsewhere.
   Include a cross-chapter example when the proposal is meant to be global.
4. Ask the author about the decision that matters. Treat suggestions as proposals
   until accepted; distinguish acceptance of a pattern from acceptance of every
   candidate symbol. Incorporate corrections without reopening settled choices.
5. Trace the accepted change through the inventory, then bring the next concrete
   weakness. Let the author steer the order and depth of the discussion.

Prefer a focused question or a comparison table over a questionnaire. Continue
useful inspection between rounds. Do not close the session merely because one
family is consistent or a predetermined number of issues has been discussed.

When unfamiliar disciplinary practice or a disputed convention needs grounding,
consult [research](references/research.md), then follow its primary-source links
or search further as needed. Explain whether advice is a disciplinary convention,
an author's recommendation, or a choice for this manuscript. Sources inform the
discussion; they do not override the author's settled preferences.

## What to investigate

Use these lenses against the actual manuscript; they are not a fixed questionnaire
or a universal symbol assignment.

- **Identity and families:** unrelated meanings sharing a letter; one concept
  acquiring unrelated names; related representations whose notation hides their
  relationship. Evaluate the complete written symbol, including function
  application, rather than banning every shared glyph mechanically.
- **Counts and dimensions:** physical entity counts, coordinate dimensions,
  history lengths, prediction and loss extents, layer widths and depths. Preserve
  conceptual distinctions and define relationships even when counts coincide.
- **Selectors:** time, component, layer, training example, and iteration;
  subscripts versus parenthesized superscripts versus function arguments; order,
  origin, range, and physical clock. A discrete selector can select a real-valued
  input. Retain useful visual separation rather than forcing every role below.
- **Transformations:** prediction, estimation, standardization, smoothing, means,
  quantization, and optimization. Each marker should convey distinct information.
  Specify averaging domains and transformation order where these change meaning.
- **Collections and entries:** whole arrays versus coordinates; constituents
  versus their collection; stacking and reshaping versus information-changing
  transformations. Explore preserving the base letter and omitting a selector
  to denote collection, with shape and order defined once. Prose may be enough
  for flattening; a new symbol or vectorization operator needs a concrete benefit.
- **Typography:** scalar/vector/matrix/tensor distinctions, Latin/Greek choices,
  and case or font variants for related representations. Check manuscript macros
  and font support before recommending a visual distinction. Resolve review-rule
  conflicts explicitly rather than disguising them as compliance.

Prioritize ambiguity that occurs in the manuscript. Hypothetical combinations
of selectors alone are insufficient grounds for redesigning readable notation.

## Produce the Markdown agreement

When the author requests a record, write it to their chosen path, or a sensible
Markdown location beside the manuscript, and link the result. A request to gather
decisions can capture an unfinished session: preserve open questions rather than
silently choosing answers or claiming completion of the notation design.

Make the document usable without the chat. Include:

- Manuscript scope and coverage limits.
- Accepted conventions, their meanings, and representative equations.
- A current-to-proposed mapping, with domains or shapes where needed. Mark
  tentative names separately from accepted patterns and final assignments.
- Relationships between counts, representations, collections, and transformations.
- Explicit exceptions to review rules and the author's rationale.
- Unresolved choices and affected source locations; cite external guidance only
  where it supports a decision or explains a tradeoff.

Before delivery, check the record against the conversation: every accepted choice
is represented, rejected proposals are absent from the adopted scheme, tentative
choices remain labeled, and examples satisfy the agreed grammar and applicable
review rules or identify an explicit exception. Distinguish proposed renamings
from changes actually made to the manuscript. Update the existing agreement when
continuing a session rather than creating competing versions.
