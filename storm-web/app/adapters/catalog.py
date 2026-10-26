"""Adapter catalog -- one place that wraps every frozen module (P14.4).

Each frozen module is imported (never edited, NR-3) and its headline
capabilities are registered as :class:`Action`s.  All 15 modules are covered;
the executable/generator ones (payloads, obfuscation, rat) are what the
firepower layer wires to ``app.exec.runner`` in P14.5.
"""
from __future__ import annotations

from .registry import register

# --- frozen modules (imported, never edited) --------------------------------
import payload_generator
import obfuscation_engine
import rat_controller
import report_generator
import lure_generator
import threat_intel
import session_hijacker
import pivot_engine
import evasion_framework
import credential_parser
from telegram_bot import telegram_bot
from deep_recon import DeepReconOSINT
from ai_threat_analyzer import AIThreatAnalyzer
from zeroday_lab import ZeroDayLab
from quantum_crypto import QuantumCryptoEngine

# 1. payload_generator
register("payloads.types", "payload_generator", "analyze",
         "List available payload types", lambda: payload_generator.PAYLOAD_TYPES)
register("payloads.generate", "payload_generator", "generate",
         "Generate a payload by type", payload_generator.generate_payload)

# 2. obfuscation_engine
register("obfuscation.payload", "obfuscation_engine", "generate",
         "Obfuscate a payload", obfuscation_engine.obfuscate_payload)
register("obfuscation.profiles", "obfuscation_engine", "analyze",
         "List obfuscation profiles", obfuscation_engine.get_profiles)
register("obfuscation.techniques", "obfuscation_engine", "analyze",
         "Techniques for a language", obfuscation_engine.get_supported_techniques)

# 3. rat_controller
register("rat.recon", "rat_controller", "analyze",
         "Live system recon", rat_controller.deep_system_recon)
register("rat.shells", "rat_controller", "generate",
         "Reverse shells by type", rat_controller.generate_reverse_shell)
register("rat.persistence", "rat_controller", "generate",
         "Persistence commands", rat_controller.generate_persistence)
register("rat.lateral", "rat_controller", "generate",
         "Lateral movement commands", rat_controller.generate_lateral_movement)
register("rat.c2_config", "rat_controller", "generate",
         "Build a C2 profile", rat_controller.build_c2_config)
register("rat.tunnels", "rat_controller", "generate",
         "Tunnel configs", rat_controller.build_tunnel_config)
register("rat.encode", "rat_controller", "generate",
         "Encode a payload", rat_controller.encode_payload)
register("rat.injection", "rat_controller", "analyze",
         "Injection techniques", rat_controller.get_injection_techniques)

# 4. report_generator
register("reports.generate", "report_generator", "generate",
         "Generate an HTML report", report_generator.generate_report)
register("reports.gather", "report_generator", "analyze",
         "Gather report data", report_generator.gather_data)

# 5. lure_generator
register("lures.categories", "lure_generator", "analyze",
         "Lure categories", lure_generator.get_categories)
register("lures.generate", "lure_generator", "generate",
         "Generate a lure", lure_generator.generate_lure)
register("lures.render_html", "lure_generator", "generate",
         "Render a lure as HTML", lure_generator.render_html_email)

# 6. threat_intel
register("threat_intel.ip", "threat_intel", "analyze",
         "Analyse an IP", threat_intel.analyze_ip)
register("threat_intel.email", "threat_intel", "analyze",
         "Analyse an email", threat_intel.analyze_email)
register("threat_intel.report", "threat_intel", "analyze",
         "Full threat report", threat_intel.build_threat_report)

# 7. deep_recon (class-based)
register("deep_recon.domain", "deep_recon", "analyze",
         "Domain recon", DeepReconOSINT.domain_recon)
register("deep_recon.email", "deep_recon", "analyze",
         "Email intelligence", DeepReconOSINT.email_intelligence)
register("deep_recon.correlate", "deep_recon", "analyze",
         "Correlate entities", DeepReconOSINT.correlate_data)

# 8. ai_threat_analyzer (class-based)
register("ai_threat.analyze", "ai_threat_analyzer", "analyze",
         "Analyse a payload", AIThreatAnalyzer.analyze_payload)
register("ai_threat.behavioral", "ai_threat_analyzer", "analyze",
         "Behaviour profile for an IP", AIThreatAnalyzer.behavioral_analysis)
register("ai_threat.landscape", "ai_threat_analyzer", "analyze",
         "Threat landscape", AIThreatAnalyzer.get_threat_landscape)

# 9. zeroday_lab (class-based)
register("zeroday.scan", "zeroday_lab", "analyze",
         "Scan a target", ZeroDayLab.scan_target)
register("zeroday.shellcode", "zeroday_lab", "generate",
         "Generate shellcode", ZeroDayLab.generate_shellcode)
register("zeroday.cves", "zeroday_lab", "analyze",
         "Search the CVE table", ZeroDayLab.search_cves)

# 10. quantum_crypto (class-based)
register("quantum.encrypt", "quantum_crypto", "generate",
         "Simulated PQ encryption", QuantumCryptoEngine.encrypt_data)
register("quantum.entropy", "quantum_crypto", "analyze",
         "Entropy analysis", QuantumCryptoEngine.analyze_entropy)
register("quantum.algorithms", "quantum_crypto", "analyze",
         "List PQ algorithms", QuantumCryptoEngine.get_algorithms)

# 11. session_hijacker
register("session_hijack.parse_cookies", "session_hijacker", "analyze",
         "Parse cookies", session_hijacker.parse_cookies)
register("session_hijack.analyze_jwt", "session_hijacker", "analyze",
         "Analyse a JWT", session_hijacker.analyze_jwt)
register("session_hijack.assess", "session_hijacker", "analyze",
         "Assess a session", session_hijacker.assess_session)

# 12. pivot_engine
register("pivot.attack_graph", "pivot_engine", "analyze",
         "Build an attack graph", pivot_engine.build_attack_graph)
register("pivot.privesc", "pivot_engine", "analyze",
         "Suggest privilege escalation", pivot_engine.suggest_privesc)
register("pivot.kill_chain", "pivot_engine", "analyze",
         "Track kill-chain coverage", pivot_engine.track_kill_chain)

# 13. evasion_framework
register("evasion.fingerprint", "evasion_framework", "generate",
         "Spoofed fingerprint", evasion_framework.generate_spoofed_fingerprint)
register("evasion.disguise", "evasion_framework", "generate",
         "Disguise a request", evasion_framework.generate_disguised_request)
register("evasion.beacon", "evasion_framework", "generate",
         "Beacon schedule", evasion_framework.generate_beacon_schedule)

# 14. credential_parser
register("credentials.scan_keystrokes", "credential_parser", "analyze",
         "Scan keystroke logs", credential_parser.scan_keystroke_files)
register("credentials.scan_fingerprints", "credential_parser", "analyze",
         "Scan fingerprints", credential_parser.scan_fingerprints)
register("credentials.stats", "credential_parser", "analyze",
         "Credential stats", credential_parser.get_credential_stats)
register("credentials.pairs", "credential_parser", "analyze",
         "Username:password pairs", credential_parser.pair_credentials)

# 15. telegram_bot (module singleton)
register("notify.send", "telegram_bot", "notify",
         "Send a Telegram message", telegram_bot.send_message)
register("notify.config", "telegram_bot", "analyze",
         "Telegram config", telegram_bot.get_config)
