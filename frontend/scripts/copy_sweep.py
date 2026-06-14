# One-off copy sweep: (1) targeted engine-name replacements, (2) em-dash
# removal in user-visible component copy, (3) report of anything left over.
import io
import re

BASE = r"C:\Users\vivek\Desktop\AgenticAI_POCs\hf_adaptiveui_ux\v2\frontend-vue"


def load(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()


def save(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


TARGETED = {
    r"src\pages\Chat.vue": [
        ("label: 'learned · UCB',", "label: 'learned · memory',"),
        ('title="Text format is chosen per user + intent by the APE bandit (UCB) and learns from your reactions"',
         'title="Text format is chosen per user + intent by APE\'s adaptive memory and learns from your reactions"'),
        ("? 'Response format selected by the APE bandit for this user + intent'",
         "? 'Response format selected by APE for this user + intent'"),
        ('title="Visual redraw — same data, new chart kind. APE was skipped: no reward recorded, bandit untouched."',
         'title="Visual redraw: same data, new chart kind. APE was skipped, no reward recorded, memory untouched."'),
    ],
    r"src\pages\FutureWork.vue": [
        ("{ icon: BoltIcon, title: 'Per-user format bandit', body: 'Round-robin → UCB picks the response format for each user and each question type, live on every turn.' },",
         "{ icon: BoltIcon, title: 'Per-user format memory', body: 'Fair first trials, then confidence-weighted picks choose the response format for each user and each question type, live on every turn.' },"),
        ("only format moves the bandit", "only format moves the memory"),
        ("Reactions attach to the exact answer they refer to — no turn ids to track — with conditional writes that can’t double-apply.",
         "Reactions attach to the exact answer they refer to, with no turn ids to track, using conditional writes that can’t double-apply."),
        ("The bandit only learns as fast as the signal arrives.", "The engine only learns as fast as the signal arrives."),
        ("copy / save and regenerate clicks — frequent UI events the bandit can trust",
         "copy / save and regenerate clicks, frequent UI events the engine can trust"),
        ("A “visualization” arm the bandit can select for data-shaped intents",
         "A “visualization” option the engine can select for data-shaped intents"),
        ("A second, stacked bandit that learns the teaching strategy", "A second, stacked learner that picks the teaching strategy"),
        ("Validated in shadow mode first — learned globally", "Validated in shadow mode first, learned globally"),
    ],
    r"src\pages\Login.vue": [
        ("adapt their format to you — picked and learned by the APE bandit.",
         "adapt their format to you, picked and learned by APE."),
    ],
    r"src\components\viz\ApePlayground.vue": [
        ("label: 'exploring · round-robin',", "label: 'exploring · fair trials',"),
        ("note: 'Cold start — every format gets one fair trial before scores decide.',",
         "note: 'Cold start: every format gets one fair trial before scores decide.',"),
        ("label: 'exploiting · UCB',", "label: 'exploiting · learned',"),
        ("note: 'Enough evidence — the highest upper-confidence score wins this pick.',",
         "note: 'Enough evidence: the strongest memory wins this pick.',"),
        ("note: 'The engine degraded gracefully — a neutral format was served.',",
         "note: 'The engine degraded gracefully and a neutral format was served.',"),
        ("'untried — guaranteed next in the rotation' : 'UCB ' + a.ucb.toFixed(3)",
         "'untried · next in the rotation' : 'confidence ' + a.ucb.toFixed(3)"),
        ("'UCB exploitation' : 'round-robin exploration'", "'learned memory' : 'fair exploration'"),
        ("This is not a mock — the button calls the production bandit. It will round-robin through untried formats\n          first, then switch to UCB once it has evidence. Your real chat profile is untouched.",
         "This is not a mock; the button calls the production engine. It tries every untried format once,\n          then leans on what it has learned. Your real chat profile is untouched."),
        ("2 · Ask the bandit", "2 · Ask the engine"),
        ("The bandit’s scoreboard", "The engine’s scoreboard"),
    ],
    r"src\pages\Home.vue": [
        ("<span>© 2026 APE — Adaptive Personalisation Engine</span>",
         "<span>© 2026 APE · Adaptive Personalisation Engine</span>"),
    ],
}

for rel, pairs in TARGETED.items():
    p = BASE + "\\" + rel
    s = load(p)
    for old, new in pairs:
        if old not in s:
            print("MISS  %s :: %s" % (rel, old[:70]))
        else:
            s = s.replace(old, new)
    save(p, s)
    print("done targeted", rel)

# ---- bulk em-dash removal in visible copy files ----
DASH_FILES = [
    r"src\pages\Home.vue", r"src\pages\About.vue", r"src\pages\FutureWork.vue",
    r"src\pages\Login.vue", r"src\pages\Chat.vue", r"src\pages\RagFinance.vue",
    r"src\layout\AppShell.vue",
    r"src\components\viz\ApePlayground.vue", r"src\components\viz\AgentTrace.vue",
    r"src\components\viz\FormatMorph.vue", r"src\components\viz\InteractiveChart.vue",
    r"src\components\viz\ArchFlow.vue", r"src\components\viz\NeuralBrain.vue",
    r"src\components\viz\VizChart.vue", r"src\components\WidgetRegistryRenderer.vue",
]
for rel in DASH_FILES:
    p = BASE + "\\" + rel
    s = load(p)
    n = s.count(" — ")
    s = s.replace(" — ", ", ")
    save(p, s)
    print("dashes %-55s %d replaced" % (rel, n))

# ---- leftover report (visible-ish lines only) ----
print("\n--- leftover em dashes ---")
for rel in DASH_FILES:
    for i, line in enumerate(load(BASE + "\\" + rel).splitlines(), 1):
        if "—" in line:
            print("%s:%d: %s" % (rel, i, line.strip()[:110]))

print("\n--- leftover UCB / bandit mentions ---")
for rel in list(TARGETED.keys()) + DASH_FILES + [r"src\components\viz\TechGlyph.vue"]:
    seen = set()
    for i, line in enumerate(load(BASE + "\\" + rel).splitlines(), 1):
        if re.search(r"UCB|bandit", line, re.IGNORECASE) and (rel, i) not in seen:
            seen.add((rel, i))
            print("%s:%d: %s" % (rel, i, line.strip()[:110]))
