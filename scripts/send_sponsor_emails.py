#!/usr/bin/env python3
"""
send_sponsor_emails.py — Send the prepared sponsor pitch drafts.

This script reads prepared drafts from docs/sponsor-drafts/YYYY-MM-DD/ and sends them
via Gmail SMTP using the social email credentials.

Requirements:
- Save social email credentials in /home/ubuntu/.hermes/.service-credentials
- Run daily after the cron job prepares the drafts

Usage:
  python3 send_sponsor_emails.py              # sends today's drafts
  python3 send_sponsor_emails.py --dry-run     # just shows what would be sent
"""
import os
import sys
import json
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

DRAFTS_DIR = Path("/home/ubuntu/projects/uzi-network/docs/sponsor-drafts")

def load_credentials():
    """Load email credentials from .service-credentials."""
    creds_file = Path("/home/ubuntu/.hermes/.service-credentials")
    if not creds_file.exists():
        return None
    creds = {}
    for line in creds_file.read_text().split("\n"):
        if line.startswith("export "):
            k, v = line[7:].split("=", 1)
            creds[k] = v.strip('"').strip("'")
    return creds

def send_email(creds, to_email, subject, body):
    """Send email via Gmail SMTP."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = creds.get("SOCIAL_EMAIL")
    sender_password = creds.get("SOCIAL_EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        print("ERROR: Email credentials not found")
        return False

    msg = MIMEMultipart()
    msg["From"] = f"Uzi Network <{sender_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"ERROR sending to {to_email}: {e}")
        return False

def main():
    dry_run = "--dry-run" in sys.argv
    today = datetime.now().strftime("%Y-%m-%d")
    drafts_path = DRAFTS_DIR / today

    if not drafts_path.exists():
        print(f"No drafts for {today}. Run the cron job first.")
        return

    drafts = list(drafts_path.glob("*.md"))
    if not drafts:
        print(f"No drafts in {drafts_path}")
        return

    creds = load_credentials()
    if not creds and not dry_run:
        print("No credentials found. Run with --dry-run to preview.")
        return

    print(f"{'[DRY RUN] ' if dry_run else ''}Found {len(drafts)} drafts for {today}")
    print()

    sent = 0
    for draft_path in drafts:
        content = draft_path.read_text()
        # Parse: first line is "To: ...", second is "Subject: ...", then blank, then body
        lines = content.split("\n")
        to_email = ""
        subject = ""
        body_lines = []
        in_body = False
        for line in lines:
            if line.startswith("To: "):
                to_email = line[4:].strip()
            elif line.startswith("Subject: "):
                subject = line[9:].strip()
            elif line.strip() == "" and not in_body:
                in_body = True
            elif in_body:
                body_lines.append(line)

        body = "\n".join(body_lines)

        if not to_email or not subject:
            print(f"  ✗ {draft_path.name}: missing To or Subject")
            continue

        if dry_run:
            print(f"  Would send: {draft_path.name}")
            print(f"    To: {to_email}")
            print(f"    Subject: {subject}")
            print()
        else:
            print(f"  Sending: {draft_path.name} → {to_email}...", end=" ")
            if send_email(creds, to_email, subject, body):
                print("✓")
                sent += 1
            else:
                print("✗")

    if not dry_run:
        print(f"\nSent {sent}/{len(drafts)} emails")

if __name__ == "__main__":
    main()
