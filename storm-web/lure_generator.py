"""
Storm-Breaker Lure Generator v2.0
Professional phishing email/SMS lure templates with variable substitution
Supports: email templates, SMS pretexts, HTML email rendering, bulk generation,
          campaign tracking URLs, 9 categories with 25+ templates
"""

import random
import string
import json
import re
import html
from datetime import datetime, timedelta


LURE_CATEGORIES = {
    'it_support': {
        'name': 'IT Support',
        'icon': '🖥️',
        'description': 'IT helpdesk and system administration pretexts',
        'templates': [
            {
                'name': 'Password Expiry',
                'subject': 'Action Required: Your password expires in {{hours}} hours',
                'body': '''Dear {{name}},

Your corporate password is set to expire in {{hours}} hours. To avoid account lockout, please update your password immediately using the secure link below.

🔐 Update Password: {{link}}

If you do not update your password before {{deadline}}, your account will be temporarily suspended and you will need to contact the helpdesk at ext. 4357.

For security purposes, this link expires in 24 hours and can only be used once.

Best regards,
IT Support Team
{{company}}
Help Desk: support@{{company_domain}}''',
                'sms': '⚠️ {{company}} IT: Your password expires in {{hours}}hrs. Update now to avoid lockout: {{link}}',
            },
            {
                'name': 'MFA Setup Required',
                'subject': 'Security Alert: Multi-Factor Authentication Enrollment Required',
                'body': '''Dear {{name}},

As part of our enhanced security initiative, all employees are required to set up Multi-Factor Authentication (MFA) by {{deadline}}.

This is a mandatory compliance requirement per our updated security policy (SEC-2024-003).

Please complete your MFA enrollment using the link below:

🔒 Set Up MFA: {{link}}

Supported authentication methods:
• Microsoft Authenticator
• Google Authenticator
• Hardware security key (YubiKey)
• SMS verification (backup only)

Failure to enroll by the deadline will result in restricted account access until enrollment is complete.

Thank you for helping us keep {{company}} secure.

IT Security Team
{{company}}''',
                'sms': '🔒 {{company}}: MFA enrollment required by {{deadline}}. Enroll now: {{link}}',
            },
            {
                'name': 'System Maintenance',
                'subject': '🔧 Scheduled System Maintenance - Account Verification Required',
                'body': '''Dear {{name}},

We will be performing critical system maintenance on {{deadline}} as part of our infrastructure upgrade (Ticket: INC{{ref_number}}).

To ensure continuity of your services, please verify your account credentials before the maintenance window begins.

✅ Verify Account: {{link}}

During the maintenance window ({{deadline}} — approx. 6 hours), the following services will be affected:
• Email access (Outlook/Exchange)
• VPN connectivity
• SharePoint and internal applications
• Wi-Fi authentication

Please save any work in progress before the maintenance window.

We appreciate your cooperation.

IT Infrastructure Team
{{company}}''',
                'sms': '🔧 {{company}} maintenance {{deadline}}. Verify account to avoid disruption: {{link}}',
            },
            {
                'name': 'Suspicious Login Alert',
                'subject': '🔴 Security Alert: Unusual sign-in activity detected',
                'body': '''Dear {{name}},

We detected an unusual sign-in attempt on your {{company}} account:

📍 Location: {{location}}
🖥️ Device: {{device}}
⏰ Time: {{deadline}}
🌐 IP Address: {{source_ip}}

If this was you, please verify your identity to dismiss this alert.
If this was NOT you, secure your account immediately.

🔒 Review Activity: {{link}}

Do not ignore this alert. Unauthorized access attempts may indicate your credentials have been compromised.

Security Operations Center
{{company}}
Incident Reference: SEC-{{ref_number}}''',
                'sms': '🔴 {{company}} Security: Unusual login from {{location}} at {{deadline}}. Review: {{link}}',
            },
        ],
    },
    'hr_department': {
        'name': 'HR Department',
        'icon': '👔',
        'description': 'Human resources and employee management pretexts',
        'templates': [
            {
                'name': 'Benefits Enrollment',
                'subject': 'Open Enrollment Period - Review and Update Your Benefits',
                'body': '''Dear {{name}},

The annual benefits open enrollment period is now active. You have until {{deadline}} to review and update your benefit selections for the upcoming plan year.

📋 Review Benefits: {{link}}

Key changes this year:
• Updated health insurance plans with lower premiums
• New dental and vision coverage options
• Enhanced 401(k) matching (up to 6%)
• Flexible spending account contribution limits increased
• New mental health and wellness benefits

If no changes are made by {{deadline}}, your current selections will automatically roll over to the next plan year.

For questions, contact HR Benefits at benefits@{{company_domain}} or ext. 2200.

Human Resources Department
{{company}}''',
                'sms': '{{company}} HR: Benefits open enrollment ends {{deadline}}. Review options: {{link}}',
            },
            {
                'name': 'Compensation Review',
                'subject': 'Confidential: Your Annual Compensation Review',
                'body': '''Dear {{name}},

Your annual compensation review has been completed by your manager and approved by the compensation committee.

Please log in to the HR portal to view your updated compensation details, including any salary adjustments, bonus allocations, and equity grants effective next pay period.

💰 View Compensation Details: {{link}}

This information is strictly confidential and should not be shared with colleagues. Please review within 5 business days and acknowledge receipt.

If you have questions about your review, please schedule time with your HR Business Partner.

Compensation & Benefits Team
{{company}}''',
                'sms': '{{company}} HR: Your compensation review is ready. View confidential details: {{link}}',
            },
            {
                'name': 'Policy Acknowledgment',
                'subject': 'Required: Updated Company Policy Acknowledgment — Due {{deadline}}',
                'body': '''Dear {{name}},

Our company policies have been updated for the new fiscal year. All employees must review and digitally acknowledge the updated policies by {{deadline}}.

📄 Review & Acknowledge: {{link}}

Key policy updates include:
• Remote/hybrid work policy changes (Section 4.2)
• Updated data handling and classification procedures
• Revised travel and expense guidelines
• New social media and AI usage policy
• Updated code of conduct provisions

Non-acknowledgment by the deadline will be flagged to your manager and may affect your compliance standing.

Human Resources
{{company}}''',
                'sms': '{{company}}: Updated policies require acknowledgment by {{deadline}}. Review now: {{link}}',
            },
            {
                'name': 'Training Completion',
                'subject': 'Mandatory Training: Annual Security Awareness — Due {{deadline}}',
                'body': '''Dear {{name}},

Your annual security awareness training is past due. Per company policy and regulatory requirements, all employees must complete this training by {{deadline}}.

🎓 Complete Training: {{link}}

Training Duration: Approximately 25 minutes
Topics Covered:
• Phishing and social engineering awareness
• Data protection and privacy (GDPR/CCPA)
• Password security best practices
• Incident reporting procedures
• Physical security protocols

Employees who have not completed training by the deadline will have their system access temporarily restricted.

Learning & Development Team
{{company}}''',
                'sms': '{{company}}: Security training overdue. Complete by {{deadline}} to maintain access: {{link}}',
            },
        ],
    },
    'finance': {
        'name': 'Finance',
        'icon': '💰',
        'description': 'Financial and payroll-related pretexts',
        'templates': [
            {
                'name': 'Expense Report',
                'subject': 'Expense Report EXP-{{ref_number}} Requires Verification',
                'body': '''Dear {{name}},

Your recent expense report (Reference: EXP-{{ref_number}}) requires additional verification before processing. There appear to be items that need your confirmation.

📊 Review Expenses: {{link}}

Report Summary:
• Reference: EXP-{{ref_number}}
• Total Amount: ${{amount}}
• Items: {{item_count}} line items
• Status: Pending Verification
• Submitted: {{deadline}}

If you do not verify by end of business {{deadline}}, the reimbursement will be delayed to the next pay cycle (typically 2-3 additional weeks).

Finance Department
{{company}}''',
                'sms': '{{company}} Finance: Expense EXP-{{ref_number}} (${{amount}}) needs verification. Review: {{link}}',
            },
            {
                'name': 'Direct Deposit Update',
                'subject': 'Important: Verify Your Direct Deposit Information — Payroll System Upgrade',
                'body': '''Dear {{name}},

We are migrating to a new payroll processing system effective {{deadline}}. To ensure uninterrupted salary deposits, all employees must verify their direct deposit information.

🏦 Verify Banking Info: {{link}}

What you'll need:
• Bank name and routing number
• Account number
• Account type (checking/savings)

If your information is not verified by {{deadline}}, your next payment may be delayed or issued via paper check, which takes an additional 5-7 business days.

This is a one-time verification required for the system migration.

Payroll Department
{{company}}''',
                'sms': '{{company}} Payroll: Verify direct deposit before {{deadline}} to avoid payment delays: {{link}}',
            },
            {
                'name': 'Tax Document',
                'subject': 'Your {{tax_year}} W-2/Tax Documents Are Ready',
                'body': '''Dear {{name}},

Your {{tax_year}} tax documents (W-2, 1099) are now available for download through our secure employee portal.

📄 Download Tax Documents: {{link}}

Important deadlines:
• Documents available until: December 31, {{tax_year}}
• Tax filing deadline: April 15, {{next_year}}
• Amended return deadline: October 15, {{next_year}}

Please verify that the information on your documents is accurate. If you notice any discrepancies, contact Payroll within 30 days.

For security, you will need to verify your identity before accessing the documents.

Payroll & Tax Department
{{company}}''',
                'sms': '{{company}}: Your {{tax_year}} tax documents (W-2) are ready. Download securely: {{link}}',
            },
        ],
    },
    'delivery': {
        'name': 'Delivery & Shipping',
        'icon': '📦',
        'description': 'Package delivery and shipping notification pretexts',
        'templates': [
            {
                'name': 'Package Delivery',
                'subject': 'Your package is waiting for delivery confirmation',
                'body': '''Hello {{name}},

We attempted to deliver your package but were unable to complete delivery. Please confirm your delivery address to reschedule.

📦 Confirm Delivery: {{link}}

Package Details:
• Tracking Number: {{tracking}}
• Estimated Weight: {{weight}} lbs
• Delivery Attempt: {{deadline}}
• Status: Address Confirmation Required
• Carrier: Express Logistics

If not confirmed within 48 hours, the package will be returned to sender and a redelivery fee of ${{amount}} may apply.

Delivery Services Team
Express Logistics''',
                'sms': '📦 Delivery attempted for package {{tracking}}. Confirm address to reschedule: {{link}}',
            },
            {
                'name': 'Customs Hold',
                'subject': 'Package Held at Customs — Action Required ({{tracking}})',
                'body': '''Dear {{name}},

Your international shipment (Tracking: {{tracking}}) is being held at customs and requires additional documentation for clearance.

🛃 Submit Documentation: {{link}}

Shipment Details:
• Tracking: {{tracking}}
• Origin: International
• Status: Customs Hold
• Required: Identity verification and customs declaration

A customs processing fee of ${{amount}} may apply. Packages not cleared within 5 business days will be returned to the origin country.

Failure to respond may result in package seizure per customs regulations.

International Shipping & Customs Clearance Department''',
                'sms': '🛃 Package {{tracking}} held at customs. Submit docs to release: {{link}}',
            },
        ],
    },
    'cloud_services': {
        'name': 'Cloud Services',
        'icon': '☁️',
        'description': 'Cloud storage and SaaS service pretexts',
        'templates': [
            {
                'name': 'Storage Full',
                'subject': '⚠️ Your cloud storage is almost full (95% used)',
                'body': '''Dear {{name}},

Your {{company}} cloud storage account has reached 95% capacity. To prevent data loss and ensure continued access to your files and shared documents, please take action.

☁️ Manage Storage: {{link}}

Current Usage:
• Used: 14.3 GB / 15 GB (95.3%)
• Files: 2,847 items
• Shared folders: 23

Options:
1. Delete unnecessary files to free space
2. Upgrade to Business Premium (unlimited storage)
3. Archive older files to cold storage

Files synced to your device may stop updating when storage is full. Auto-save will be disabled for shared documents.

Cloud Services Team
{{company}}''',
                'sms': '⚠️ {{company}} cloud storage at 95%. Manage now to prevent data loss: {{link}}',
            },
            {
                'name': 'Account Suspension Warning',
                'subject': '🔴 Account suspension notice — Action required within 24 hours',
                'body': '''Dear {{name}},

Your {{company}} account has been flagged for suspension due to a potential Terms of Service violation detected by our automated security systems.

Reason: Unusual activity pattern detected
Account: {{email}}
Detection Time: {{deadline}}
Action Required By: 24 hours from this notice

If no action is taken, your account and all associated data will be temporarily suspended.

🔒 Verify Account: {{link}}

If you believe this is an error, please verify your identity to dismiss the flag. Your data and access will remain intact after successful verification.

Trust & Safety Team
{{company}}''',
                'sms': '🔴 {{company}}: Account suspension warning. Verify within 24hrs: {{link}}',
            },
            {
                'name': 'Shared Document',
                'subject': '{{sender_name}} shared a document with you: "{{document_name}}"',
                'body': '''Hi {{name}},

{{sender_name}} ({{sender_email}}) has shared a document with you.

📄 Document: "{{document_name}}"
📁 Folder: {{folder_name}}
👤 Shared by: {{sender_name}}
🕐 Shared: {{deadline}}
🔑 Access: View & Edit

Open Document: {{link}}

This shared link expires in 7 days. You may need to sign in to access the document.

— {{company}} Document Sharing''',
                'sms': '📄 {{sender_name}} shared "{{document_name}}" with you. Open: {{link}}',
            },
        ],
    },
    'social_media': {
        'name': 'Social Media',
        'icon': '📱',
        'description': 'Social media platform notification pretexts',
        'templates': [
            {
                'name': 'Account Verification',
                'subject': '⚠️ Verify your account to avoid suspension',
                'body': '''Dear {{name}},

We've noticed unusual activity on your account that may indicate unauthorized access. To protect your account and prevent suspension, please verify your identity.

✅ Verify Account: {{link}}

Recent suspicious activity detected:
• Login from unrecognized device ({{device}})
• Location: {{location}}
• Multiple failed authentication attempts
• Profile changes from unknown IP

If you don't verify within 24 hours, your account may be temporarily restricted to protect your data and followers.

Trust & Safety Team''',
                'sms': '⚠️ Unusual activity detected. Verify to avoid account suspension: {{link}}',
            },
            {
                'name': 'New Login Alert',
                'subject': 'New login to your account from {{location}}',
                'body': '''Hi {{name}},

We noticed a new login to your account:

📍 Location: {{location}}
🖥️ Device: {{device}}
⏰ Time: {{deadline}}
🌐 IP: {{source_ip}}

Was this you?

✅ Yes, this was me: {{link}}
❌ No, secure my account: {{link}}

If you didn't log in, someone may have access to your account. We recommend changing your password immediately.

Security Team''',
                'sms': 'New login from {{location}} on {{device}}. Wasn\'t you? Secure account: {{link}}',
            },
        ],
    },
    'banking': {
        'name': 'Banking & Financial',
        'icon': '🏦',
        'description': 'Banking, payment, and financial service pretexts',
        'templates': [
            {
                'name': 'Unusual Transaction',
                'subject': '🔴 Unusual transaction detected on your account',
                'body': '''Dear {{name}},

We detected an unusual transaction on your account that requires your immediate attention:

Transaction Details:
• Amount: ${{amount}}
• Merchant: {{merchant_name}}
• Location: {{location}}
• Date: {{deadline}}
• Card ending: ****{{card_last4}}

If you authorized this transaction, no action is needed.
If you did NOT authorize this transaction, please report it immediately:

🔒 Review Transaction: {{link}}

For your security, we may temporarily limit your account until verification is complete.

Fraud Prevention Team
{{company}} Banking''',
                'sms': '🔴 {{company}} Bank: ${{amount}} charge at {{merchant_name}}. Not you? Report: {{link}}',
            },
            {
                'name': 'Account Security Update',
                'subject': 'Important: Enhanced security verification required for your account',
                'body': '''Dear {{name}},

As part of our ongoing commitment to protecting your financial information, we are implementing enhanced security measures across all accounts.

To maintain uninterrupted access to your account and online banking services, please complete the security verification process by {{deadline}}.

🔐 Complete Verification: {{link}}

What you'll need:
• Your account credentials
• Government-issued ID (for identity confirmation)
• Phone number on file (for verification code)

This is a one-time requirement as part of our annual security compliance update.

Accounts that are not verified may experience temporary access restrictions.

Account Security Team
{{company}} Banking
Member FDIC | Equal Housing Lender''',
                'sms': '{{company}} Bank: Security verification required by {{deadline}}. Complete now: {{link}}',
            },
        ],
    },
    'government': {
        'name': 'Government & Tax',
        'icon': '🏛️',
        'description': 'Government agency and tax authority pretexts',
        'templates': [
            {
                'name': 'Tax Refund',
                'subject': 'Tax Refund Notification — Ref: TAX-{{ref_number}}',
                'body': '''Dear {{name}},

After reviewing your tax return for the fiscal year {{tax_year}}, we have determined that you are eligible for a tax refund.

Refund Details:
• Reference Number: TAX-{{ref_number}}
• Refund Amount: ${{amount}}
• Processing Status: Pending Verification
• Estimated Deposit: 5-10 business days after verification

To process your refund, please verify your identity and banking information:

💰 Claim Refund: {{link}}

This refund will expire if not claimed within 30 days of this notification.

Please note: We will never ask for your full Social Security Number via email. Only the last 4 digits are required for verification.

Tax Services Division
Ref: TAX-{{ref_number}}''',
                'sms': '💰 Tax refund of ${{amount}} available. Verify to claim (Ref: TAX-{{ref_number}}): {{link}}',
            },
            {
                'name': 'Compliance Notice',
                'subject': 'Compliance Notice: Required Information Update — Due {{deadline}}',
                'body': '''Dear {{name}},

This notice is to inform you that your records require updating to maintain compliance with current regulations.

Reference: COMP-{{ref_number}}
Due Date: {{deadline}}
Status: Action Required

Failure to update your information by the deadline may result in:
• Account holds or restrictions
• Processing delays for pending applications
• Compliance penalties

📋 Update Information: {{link}}

This is an automated notice. Please do not reply directly to this message. For assistance, contact our support line.

Compliance & Records Division''',
                'sms': 'Compliance notice: Update required by {{deadline}}. Reference COMP-{{ref_number}}: {{link}}',
            },
        ],
    },
    'healthcare': {
        'name': 'Healthcare',
        'icon': '🏥',
        'description': 'Healthcare and medical service pretexts',
        'templates': [
            {
                'name': 'Appointment Confirmation',
                'subject': 'Appointment Confirmation — Please verify your information',
                'body': '''Dear {{name}},

You have an upcoming appointment that requires pre-visit verification:

Appointment Details:
• Provider: {{company}} Medical Center
• Date: {{deadline}}
• Type: Annual Check-up / Follow-up
• Reference: APT-{{ref_number}}

Before your visit, please verify your insurance information and update any changes to your medical history through our patient portal:

📋 Verify Information: {{link}}

Please complete this step at least 24 hours before your appointment to avoid delays at check-in.

If you need to reschedule, please do so at least 48 hours in advance to avoid a cancellation fee.

Patient Services
{{company}} Medical Center''',
                'sms': '🏥 {{company}} Medical: Appointment {{deadline}}. Verify info: {{link}}',
            },
            {
                'name': 'Test Results',
                'subject': 'Your lab results are ready for review',
                'body': '''Dear {{name}},

Your recent laboratory test results are now available through our secure patient portal.

📊 View Results: {{link}}

Result Details:
• Order Reference: LAB-{{ref_number}}
• Ordered by: Dr. {{doctor_name}}
• Collection Date: {{deadline}}
• Status: Results Available

For your privacy and security, you will need to verify your identity before accessing your results.

If you have questions about your results, please schedule a follow-up appointment with your provider.

Laboratory Services
{{company}} Medical Center

HIPAA Notice: This message contains protected health information intended only for the named recipient.''',
                'sms': '📊 {{company}} Medical: Lab results ready. View securely: {{link}}',
            },
        ],
    },
}


def get_categories():
    """Return all available lure categories and their templates"""
    result = {}
    for key, cat in LURE_CATEGORIES.items():
        result[key] = {
            'name': cat['name'],
            'icon': cat['icon'],
            'description': cat.get('description', ''),
            'template_count': len(cat['templates']),
            'templates': [{'name': t['name'], 'has_sms': 'sms' in t} for t in cat['templates']],
        }
    return result


def generate_lure(category, template_index, variables=None, lure_type='email'):
    """Generate a lure from a template with variable substitution"""
    if category not in LURE_CATEGORIES:
        return {'error': f'Unknown category: {category}'}

    cat = LURE_CATEGORIES[category]
    if template_index < 0 or template_index >= len(cat['templates']):
        return {'error': f'Invalid template index: {template_index}'}

    template = cat['templates'][template_index]
    variables = variables or {}

    # Set defaults for common variables
    now = datetime.now()
    defaults = {
        'name': 'Valued User',
        'company': 'Acme Corporation',
        'company_domain': 'acmecorp.com',
        'hours': '24',
        'deadline': (now + timedelta(days=3)).strftime('%B %d, %Y'),
        'link': 'https://example.com/verify',
        'ref_number': ''.join(random.choices(string.digits, k=6)),
        'amount': f'{random.randint(50, 500)}.{random.randint(10, 99)}',
        'tracking': ''.join(random.choices(string.ascii_uppercase + string.digits, k=12)),
        'weight': f'{random.randint(1, 30)}.{random.randint(1, 9)}',
        'location': random.choice(['Moscow, Russia', 'Lagos, Nigeria', 'Shanghai, China',
                                    'Bucharest, Romania', 'São Paulo, Brazil', 'Unknown Location']),
        'device': random.choice(['iPhone 15 Pro (Safari)', 'Windows 11 PC (Chrome 120)',
                                  'MacBook Pro (Safari 17)', 'Android 14 (Chrome Mobile)',
                                  'Linux Desktop (Firefox 121)']),
        'source_ip': f'{random.randint(45,220)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,254)}',
        'email': 'user@example.com',
        'item_count': str(random.randint(3, 12)),
        'tax_year': str(now.year - 1),
        'next_year': str(now.year),
        'card_last4': ''.join(random.choices(string.digits, k=4)),
        'merchant_name': random.choice(['AMZN Digital', 'PayPl *Transfer', 'WIRE TRF International',
                                         'Apple.com/bill', 'COINBASE', 'Unknown Vendor']),
        'sender_name': random.choice(['John Mitchell', 'Sarah Chen', 'Michael Torres',
                                       'Emily Watson', 'David Kim']),
        'sender_email': 'colleague@company.com',
        'document_name': random.choice(['Q4 Financial Report.xlsx', 'Project Roadmap 2024.pptx',
                                         'Budget Proposal - DRAFT.docx', 'Meeting Notes - Confidential.pdf']),
        'folder_name': random.choice(['Shared Documents', 'Team Files', 'Project Alpha', 'Q4 Reports']),
        'doctor_name': random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Davis']),
    }

    # Merge defaults with user-provided variables
    merged = {**defaults, **variables}

    if lure_type == 'sms':
        if 'sms' not in template:
            return {'error': 'This template does not have an SMS variant'}
        content = template['sms']
    else:
        content = template['body']

    subject = template.get('subject', '')

    # Perform substitution
    for key, val in merged.items():
        content = content.replace(f'{{{{{key}}}}}', str(val))
        subject = subject.replace(f'{{{{{key}}}}}', str(val))

    # Character count for SMS
    char_count = len(content) if lure_type == 'sms' else None

    return {
        'category': cat['name'],
        'template': template['name'],
        'type': lure_type,
        'subject': subject,
        'body': content,
        'variables_used': {k: v for k, v in merged.items() if f'{{{{{k}}}}}' in template.get('body', '') + template.get('subject', '') + template.get('sms', '')},
        'char_count': char_count,
        'sms_segments': (char_count // 160 + 1) if char_count else None,
        'generated_at': datetime.now().isoformat(),
    }


def generate_bulk_lures(category, template_index, targets, variables=None, lure_type='email'):
    """Generate lures for multiple targets"""
    results = []
    base_vars = variables or {}

    for target in targets:
        target_vars = {**base_vars}
        if isinstance(target, dict):
            target_vars.update(target)
        else:
            target_vars['name'] = str(target)

        result = generate_lure(category, template_index, target_vars, lure_type)
        results.append(result)

    return {
        'lures': results,
        'total': len(results),
        'category': category,
        'template_index': template_index,
        'type': lure_type,
        'generated_at': datetime.now().isoformat(),
    }


def preview_template(category, template_index):
    """Get a raw template preview with variable placeholders visible"""
    if category not in LURE_CATEGORIES:
        return {'error': f'Unknown category: {category}'}

    cat = LURE_CATEGORIES[category]
    if template_index < 0 or template_index >= len(cat['templates']):
        return {'error': f'Invalid template index: {template_index}'}

    template = cat['templates'][template_index]
    all_vars = _extract_variables(
        template.get('body', '') + ' ' + template.get('subject', '') + ' ' + template.get('sms', '')
    )

    return {
        'category': cat['name'],
        'category_key': category,
        'name': template['name'],
        'subject': template.get('subject', ''),
        'body': template['body'],
        'sms': template.get('sms', ''),
        'available_variables': sorted(all_vars),
        'has_sms': 'sms' in template,
    }


def render_html_email(subject, body, variables=None):
    """Render a plain text lure as a professional HTML email"""
    variables = variables or {}
    company = variables.get('company', 'Acme Corporation')
    company_domain = variables.get('company_domain', 'acmecorp.com')
    link = variables.get('link', '#')

    body_html = html.escape(body).replace('\n\n', '</p><p style="margin:0 0 16px;">').replace('\n', '<br>')
    # Convert link placeholders to actual HTML links
    body_html = re.sub(
        r'(https?://[^\s<]+)',
        r'<a href="\1" style="color:#3b82f6;text-decoration:underline;">\1</a>',
        body_html
    )

    return f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:40px 20px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
    <tr><td style="background:#1e293b;padding:24px 32px;text-align:center;">
        <h1 style="color:#ffffff;font-size:18px;margin:0;font-weight:600;">{html.escape(company)}</h1>
    </td></tr>
    <tr><td style="padding:32px;">
        <h2 style="font-size:18px;color:#1e293b;margin:0 0 20px;">{html.escape(subject)}</h2>
        <div style="font-size:14px;color:#475569;line-height:1.7;">
            <p style="margin:0 0 16px;">{body_html}</p>
        </div>
    </td></tr>
    <tr><td style="padding:0 32px 32px;text-align:center;">
        <a href="{html.escape(link)}" style="display:inline-block;background:#3b82f6;color:#ffffff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:14px;">Take Action Now</a>
    </td></tr>
    <tr><td style="background:#f8fafc;padding:20px 32px;border-top:1px solid #e2e8f0;">
        <p style="font-size:11px;color:#94a3b8;margin:0;text-align:center;">
            © {datetime.now().year} {html.escape(company)}. All rights reserved.<br>
            This is an automated message. Please do not reply directly.<br>
            <a href="#" style="color:#94a3b8;">Unsubscribe</a> | <a href="#" style="color:#94a3b8;">Privacy Policy</a>
        </p>
    </td></tr>
</table>
</td></tr>
</table>
</body>
</html>'''


def _extract_variables(text):
    """Extract all {{variable}} placeholders from text"""
    return list(set(re.findall(r'\{\{(\w+)\}\}', text)))
