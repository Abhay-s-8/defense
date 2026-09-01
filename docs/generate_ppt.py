import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Initialize Presentation with 16:9 Widescreen
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color Palette (Dark Theme with Saffron/Gold & Emerald Accents)
BG_COLOR = RGBColor(11, 15, 25)          # Deep Dark Navy #0B0F19
PANEL_COLOR = RGBColor(30, 41, 59)       # Slate Card #1E293B
PANEL_BORDER = RGBColor(51, 65, 85)      # Slate Border #334155
GOLD_ACCENT = RGBColor(245, 158, 11)     # Saffron Gold #F59E0B
GREEN_ACCENT = RGBColor(16, 185, 129)    # Emerald #10B981
BLUE_ACCENT = RGBColor(59, 130, 246)     # Sky Blue #3B82F6
PURPLE_ACCENT = RGBColor(168, 85, 247)   # Purple #A855F7
RED_ACCENT = RGBColor(239, 68, 68)       # Crimson Red #EF4444
WHITE = RGBColor(255, 255, 255)
MUTED_TEXT = RGBColor(148, 163, 184)     # Light Slate #94A3B8

def set_slide_background(slide):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = BG_COLOR

def add_header(slide, tag, title, subtitle=None):
    # Category Tag
    tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
    tf_tag = tag_box.text_frame
    tf_tag.word_wrap = True
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = tag.upper()
    p_tag.font.size = Pt(11)
    p_tag.font.bold = True
    p_tag.font.color.rgb = GOLD_ACCENT

    # Main Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.6))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = WHITE

    if subtitle:
        sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.7), Inches(0.4))
        tf_sub = sub_box.text_frame
        tf_sub.word_wrap = True
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = subtitle
        p_sub.font.size = Pt(13)
        p_sub.font.color.rgb = MUTED_TEXT

def add_card(slide, left, top, width, height, title, body_bullets, border_color=None, bg_color=PANEL_COLOR):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)
    else:
        shape.line.color.rgb = PANEL_BORDER
        shape.line.width = Pt(1)

    tf = shape.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP

    if title:
        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(15)
        p_title.font.bold = True
        p_title.font.color.rgb = WHITE
        p_title.alignment = PP_ALIGN.LEFT

    for i, bullet in enumerate(body_bullets):
        p = tf.add_paragraph()
        p.text = bullet
        p.font.size = Pt(12)
        p.font.color.rgb = MUTED_TEXT if not bullet.startswith("✓") and not bullet.startswith("★") else WHITE
        p.space_before = Pt(6)
        p.alignment = PP_ALIGN.LEFT

# ============================================================
# SLIDE 1: TITLE SLIDE
# ============================================================
slide_layout = prs.slide_layouts[6]
slide1 = prs.slides.add_slide(slide_layout)
set_slide_background(slide1)

# Badge
badge = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.2), Inches(4.5), Inches(0.45))
badge.fill.solid()
badge.fill.fore_color.rgb = RGBColor(245, 158, 11)
badge.line.fill.background()
tf_badge = badge.text_frame
p_b = tf_badge.paragraphs[0]
p_b.text = "AI-POWERED PAYMENT DEFENSE SYSTEM"
p_b.font.size = Pt(11)
p_b.font.bold = True
p_b.font.color.rgb = RGBColor(11, 15, 25)
p_b.alignment = PP_ALIGN.CENTER

# Main Hero Title
title_box = slide1.shapes.add_textbox(Inches(0.8), Inches(1.8), Inches(11.5), Inches(1.8))
tf = title_box.text_frame
tf.word_wrap = True
p1 = tf.paragraphs[0]
p1.text = "AI DEFENSE LAB"
p1.font.size = Pt(44)
p1.font.bold = True
p1.font.color.rgb = WHITE

p2 = tf.add_paragraph()
p2.text = "The Multi-Layered Defense Triad for Payment Security"
p2.font.size = Pt(24)
p2.font.color.rgb = GOLD_ACCENT
p2.font.bold = True

p3 = tf.add_paragraph()
p3.text = "Red Team × Blue Team  •  Behavioral Biometrics  •  Fortified XGBoost  •  Graph Neural Networks"
p3.font.size = Pt(14)
p3.font.color.rgb = MUTED_TEXT

# Key Value Pillars
add_card(slide1, Inches(0.8), Inches(4.3), Inches(3.6), Inches(2.2), "Layer 1: Biometrics", [
    "• Captures live keystroke flight/dwell rhythm",
    "• Detects Coercion & Digital Arrest scams",
    "• Flags remote desktop & bot automation"
], GREEN_ACCENT)

add_card(slide1, Inches(4.8), Inches(4.3), Inches(3.6), Inches(2.2), "Layer 2: XGBoost V4", [
    "• Server-side real-time feature store",
    "• Vectorized inference: 1,000 txs in 32ms",
    "• Exact TreeSHAP mathematical grounding"
], BLUE_ACCENT)

add_card(slide1, Inches(8.8), Inches(4.3), Inches(3.6), Inches(2.2), "Layer 3: GNN Network", [
    "• Analyzes directed fund-flow topologies",
    "• Detects multi-hop mule syndicates",
    "• Uncovers cyclic money laundering loops"
], PURPLE_ACCENT)

# Footer Note
footer_box = slide1.shapes.add_textbox(Inches(0.8), Inches(6.8), Inches(11.5), Inches(0.4))
p_foot = footer_box.text_frame.paragraphs[0]
p_foot.text = "Team: AITIANS  |  Army Institute of Technology, Pune"
p_foot.font.size = Pt(12)
p_foot.font.color.rgb = MUTED_TEXT

# ============================================================
# SLIDE 2: THE REAL-WORLD PROBLEM
# ============================================================
slide2 = prs.slides.add_slide(slide_layout)
set_slide_background(slide2)
add_header(slide2, "The Threat Landscape", "Why Traditional Fraud Detectors Fail Against Modern Scams", "Single-layer tabular models are fundamentally blind to modern social engineering and mule networks.")

add_card(slide2, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), "1. Social Engineering Blind Spot", [
    "The Digital Arrest / Vishing Dilemma:",
    "",
    "• In APP scams, the genuine customer makes the payment themselves.",
    "• Device ID, location, and credentials are 100% authentic.",
    "• Standard ML models see zero anomalies and approve the transfer.",
    "",
    "★ Missing Link: Interaction-level coercion & hesitation telemetry."
], RED_ACCENT)

add_card(slide2, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), "2. Distributed Mule Networks", [
    "Smurfing & Multi-Hop Laundering:",
    "",
    "• Syndicates break stolen funds into 200 micro-payments of ₹2,000.",
    "• Single-transaction classifiers evaluate each payment in isolation.",
    "• No individual row triggers velocity or amount alarms.",
    "",
    "★ Missing Link: Graph-level money-flow topology analysis."
], RED_ACCENT)

add_card(slide2, Inches(8.8), Inches(1.8), Inches(3.6), Inches(4.8), "3. Static Model Decay", [
    "The Adversarial Cat-and-Mouse Game:",
    "",
    "• Fraudsters adapt to static rules and find low-and-slow blind spots.",
    "• Models score well on historical data but miss fresh evasion techniques.",
    "• Missed attacks are logged but rarely retrained systematically.",
    "",
    "★ Missing Link: Continuous Red-Team adversarial learning loop."
], RED_ACCENT)

# ============================================================
# SLIDE 3: THE 3-LAYER DEFENSE TRIAD
# ============================================================
slide3 = prs.slides.add_slide(slide_layout)
set_slide_background(slide3)
add_header(slide3, "Core Innovation", "The Multi-Layered Defense Triad Architecture", "A multi-dimensional defense platform protecting transactions from keystroke to settlement.")

add_card(slide3, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), "Layer 1: Interaction Level", [
    "Behavioral Biometrics Engine",
    "Focus: User Coercion & Bot Telemetry",
    "",
    "• Real-time keystroke dwell & flight time",
    "• Submission hesitation index (>4.5s)",
    "• Active voice call & remote desktop flags",
    "• Prevents Digital Arrest & Session Hijack",
    "",
    "Weight in Fusion: 20%"
], GREEN_ACCENT)

add_card(slide3, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), "Layer 2: Transaction Level", [
    "Fortified XGBoost V4 Engine",
    "Focus: Behavioral Anomaly & Velocity",
    "",
    "• Server-side real-time feature store",
    "• Anti-feature tampering & deviation scoring",
    "• Vectorized batch inference (32ms / 1K)",
    "• Exact TreeSHAP mathematical explainability",
    "",
    "Weight in Fusion: 50%"
], BLUE_ACCENT)

add_card(slide3, Inches(8.8), Inches(1.8), Inches(3.6), Inches(4.8), "Layer 3: Network Level", [
    "GNN Mule Ring Analyzer",
    "Focus: Account Linkages & Topology",
    "",
    "• Directed multigraph money-flow mapping",
    "• Cyclic fund routing detection (A→B→C→A)",
    "• Smurfing fan-out & mule funneling alerts",
    "• Freezes coordinated syndicate clusters",
    "",
    "Weight in Fusion: 30%"
], PURPLE_ACCENT)

# ============================================================
# SLIDE 4: LAYER 1 DEEP-DIVE (BIOMETRICS)
# ============================================================
slide4 = prs.slides.add_slide(slide_layout)
set_slide_background(slide4)
add_header(slide4, "Layer 1 Deep-Dive", "Behavioral Biometrics: Defeating Scams at the Keystroke Level", "Detecting psychological coercion and automated bots before the payment is even dispatched.")

add_card(slide4, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8), "How Biometric Telemetry Works", [
    "1. Live Keystroke Dynamics:",
    "   • Dwell Time: Duration key is held down (~90-150ms).",
    "   • Flight Time: Transition time between keys (~120-280ms).",
    "   • Bot Detection: Identifies inhuman 0ms key variance.",
    "",
    "2. Psychological Coercion Indicators:",
    "   • Excessive hesitation prior to submit (>4.5 seconds pause).",
    "   • High correction rate (frequent backspaces from anxiety).",
    "   • Active voice call during checkout (Vishing signature).",
    "",
    "3. Remote Screen Overlays:",
    "   • Detects Anydesk/Teamviewer background hooks."
], GREEN_ACCENT)

add_card(slide4, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8), "Live Scam Intervention Workflow", [
    "Scenario: Citizen targeted by Digital Arrest scammer.",
    "",
    "Step 1: Scammer orders victim to transfer ₹1,00,000 immediately.",
    "Step 2: Victim enters payment from genuine phone & IP.",
    "Step 3: Biometrics engine detects active phone call + 6.8s submit hesitation + high backspace count.",
    "Step 4: Unified engine intercepts transaction and triggers:",
    "",
    "★ Policy Directive: COERCION_SAFETY_INTERVENTION",
    "★ Action: Scam warning prompt + mandatory 15-min cooling delay.",
    "★ Result: Transfer prevented before money leaves the bank."
], GOLD_ACCENT)

# ============================================================
# SLIDE 5: LAYER 2 DEEP-DIVE (XGBOOST & FEATURE STORE)
# ============================================================
slide5 = prs.slides.add_slide(slide_layout)
set_slide_background(slide5)
add_header(slide5, "Layer 2 Deep-Dive", "Fortified XGBoost V4 & Server-Side Feature Store", "Sub-millisecond tabular inference backed by anti-injection real-time feature derivation.")

add_card(slide5, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8), "Anti-Injection Real-Time Feature Store", [
    "The Vulnerability in Typical Fraud Models:",
    "• Naive APIs trust client metadata (e.g. client says velocity is 1).",
    "• Attackers tamper with payload to bypass the model.",
    "",
    "Our Server-Side Solution (RealTimeFeatureStore):",
    "• Ingests raw minimal payment (amount, merchant, card).",
    "• Server automatically computes rolling 5m velocity.",
    "• Server calculates 30-day historical spending averages.",
    "• Threat-intel IP reputation score derived server-side.",
    "",
    "✓ 100% Anti-Tamper & Zero Client Trust."
], BLUE_ACCENT)

add_card(slide5, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8), "Performance & TreeSHAP Explainability", [
    "High-Throughput Vectorized Inference:",
    "• Single-pass Pandas matrix manipulation.",
    "• Scores 1,000 synthetic attacks in 32 milliseconds (0.032s).",
    "",
    "Exact TreeSHAP Marginal Contributions:",
    "• Extracts exact booster tree split weights (`pred_contribs=True`).",
    "• Identifies top positive risk drivers (e.g. +3.44 on velocity).",
    "• Identifies negative safety anchors (e.g. -0.87 on established device).",
    "",
    "✓ Eliminates LLM hallucinations during compliance explanations."
], BLUE_ACCENT)

# ============================================================
# SLIDE 6: LAYER 3 DEEP-DIVE (GNN MULE TOPOLOGY)
# ============================================================
slide6 = prs.slides.add_slide(slide_layout)
set_slide_background(slide6)
add_header(slide6, "Layer 3 Deep-Dive", "Graph Network & Mule Ring Link Analysis", "Dismantling smurfing fan-outs and cyclic money laundering networks in real time.")

add_card(slide6, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8), "Graph Analysis Capabilities", [
    "1. Directed Fund-Flow Topology:",
    "   • Tracks nodes (Accounts, Beneficiaries, Merchants).",
    "   • Real-time graph adjacency and transaction edges.",
    "",
    "2. Cyclic Money Laundering Detection:",
    "   • Traverses graph using BFS/DFS path analysis.",
    "   • Detects closed wash-trading loops (A → B → C → A).",
    "",
    "3. Smurfing Fan-Out & Mule Funneling:",
    "   • Flags accounts dispersing funds to 4+ new mules.",
    "   • Flags destination accounts with rapid high in-degree inflows."
], PURPLE_ACCENT)

add_card(slide6, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8), "Mule Syndicate Neutralization", [
    "Scenario: Criminal syndicate laundering ₹20 Lakhs.",
    "",
    "Step 1: Stolen money dispersed across 5 sleeper mule accounts.",
    "Step 2: GNN engine traces directed edges and flags high degree fan-out.",
    "Step 3: Mules attempt to recycle funds back to an aggregator.",
    "Step 4: Cyclic flow algorithm flags closed laundering path.",
    "",
    "★ Policy Directive: MULE_SYNDICATE_FREEZE",
    "★ Action: Entire sub-graph isolated and accounts frozen instantly.",
    "★ Result: Money laundering ring dismantled in one operation."
], PURPLE_ACCENT)

# ============================================================
# SLIDE 7: DECISION FUSION & POLICY ENGINE
# ============================================================
slide7 = prs.slides.add_slide(slide_layout)
set_slide_background(slide7)
add_header(slide7, "Policy Intelligence", "Unified Multi-Layer Decision Fusion Engine", "Ensemble weighting and targeted action directives for zero customer friction and max security.")

add_card(slide7, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), "1. Frictionless Approval", [
    "Risk Score: 0% - 34%",
    "Color Directive: Emerald Green",
    "",
    "• Genuine biometrics & normal cadence",
    "• Expected spend within 30d baseline",
    "• Clean graph node topology",
    "",
    "✓ Instant seamless payment approval with zero user friction."
], GREEN_ACCENT)

add_card(slide7, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), "2. Step-Up 2FA Challenge", [
    "Risk Score: 35% - 69%",
    "Color Directive: Amber Yellow",
    "",
    "• Moderate behavioral velocity",
    "• Unfamiliar device or evening timing",
    "• No coercion flags detected",
    "",
    "✓ Triggers FIDO2 WebAuthn or Biometric Passkey challenge."
], GOLD_ACCENT)

add_card(slide7, Inches(8.8), Inches(1.8), Inches(3.6), Inches(4.8), "3. Targeted Interventions", [
    "Specialized Defense Directives:",
    "",
    "★ COERCION_SAFETY_INTERVENTION",
    "• Triggered by voice call + severe hesitation.",
    "• Introduces 15-min scam cooling delay.",
    "",
    "★ MULE_SYNDICATE_FREEZE",
    "• Triggered by cyclic laundering loop / smurfing.",
    "• Freezes entire multi-node cluster."
], RED_ACCENT)

# ============================================================
# SLIDE 8: RED TEAM ADVERSARIAL GENERATOR
# ============================================================
slide8 = prs.slides.add_slide(slide_layout)
set_slide_background(slide8)
add_header(slide8, "Adversarial Stress-Testing", "The Red Team Simulation Engine: 6 Attack Families", "Challenging the defense system with continuous stochastic synthetic fraud attacks.")

add_card(slide8, Inches(0.8), Inches(1.8), Inches(3.6), Inches(2.3), "1. Account Takeover (ATO)", [
    "• New device + high IP risk + location shift",
    "• Elevated transaction amount vs average",
    "• Repeated password failures prior to tx"
], RED_ACCENT)

add_card(slide8, Inches(4.8), Inches(1.8), Inches(3.6), Inches(2.3), "2. Card Testing Micro-Charges", [
    "• Rapid velocity (15-30 txs / 5 mins)",
    "• Micro-amounts (₹1 - ₹100 per test)",
    "• Probing stolen card validity"
], RED_ACCENT)

add_card(slide8, Inches(8.8), Inches(1.8), Inches(3.6), Inches(2.3), "3. Low & Slow Stealth", [
    "• Mimicking user's normal daytime hours",
    "• Near-baseline amounts (0.8x - 1.2x)",
    "• Subtle zero-day camouflage tactics"
], RED_ACCENT)

add_card(slide8, Inches(0.8), Inches(4.3), Inches(3.6), Inches(2.3), "4. Mule Activity", [
    "• Fast fund movement to newly created beneficiary",
    "• Moderate IP risk + high amount ratio",
    "• Testing account drain thresholds"
], RED_ACCENT)

add_card(slide8, Inches(4.8), Inches(4.3), Inches(3.6), Inches(2.3), "5. Digital Arrest Coercion", [
    "• Genuine user device and credentials",
    "• Severe submit hesitation & active call",
    "• Tests Layer 1 biometric intervention"
], GOLD_ACCENT)

add_card(slide8, Inches(8.8), Inches(4.3), Inches(3.6), Inches(2.3), "6. Mule Syndicates", [
    "• Coordinated cyclic fund loops",
    "• Multi-account fan-out smurfing",
    "• Tests Layer 3 GNN graph detection"
], PURPLE_ACCENT)

# ============================================================
# SLIDE 9: CLOSED-LOOP RETRAINING (ATTACK -> DEFEND)
# ============================================================
slide9 = prs.slides.add_slide(slide_layout)
set_slide_background(slide9)
add_header(slide9, "Continuous Learning", "Closed-Loop Adversarial Retraining with Balanced Replay", "Turning missed attacks into fortified defensive weights while holding False Positives under 0.8%.")

add_card(slide9, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8), "The Closed-Loop Retraining Pipeline", [
    "How the Model Learns Without Forgetting:",
    "",
    "1. Red Team launches 5,000 synthetic attacks.",
    "2. Blue Team scores transactions and records missed cases.",
    "3. Missed attacks stored in database as candidate training data.",
    "4. Balanced Replay Buffer generated:",
    "   • 1,200 normal benign payments (Negative Anchor)",
    "   • Captured adversarial misses (Positive Class)",
    "5. Retrains XGBoost with cross-entropy loss and early stopping.",
    "6. Serializes fortified model to disk for all worker nodes.",
    "",
    "✓ Prevents Catastrophic Forgetting & Decision Boundary Drift."
], GREEN_ACCENT)

add_card(slide9, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8), "Adversarial Benchmark Results", [
    "Round 2 (Baseline Initial Model):",
    "• 5,000 Stealth Adversarial Attacks Launched",
    "• Detected: 582  |  Missed: 4,418",
    "• Detection Rate: 11.64%",
    "",
    "Round 3 (After Closed-Loop Retraining):",
    "• 5,000 Held-Out Adversarial Attacks Launched",
    "• Detected: 4,874  |  Missed: 126",
    "• Detection Rate: 97.48%",
    "",
    "★ False Negative Reduction: 97.15%",
    "★ False Positive Rate: Held at <0.8%"
], GOLD_ACCENT)

# ============================================================
# SLIDE 10: GENAI EXPLAINABILITY GROUNDING
# ============================================================
slide10 = prs.slides.add_slide(slide_layout)
set_slide_background(slide10)
add_header(slide10, "Explainable AI (XAI)", "Grounded GenAI Explainability Layer", "Translating exact TreeSHAP mathematical feature weights into human-readable compliance insights.")

add_card(slide10, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8), "Mathematical Grounding (No Hallucination)", [
    "The Risk with Raw LLM Explanations:",
    "• LLMs often guess causes based on superficial patterns.",
    "• Fails regulatory banking compliance (RBI, GDPR, OCC).",
    "",
    "Our TreeSHAP Grounded Approach:",
    "• Booster tree split margins extracted mathematically.",
    "• Top positive drivers: `[+] Velocity (+3.44)`, `[+] IP Risk (+3.06)`",
    "• Top safety anchors: `[-] Device Age (-0.74)`",
    "• LLM prompt strictly constrained to mathematical weights.",
    "",
    "✓ 100% Mathematically Grounded & Regulatory Compliant."
], BLUE_ACCENT)

add_card(slide10, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8), "Sample Plain-Language Output", [
    "Sample GenAI 360° Defense Summary:",
    "",
    "\"Transaction flagged as FRAUD (99.31% probability).",
    "The decision is mathematically driven by an abnormal surge in 5-minute velocity (+2.84 risk driver) and an elevated IP risk score (+2.70 risk driver).",
    "",
    "Key Signals Observed:",
    "• [+] Transaction Velocity 5M (+2.84 risk driver)",
    "• [+] IP Risk Score (+2.70 risk driver)",
    "• [-] Account Age Days (-0.13 safety anchor)",
    "",
    "Recommended Action: Trigger FIDO2 step-up challenge or route to Tier-2 fraud review.\""
], GOLD_ACCENT)

# ============================================================
# SLIDE 11: TECHNICAL STACK & PRODUCTION HARDENING
# ============================================================
slide11 = prs.slides.add_slide(slide_layout)
set_slide_background(slide11)
add_header(slide11, "Engineering Rigor", "Technical Architecture & Production Hardening", "Built for zero startup crashes, high concurrency, and resilient cloud deployment.")

add_card(slide11, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), "Resilient Storage", [
    "Hybrid Database Engine:",
    "",
    "• Primary: MongoDB Atlas.",
    "• Fallback: In-memory store.",
    "• Zero-crash startup guarantee.",
    "• Seamless offline demo capability."
], GREEN_ACCENT)

add_card(slide11, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), "High-Speed Inference", [
    "Vectorized Performance:",
    "",
    "• Vectorized Pandas DataFrame batching.",
    "• 1,000 attacks scored in 32ms.",
    "• Non-blocking Flask workers.",
    "• Sub-second Red Team execution."
], BLUE_ACCENT)

add_card(slide11, Inches(8.8), Inches(1.8), Inches(3.6), Inches(4.8), "API Hardening", [
    "Security & Protection:",
    "",
    "• Sliding-window rate limiting.",
    "• Brute force defense on auth/predict.",
    "• Enterprise HTTP security headers.",
    "• Model artifact disk serialization."
], GOLD_ACCENT)

# ============================================================
# SLIDE 12: CONCLUSION & SUMMARY
# ============================================================
slide12 = prs.slides.add_slide(slide_layout)
set_slide_background(slide12)
add_header(slide12, "Summary & Vision", "The Future of Payment Defense", "From reactive static scoring to continuous, multi-dimensional adversarial defense.")

add_card(slide12, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8), "Key Breakthroughs Accomplished", [
    "1. Multi-Layer Defense Triad:",
    "   • Layer 1 (Biometrics) stops Digital Arrest & Social Engineering.",
    "   • Layer 2 (XGBoost) stops takeover & velocity anomalies in 32ms.",
    "   • Layer 3 (GNN) dismantles multi-hop mule syndicates.",
    "",
    "2. Continuous Adversarial Learning:",
    "   • Closed-loop retraining boosts detection from 11.6% to 97.48%.",
    "   • Balanced replay buffers hold False Positive Rate under 0.8%.",
    "",
    "3. Grounded Explainable AI:",
    "   • Exact TreeSHAP mathematical feature weighting."
], GREEN_ACCENT)

add_card(slide12, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8), "Team AITIANS — Final Takeaway", [
    "\"Fraud is not one-dimensional, and defense cannot be static.\"",
    "",
    "By uniting interaction telemetry, sub-millisecond transaction ML, and graph topology intelligence into one continuous learning loop, we establish a robust, self-healing payment defense perimeter.",
    "",
    "Attack. Detect. Learn. Defend.",
    "",
    "Team: AITIANS (Army Institute of Technology, Pune)",
    "GitHub: AI-DEFENSE-LAB  |  Prototype: ai-defense-lab.vercel.app"
], GOLD_ACCENT)

output_path = "d:/ecg/AI_Defense_Lab_Presentation.pptx"
prs.save(output_path)
print(f"Presentation saved successfully to: {output_path}")
