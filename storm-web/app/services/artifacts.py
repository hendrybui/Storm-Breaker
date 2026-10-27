"""Artifacts service (P4.5) — reports, lures, payloads.

Extracted verbatim from ``app/blueprints/reports.py``,
``app/blueprints/lures.py`` and ``app/blueprints/payloads.py`` route
bodies.  Blueprints keep auth checks + request validation; generation
(frozen ``report_generator`` / ``lure_generator`` / ``payload_generator``
modules), persistence and operator-audit logging live here.

No behavior change intended — ``tests/char`` freezes response shapes.
"""
from __future__ import annotations

import json

import database as db


# -- Reports -----------------------------------------------------------------------

def create_report(config: dict, report_type: str, operator: str,
                  ip: str) -> dict:
    """Generate a report via the frozen module, persist + audit-log it."""
    from report_generator import generate_report  # lazy import preserved
    from app.core.integrity import sign_content
    result = generate_report(config)
    integrity = sign_content(result['html'])
    stats = dict(result['stats'])
    stats['integrity'] = integrity
    # Save to database
    report_id = db.save_report(
        name=config['title'],
        report_type=report_type,
        config=config,
        html_content=result['html'],
        stats=stats,
    )
    db.log_operator_action(operator, 'generate_report',
                           f'Generated report: {config["title"]}', ip)
    return {'id': report_id, 'stats': stats,
            'generated_at': result['generated_at'], 'integrity': integrity}


def list_reports() -> list:
    """All saved reports with stringified stats/config JSON decoded."""
    reports = db.get_reports()
    for r in reports:
        if isinstance(r.get('stats'), str):
            try:
                r['stats'] = json.loads(r['stats'])
            except Exception:
                pass
        if isinstance(r.get('config'), str):
            try:
                r['config'] = json.loads(r['config'])
            except Exception:
                pass
    return reports


def get_report(report_id: int):
    return db.get_report(report_id)


def delete_report(report_id: int) -> None:
    db.delete_report(report_id)


# -- Lures ---------------------------------------------------------------------------

def lure_categories() -> list:
    from lure_generator import get_categories
    return get_categories()


def lure_preview(category, template_index) -> dict:
    from lure_generator import preview_template
    return preview_template(category, template_index)


def generate_lure(category, template_index, variables, lure_type,
                  log_note: str, operator: str, ip: str) -> dict:
    """Generate one lure; ``log_note`` is the exact legacy audit string."""
    from lure_generator import generate_lure
    result = generate_lure(
        category=category,
        template_index=template_index,
        variables=variables,
        lure_type=lure_type,
    )
    db.log_operator_action(operator, 'generate_lure', log_note, ip)
    return result


def render_lure_html(subject, body, variables) -> dict:
    from lure_generator import render_html_email
    return {'html': render_html_email(subject=subject, body=body,
                                      variables=variables)}


def generate_bulk_lures(category, template_index, targets, variables,
                        lure_type) -> dict:
    from lure_generator import generate_bulk_lures
    return generate_bulk_lures(
        category=category,
        template_index=template_index,
        targets=targets,
        variables=variables,
        lure_type=lure_type,
    )


def saved_lures() -> list:
    return db.get_saved_lures()


def save_lure(name, category, lure_type, subject, body, variables):
    return db.save_lure(
        name=name,
        category=category,
        lure_type=lure_type,
        subject=subject,
        body=body,
        variables=variables,
    )


def delete_saved_lure(lure_id) -> None:
    db.delete_saved_lure(lure_id)


# -- Payloads --------------------------------------------------------------------------

def payload_types():
    from payload_generator import PAYLOAD_TYPES
    return PAYLOAD_TYPES


def generate_payload(payload_type, config) -> dict:
    """Generate one payload via the frozen module.

    NOTE: the P3 bulk extract dropped the blueprint's ``generate_payload``
    import, making the serving route raise NameError -> 500.  Importing
    the frozen module here restores the G1-era behavior (see PROGRESS).
    """
    from payload_generator import generate_payload
    return generate_payload(payload_type, config)


__all__ = [
    "create_report", "list_reports", "get_report", "delete_report",
    "lure_categories", "lure_preview", "generate_lure", "render_lure_html",
    "generate_bulk_lures", "saved_lures", "save_lure", "delete_saved_lure",
    "payload_types", "generate_payload",
]

