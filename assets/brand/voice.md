# Raicho voice

## Core copy

**Tagline:** Your Thunderbird, anywhere.

**Short description:** A browser interface for Thunderbird.

**Project introduction:** Raicho brings Thunderbird to your browser. Run Raicho
and Thunderbird together in Docker, then open Raicho from your other computers.
Your mail and filters stay in Thunderbird.

The introduction describes the planned product, not a released application.
In release materials, describe what that release actually supports. Deployment
and storage boundaries are defined in the [architecture](../../docs/reference/architecture.md).
Keep implementation details out of interface copy unless they help the user act.

## Tone

Be calm, clear, and useful. Describe what is happening and what someone can do next.

- Use familiar words and short sentences.
- Address the person as “you” when it helps.
- Name Thunderbird when its running state matters.
- Use sentence case for headings and buttons.
- Keep humor out of errors and connection problems.

| Prefer | Avoid |
| --- | --- |
| Connect Thunderbird | Unlock your connected workspace |
| Raicho can’t reach Thunderbird | Something went wrong |
| Updating inbox… | Supercharging your email experience |
| No messages in this inbox | Your inbox is lonely |

## Interface copy

These are copy drafts. Use each when the interface can detect the state and
support the action described.

### Onboarding

**Title:** Your Thunderbird, anywhere.

**Body:** Use Thunderbird through your browser. Connect to the Thunderbird
running in your Raicho deployment.

**Action:** Connect Thunderbird

### Connecting

**Title:** Connecting to Thunderbird…

**Body:** Keep Thunderbird running while Raicho connects.

### Connection unavailable

**Title:** Thunderbird is unavailable

**Body:** Raicho can’t reach Thunderbird. Check that Thunderbird is running and
the Raicho extension is enabled.

**Action:** Try again

### Updating the message list

**Title:** Updating inbox…

**Body:** Getting the latest message list from Thunderbird.

### Empty inbox

**Title:** No messages in this inbox

**Body:** Choose another folder to view its messages.

Use the empty state after a successful load. An unfinished update or failed
connection needs its own message.

### Search with no results

**Title:** No matching messages

**Body:** Try a different search.
