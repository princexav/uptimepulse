# UptimePulse Engineering Roadmap (20+ Hours Planned Work)

This roadmap outlines the core engineering milestones, architecture improvements, and feature expansions planned for `UptimePulse`.

---

## 📍 Phase 1: Advanced Probing & Synthetic Assertions (6–8 Hours)
- [ ] **JSON Body Assertion Engine:** Allow deep validation of nested JSON fields in API responses (e.g., `data.status == "healthy"`).
- [ ] **Custom HTTP Headers & Authentication:** Add support for Bearer tokens, Basic Auth, and custom request headers in monitor configs.
- [ ] **DNS Resolution Health Checks:** Measure DNS lookup times and verify returned A/AAAA records against expected IP ranges.
- [ ] **SSL Expiration Warning Gradients:** Emit progressive warnings at 30 days, 14 days, and 3 days before TLS expiration.

---

## 📍 Phase 2: Alert Dispatchers & Escalation Policies (6–8 Hours)
- [ ] **Discord Rich Embed Dispatcher:** Send formatted Discord webhook alerts with color-coded severity (Red for outage, Green for recovery).
- [ ] **Slack Block-Kit Dispatcher:** Format incident cards for Slack channels with quick-action links.
- [ ] **Debounce & Flap Protection:** Prevent alert spam when an endpoint fluctuates intermittently between up and down states.
- [ ] **Dead Man's Snitch (Heartbeat Ingestion):** Inverted monitoring where external cron jobs ping UptimePulse; alert if a cron job fails to check in.

---

## 📍 Phase 3: Analytics, Reporting & Visualization (6–8 Hours)
- [ ] **Uptime SLA Calculation Engine:** Compute rolling 7-day, 30-day, and 90-day availability percentages (e.g. 99.95%).
- [ ] **Prometheus Metrics Exporter:** Expose a `/metrics` HTTP endpoint for scraping latency histograms and status gauges into Grafana.
- [ ] **Automated Static Status Page Generator:** Compile a lightweight, single-page HTML status dashboard that can be published to GitHub Pages or Netlify.
- [ ] **SQLite Pruning & Retention Policies:** Automatic background cleanup of granular ping logs older than 90 days.
