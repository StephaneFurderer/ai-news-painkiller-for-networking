# Reader → Content Workflow

## Workflow

```mermaid
graph LR
    A[Reader ID] --> B[Retrieve document]
    B --> C[Set Goal\nChoose between: attract / nurture / convert\nAsk: What am I trying to make happen with this?]
    C --> D[Refine to ICP\nWhat problem am I solving?\nWhat’s the takeaway for them?\nWhat change or result could they get?\nWhat might they be wondering right now?]
    D --> E[Proof\nAdd proof or context so people trust you.\n\nBest sources:\n• Your experiences (behind the scenes, lessons learned)\n• Client results (before and after, testimonials, screenshots)\n• Real stories (your observations, industry examples)\n• External sources (only when they add weight)]
    E --> F[Format\nChoose the format that fits your goal.\n\nAttract (build awareness and trust):\n• Belief shift\n• Origin story\n• Industry myths\n\nNurture (show authority / create demand):\n• Framework\n• Step-by-step\n• How I / How to\n\nConvert (qualify and filter buyers):\n• Objection post\n• Result breakdown\n• Client success story]
```

## Usage

```bash
python readwise_processor.py --document-id "<reader_document_id>" --task summarize
```

Tasks: summarize, extract-key-points, analyze-sentiment.

Configure token via `READWISE_TOKEN` or `config/settings.py`.