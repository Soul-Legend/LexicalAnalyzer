# Lexical Analyzer Generator

This project is a Lexical Analyzer Generator implemented in Python. It allows users to define token patterns using regular expressions, constructs the corresponding finite automata (NFA and DFA), and uses the optimized DFA to tokenize input source code. The generator supports two primary DFA construction methods: Thompson's construction algorithm followed by subset construction, and direct DFA construction via syntax tree augmentation and followpos computation.

## Features

*   **Regular Expression Input:** Define token specifications using a syntax similar to standard regular expressions.
*   **Dual DFA Construction Methods:**
    *   **Thompson's Algorithm:** ER → NFA → DFA → Minimized DFA.
    *   **Followpos (Direct Method):** ER → Augmented Syntax Tree → Followpos Table → DFA → Minimized DFA.
*   **Automata Visualization:**
    *   Textual representation of NFAs (individual and combined).
    *   Textual representation of DFAs (non-minimized and minimized transition tables).
    *   Graphical rendering of the final minimized DFA (requires Graphviz).
*   **Lexical Analysis:** Tokenizes input source code based on the generated minimized DFA.
*   **Symbol Table:** Manages static definitions (patterns, reserved words) and dynamic symbols found during tokenization.
*   **User Interface:** A graphical user interface built with CustomTkinter for defining expressions, controlling the generation process, and viewing results.
*   **Test Modes:**
    *   **Manual Mode:** Step-by-step execution of the lexer generation process for user-defined inputs.
    *   **Full Test Mode:** Automated execution of predefined test cases, allowing selection of the DFA construction method.
*   **Output Formats:**
    *   DFA transition tables in a human-readable format.
    *   DFA transition tables in a specified format for automated checking.
    *   List of generated tokens.

## Prerequisites

*   Python 3.x
*   Required Python libraries:
    *   `customtkinter`
    *   `Pillow`
    *   `graphviz`
*   Graphviz: The Graphviz software (specifically the `dot` command-line tool) must be installed and accessible via the system's PATH for DFA graph rendering. Download from [graphviz.org/download/](https://graphviz.org/download/).

Install Python dependencies using pip:
```
pip install customtkinter Pillow graphviz
```
## Project Structure

├── front/     # GUI components (app, frames, callbacks, controls, ui_utils)

├── tests.py                # Predefined test cases

├── automata.py             # NFA, DFA, and related algorithms (Thompson's, subset construction, minimization)

├── config.py               # Configuration constants (e.g., EPSILON)

├── graph_drawer.py         # DFA visualization using Graphviz

├── lexer_core.py           # Lexer, symbol table, RE file parsing

├── main.py                 # Main application entry point

├── regex_utils.py          # Utilities for RE preprocessing, infix-to-postfix, precedence

├── syntax_tree_direct_dfa.py # Direct DFA construction (syntax tree, followpos)

├── ui_formatters.py        # Helper functions to format automata details for display

## Usage
Install prerequisites (as listed above).
Run the application:
```
python main.py
```
## Interface Overview
* Start Screen: Choose an operation mode:

    * Manual Mode (Thompson)

    * Manual Mode (Followpos)

    * Full Test Mode (Automatic)

* Manual Mode:

    * Input regular expression definitions (or load from a file).

    * Input source code for tokenization.

    * Step-by-step controls for:

        * Processing REs (to NFAs or augmented tree/followpos).

       * Combining NFAs & Determinization (Thompson's method).

       * Minimizing the DFA.

      * Drawing the minimized DFA.

       * Saving the DFA table.

       * Tokenizing the source code.

  *  Results are displayed in tabbed views.

* Full Test Mode:

   * Select the DFA construction method (Thompson/Followpos).

   * Choose from a list of predefined test cases.

  * The system automatically executes all generation and tokenization steps.

   * Results are displayed in tabbed views.

## Interface Overview

  *   Start Screen: Choose an operation mode:

      *   Manual Mode (Thompson)

       *  Manual Mode (Followpos)

       *  Full Test Mode (Automatic)

  *   Manual Mode:

        * Input regular expression definitions (or load from a file).

       *  Input source code for tokenization.

       *  Step-by-step controls for:

           *  Processing REs (to NFAs or augmented tree/followpos).

          *   Combining NFAs & Determinization (Thompson's method).

           *  Minimizing the DFA.

           *  Drawing the minimized DFA.

           *  Saving the DFA table.

           *  Tokenizing the source code.

        * Results are displayed in tabbed views.

   *  Full Test Mode:

       *  Select the DFA construction method (Thompson/Followpos).

      *   Choose from a list of predefined test cases.

       *  The system automatically executes all generation and tokenization steps.

        * Results are displayed in tabbed views.

## Regular Expression Definition Format
Define regular expressions in a file or the input text area, one per line:
```
TOKEN_NAME: RegularExpression
```
Example:
```
ID: [a-zA-Z_][a-zA-Z0-9_]*
NUM: [0-9]+(\.[0-9]+)?
IF: if
WS: [ ]+ %ignore
```

## Supported Syntax:
   *  Concatenation: Implicit (e.g., ab) or explicit (.).

  *   Alternation: | (e.g., a|b).

  *   Kleene Star: * (zero or more occurrences).

  *   Positive Closure: + (one or more occurrences).

  *   Optional: ? (zero or one occurrence).

  *   Grouping: () (e.g., (ab)+).

   *  Character Classes: []

       *  Literals: [abc]

        * Ranges: [a-z], [0-9]

       *  Escaped characters within classes: [\-\]] (for literal hyphen or closing bracket).

   *  Escaped Metacharacters: \., \*, \+, \?, \|, \(, \), \[, \], \\.

  *   Epsilon: & (e.g., a? is equivalent to a|&).

  *   Ignore Directive: Append %ignore to a definition to have the lexer match the pattern but not produce a token (e.g., for whitespace).

  *   Reserved Words: Identified heuristically if TOKEN_NAME is uppercase and RegularExpression is its lowercase form (e.g., IF: if).

  *   Definition Priority: The order of definitions matters. Earlier definitions take precedence in case of ambiguity for the longest match. Reserved words are typically prioritized over general identifiers by the lexer logic.

## Output interpretation
The tabbed display provides detailed insights into each stage:

* ER → NFA Ind. / Tree+Followpos:

  *  Thompson: Individual NFA details.

   * Followpos: Augmented syntax tree, followpos table, and a conceptual combined NFA.

* NFA Combined (ε-Union) / Direct DFA (Non-Min.):

    * Thompson: Combined NFA details and the non-minimized DFA from subset construction.

   *  Followpos: Non-minimized DFA from the followpos method.

* Minimized DFA (Final): Transition tables for both the non-minimized (input to minimization) and final minimized DFA.

* Minimized DFA Drawing: Graphical representation of the final DFA.

* Symbol Table (Definitions & Dynamic): Static pattern definitions, identified reserved words, and dynamic symbol table populated during tokenization.

* Lexical Analyzer Output (Tokens): The list of tokens generated from the input source code, e.g., <lexeme, TOKEN_TYPE>
