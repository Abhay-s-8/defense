import {
  ArrowRight,
  BrainCircuit,
  ChevronDown,
  Lock,
  Radar,
  ShieldCheck,
  Sparkles,
  CreditCard,
  Database,
  Server,
  Fingerprint
} from "lucide-react";

import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="mc-landing">
      <div className="mc-intro-animation" aria-hidden="true">
        <div className="army-intro-bg"></div>
        <div className="army-intro-vignette"></div>
        <div className="army-intro-content">
          <div className="army-intro-emblem">⚔</div>
          <div className="army-intro-rings">
            <span className="army-ring left"></span>
            <span className="army-ring right"></span>
            <span className="army-ring-core"></span>
          </div>
          <div className="army-intro-kicker">PATRIOTIC DEFENSE INTERFACE</div>
          <div className="mc-intro-wordmark">FraudShield</div>
          <div className="mc-intro-subtitle">AI DEFENSE LAB · TEAM AITIANS</div>
        </div>
        <div className="army-intro-scan"></div>
      </div>

      <header className="mc-header">
        <Link className="mc-brand" to="/">
          <div className="army-brand-mark" aria-label="Defense inspired mark">
            <span className="army-brand-chakra">✦</span>
            <span className="army-brand-swords">⚔</span>
          </div>
          <div className="mc-brand-copy">
            <strong>FraudShield</strong>
            <span>AI Defense Lab · Bharat Theme</span>
          </div>
        </Link>

        <div className="mc-header-right">
          <span className="mc-challenge-label">TEAM AITIANS · DEFENSE-INSPIRED INTERFACE</span>

          <Link className="mc-text-button" to="/login">
            Sign in
          </Link>

          <Link className="mc-primary-button" to="/register">
            Create account
            <ArrowRight size={17} />
          </Link>
        </div>
      </header>

      <main>
        <section className="mc-cover-section">
          <div className="mc-ambient-circle mc-ambient-one"></div>
          <div className="mc-ambient-circle mc-ambient-two"></div>

          <div className="mc-cover-card-art army-hero-panel" aria-hidden="true">
            <div className="army-hero-image"></div>
            <div className="army-hero-grid"></div>
            <div className="army-hero-status">
              <span className="army-live-dot"></span>
              DEFENSE NETWORK · ACTIVE
            </div>
            <div className="army-hero-insignia">⚔</div>
          </div>

          <div className="mc-cover-copy">
            <div className="mc-eyebrow">AI-POWERED DEFENSE · SERVICE BEFORE SELF</div>

            <h1>
              Intelligent Defense Lab
              <span>for Payment Security</span>
            </h1>

            <p>
              A defense-inspired command interface for a closed-loop Red Team vs Blue Team platform. It generates synthetic fraud scenarios, challenges the detector, learns from misses, and strengthens the next defense cycle.
            </p>

            <div className="mc-hero-actions">
              <Link className="mc-primary-button large" to="/register">
                Enter defense lab
                <ArrowRight size={18} />
              </Link>

              <Link className="mc-secondary-button large" to="/login">
                Sign in
              </Link>
            </div>

            <div className="mc-proof-row">
              <div>
                <strong>97.48%</strong>
                <span>held-out synthetic Round-3 detection</span>
              </div>

              <div>
                <strong>5,000</strong>
                <span>fresh adversarial test attacks</span>
              </div>

              <div>
                <strong>4</strong>
                <span>live Red Team attack families</span>
              </div>
            </div>
          </div>

          <a className="mc-scroll-cue" href="#story">
            Explore the defense system
            <ChevronDown size={18} />
          </a>
        </section>

        <section className="mc-story-section" id="story">
          <div className="mc-story-image-wrap">
            <img
              src="/assets/army-dashboard.png"
              alt="Indian defense inspired command interface background"
            />
            <div className="mc-story-image-overlay"></div>

            <div className="mc-story-floating-badge">
              <ShieldCheck size={19} />
              <div>
                <strong>Protected model access</strong>
                <span>JWT-authenticated Flask APIs</span>
              </div>
            </div>
          </div>

          <div className="mc-story-copy">
            <div className="mc-eyebrow">INTRODUCTION</div>
            <h2>From static fraud detection to continuous adversarial defense.</h2>

            <p>
              Traditional fraud models are usually trained on historical data and
              then deployed. Fraud behavior keeps changing. FraudShield adds a
              controlled attacker simulator around the detector so the system can
              continuously expose weak patterns before they become production
              blind spots.
            </p>

            <div className="mc-story-points">
              <div>
                <span>01</span>
                <p><strong>Red Team</strong> automatically generates synthetic fraud attempts.</p>
              </div>
              <div>
                <span>02</span>
                <p><strong>Blue Team</strong> scores every transaction with XGBoost.</p>
              </div>
              <div>
                <span>03</span>
                <p><strong>GenAI Analyst</strong> explains misses and proposes the next safe test strategy.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="mc-capabilities-section">
          <div className="mc-section-heading">
            <div>
              <div className="mc-eyebrow">CORE PLATFORM</div>
              <h2>Four layers. One adaptive defense loop.</h2>
            </div>
            <p>
              FraudShield is presented through a modern Indian defense-inspired interface while the underlying fraud pipeline remains unchanged.
            </p>
          </div>

          <div className="mc-capability-layout">
            <article className="mc-capability-card featured">
              <div className="mc-feature-card-visual">
                <div className="mc-stacked-card back"></div>
                <div className="mc-stacked-card middle"></div>
                <div className="mc-stacked-card front">
                  <div className="mc-card-chip small"></div>
                  <div className="mc-mini-logo large">
                    <i></i>
                    <b></b>
                  </div>
                </div>
              </div>
              <CreditCard size={23} />
              <h3>Blue Team Risk Engine</h3>
              <p>
                Manual transaction scoring through the same V4 XGBoost model used
                by the automated Red Team tests.
              </p>
              <div className="mc-tag-row">
                <span>XGBoost V4</span>
                <span>Probability</span>
                <span>Risk tier</span>
              </div>
            </article>

            <article className="mc-capability-card">
              <Radar />
              <h3>Red Team Simulator</h3>
              <p>
                Generates account takeover, card testing, mule activity, and
                low-and-slow synthetic attacks at scale.
              </p>
            </article>

            <article className="mc-capability-card">
              <BrainCircuit />
              <h3>GenAI Strategy Layer</h3>
              <p>
                Produces structured attack plans and human-readable analysis of
                why attacks were detected or missed.
              </p>
            </article>

            <article className="mc-capability-card">
              <Fingerprint />
              <h3>Identity & Access</h3>
              <p>
                Create-account, sign-in, password hashing, JWT authorization, and
                protected model endpoints.
              </p>
            </article>

            <article className="mc-capability-card">
              <Database />
              <h3>Experiment Memory</h3>
              <p>
                Stores Red Team runs and missed attacks so weak cases can become
                future retraining candidates.
              </p>
            </article>
          </div>
        </section>

        <section className="mc-loop-section">
          <div className="mc-loop-copy">
            <div className="mc-eyebrow">AI VS AI</div>
            <h2>The loop is the product.</h2>
            <p>
              One transaction can be checked manually. The Red Team goes further:
              it creates hundreds or thousands of controlled synthetic attacks,
              sends every one into the same Blue Team model, and measures where
              the defender still fails.
            </p>

            <div className="mc-loop-metrics">
              <div>
                <span>Round 2</span>
                <strong>11.64%</strong>
                <small>hard-attack detection</small>
              </div>
              <div className="mc-loop-arrow">→</div>
              <div>
                <span>Adversarial retraining</span>
                <strong>4,418</strong>
                <small>missed patterns used</small>
              </div>
              <div className="mc-loop-arrow">→</div>
              <div>
                <span>Round 3</span>
                <strong>97.48%</strong>
                <small>fresh synthetic holdout</small>
              </div>
            </div>
          </div>

          <div className="mc-loop-diagram">
            <LoopNode icon={<Sparkles />} label="GenAI strategy" className="strategy" />
            <LoopNode icon={<Radar />} label="Red Team" className="red-node" />
            <LoopNode icon={<ShieldCheck />} label="Blue Team" className="blue-node" />
            <LoopNode icon={<BrainCircuit />} label="Weakness analysis" className="analysis" />
            <div className="mc-loop-line line-1"></div>
            <div className="mc-loop-line line-2"></div>
            <div className="mc-loop-line line-3"></div>
            <div className="mc-loop-line line-4"></div>
          </div>
        </section>

        <section className="mc-tech-section">
          <div className="mc-tech-card">
            <Server />
            <span>Backend</span>
            <strong>Flask</strong>
          </div>
          <div className="mc-tech-card">
            <ShieldCheck />
            <span>Blue Team</span>
            <strong>XGBoost V4</strong>
          </div>
          <div className="mc-tech-card">
            <BrainCircuit />
            <span>GenAI</span>
            <strong>LLM Strategy + Analyst</strong>
          </div>
          <div className="mc-tech-card">
            <Lock />
            <span>Security</span>
            <strong>JWT + SQLite</strong>
          </div>
        </section>

        <section className="mc-final-cta">
          <div className="army-final-emblem">⚔</div>

          <div>
            <div className="mc-eyebrow">FRAUDSHIELD / AI DEFENSE LAB</div>
            <h2>Attack. Detect. Learn. Defend.</h2>
            <p>
              Build pressure into the system before attackers put pressure on the network.
            </p>
          </div>

          <Link className="mc-primary-button large" to="/register">
            Launch the lab
            <ArrowRight size={18} />
          </Link>
        </section>
      </main>
    </div>
  );
}

function LoopNode({ icon, label, className }) {
  return (
    <div className={`mc-loop-node ${className}`}>
      {icon}
      <strong>{label}</strong>
    </div>
  );
}
