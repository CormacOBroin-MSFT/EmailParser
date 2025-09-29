# EmailParser

EmailParser cleans plaintext emails by stripping out signature blocks and other contact-card clutter while keeping the conversational content intact. The heart of the project is the `convert` helper in `Parser.py`, which takes the path to an email file, scores each line, and writes a sibling `*_clean` copy with signatures removed.

## How it works

- The original email is parsed with [mailparser](https://github.com/SpamScope/mail-parser) so both MIME messages and simple text files are supported.
- Any HTML fragments are normalised into text, quotes are preserved, and the body is split into line-sized "sentences" for scoring.
- spaCy provides part-of-speech tags that help decide whether a short line is more like a salutation or contact info than real prose.
- Heuristics catch common signature openings (for example, “Best,” or “Sent from my iPhone”) and contact-card patterns such as phone numbers, email addresses, and pipe-separated title lines.
- When the signature boundary is detected, lines are skipped until the parser encounters either a quoted message delimiter or a new conversational fragment.

The result is a text file with the same structure as the original message but without the trailing signature block. Quoted threads, forward headers, and empty lines are preserved as-is.

## Setup

Create a virtual environment, install dependencies, and download the spaCy English model:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

For convenience you can run the bundled helper script, which activates the checked-in environment (if present), ensures `numpy`, `spacy`, and `en_core_web_sm` are installed, and prints the paths in use:

```bash
source activate_env.sh
```

## Usage

Run the parser against any text-based email file. The command below prints the path of the cleaned output:

```bash
python -c "from Parser import convert; print(convert('emails/test0.txt'))"
```

Key behaviour:

- A new file named `<original>_clean.txt` is written in the same directory as the input.
- Existing files are overwritten so that re-running the parser updates the cleaned copy.
- The optional `threshold` argument in `convert` (default `0.9`) controls how aggressively short lines are treated as signatures. Lower values keep more borderline lines.
- To force a different spaCy model, pass `model='en_core_web_md'` or another installed pipeline.

To tidy up generated artefacts after experimenting:

```bash
rm emails/*_clean.txt
```

## Extras

- `Example.ipynb` illustrates the parsing pipeline and lets you compare raw vs. cleaned output inside a notebook.
- The `emails/` folder contains anonymised sample messages that double as regression fixtures; feel free to drop in your own `.txt` files for quick testing.

## Troubleshooting

- If you see `OSError: [E050]` from spaCy, the requested model is missing—re-run `python -m spacy download en_core_web_sm`.
- MIME emails with attachments may produce blank bodies if `mailparser` cannot decode the payload. In that case the raw file contents are used as a fallback.
- For HTML-heavy messages, ensure they are saved with UTF-8 encoding so the parser can safely normalise line endings.