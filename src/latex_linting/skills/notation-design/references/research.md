# Research on designing coherent mathematical notation

Checked 2026-10-26. These are primary authors' recommendations and an official
typesetting guide, not evidence for one universal notation system. The workflow
implications below are our synthesis, distinguished from the sources' advice.

## Halmos: design the alphabet as a whole

In section 5, “Think about the alphabet,” Paul Halmos describes planning tables of
letters, fonts, and cases for the objects a work will need. He argues against
choosing symbols piecemeal during composition and advocates related-looking
notation for related expressions. He also warns against excessively rigid letter
reservations and distinctions readers cannot easily perceive. Section 15,
“Resist symbols,” recommends removing symbols that add no explanatory value.
His preface explicitly presents the essay as personal advice, not a recipe.
[Halmos, *How to Write Mathematics*, sections 5 and 15; university-hosted scan of the original essay](https://courses.washington.edu/b572/public/HalmosHowToWrite.pdf).

Workflow implication: inventory conceptual families across chapters before
renaming individual symbols. Compare alternatives in actual expressions, and
consider deleting unnecessary notation as a genuine design option.

## Tao: judge the system, its transformations, and its costs

Terence Tao proposes evaluating notation through unambiguous interpretation,
expressiveness, naturalness, error detection, resemblance between related
concepts, familiarity, and correspondence between mathematical transformations
and symbolic manipulations. He says a single symbol cannot be judged independently
of its surrounding system and application domain. He also distinguishes the
initial cost of learning notation from its recurring cost of use. These are
desirable properties, explicitly not mandatory axioms.
[Tao's own MathOverflow answer on notation design](https://mathoverflow.net/a/366118).

Workflow implication: test a proposed convention on definitions, transformations,
and downstream equations together. A shorter local expression may impose more
memory or translation work elsewhere. Similar typography should represent a real
relationship rather than suggest one accidentally.

## Tao: scope, economy, literature, and migration

Tao recommends putting global notation near a paper's beginning and local
notation near its use. He advises compatibility with existing literature, or
translating important imported results when notation differs. He treats repeated
use as a reason to introduce shorthand, while acknowledging exceptions; a
one-use expression generally needs no special symbol. He suggests semantic TeX
macros when tentative symbol choices may change, so one definition can be updated
instead of performing repeated replacements.
[Tao, “Use good notation”](https://terrytao.wordpress.com/advice-on-writing-papers/use-good-notation/).

Workflow implication: record scope and expected use, preserve disciplinary
conventions when they help the intended reader, and compare shorthand against
plain prose. His frequency heuristic is advice, not a mandatory numerical test.
Macros can support a later authorized migration; they are not required to explore
or document a convention.

## Bertsekas: a bridge between exposition and notation

Dimitri Bertsekas's lecture slides place consistent notation and nomenclature
among the rules governing an entire document. The notation section recommends
mnemonic names, simple indexing, and removing notation that the statement does
not need.
[Bertsekas, *Ten Simple Rules for Mathematical Writing*, rule 4](https://web.mit.edu/dimitrib/www/Ten_Rules.pdf).

Workflow implication: review prose terms and symbols together. Making notation
uniform while calling its underlying concept by several names leaves the reader
with the same translation problem.

## NIST: typography carries semantics, but styles differ

NIST distinguishes quantity symbols, unit symbols, and descriptive terms. It
prescribes italic quantities and variable indices, upright units and descriptive
qualifiers, and distinguishes scalar, vector, and tensor typefaces. Its examples
include uppercase scalars, so lowercase is not an intrinsic mathematical property
of a scalar. Its vector recommendation is bold italic; the repository's
MATH-07 uses bold upright vectors. NIST guidance is addressed to scientific and
technical manuscripts, particularly NIST authors, rather than every mathematical
discipline.
[NIST SP 811, chapter 10, especially sections 10.1 and 10.2](https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-10-more-printing-and-using-symbols-and-numbers).

Workflow implication: retain the repository's baseline, distinguish semantic
checks from house style, and surface conflicts for a manuscript-specific decision.
An outside source does not silently override an agreed typography convention.

## What these sources support, and what they do not decide

The sources support deliberate design across a manuscript, related symbol
families, explicit scope, economical notation, consistent terminology, and
evaluation in realistic equations. They do not establish a universal assignment
of hats, tildes, bars, Greek letters, superscripts, or count symbols.

The present thesis's lowercase count grammar, relative prediction indices,
calligraphic spectral Y, collection by omitting a constituent index, and
quantization-resolution annotation are negotiated manuscript choices. Treat them
as examples of designing a coherent system, not as defaults to impose on another
author. Likewise, continuous-time arguments versus discrete-time indices are a
useful signal convention, not a restriction on the domains of mathematical
functions in general.

Practical review questions derived from this research:

- Does the proposed symbol express the concept's relationship to existing ones?
- Does a visual distinction correspond to a distinction the reader needs?
- Can a reader recover the domain, shape, index roles, and transformation meaning?
- Does the proposal simplify the whole exposition, including important formulas?
- Can a symbol, qualifier, or transformation equation be omitted in favor of prose?
- Is a new convention worth its learning cost relative to established notation?

These questions guide discussion; they are not a substitute for the author's
preferences or for checking the mathematics.
