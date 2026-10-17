"""
tests/test_credential_scanner.py — Test ArmorIQ Credential Scanner and TripLine Evidence Receipt.
"""

import json
from agent.credential_scanner import analyze_and_generate_receipt, scan_credentials, calculate_shannon_entropy
from receipts.verify import verify_receipt


def test_scan_credentials_aws():
    content = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nAWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    threats, entropy = scan_credentials(content)
    assert any("AWS_ACCESS_KEY_ID" in t for t in threats)
    assert any("AWS_SECRET_ACCESS_KEY" in t for t in threats)


def test_scan_credentials_private_key():
    content = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0examplekey\n-----END RSA PRIVATE KEY-----"
    threats, entropy = scan_credentials(content)
    assert any("RSA_PRIVATE_KEY" in t for t in threats)


def test_scan_credentials_db_uri():
    content = "DATABASE_URL=postgres://app_user:super_secret_p@ssw0rd@db.internal.net:5432/production"
    threats, entropy = scan_credentials(content)
    assert any("DATABASE_CREDENTIALS" in t for t in threats)


def test_clean_file_allowed():
    content = "# Project Documentation\nThis is a standard clean readme file without any secrets or credentials."
    res = analyze_and_generate_receipt("README.md", content)
    assert res["armoriq_decision"] == "ALLOW"
    assert res["blocked"] is False
    assert len(res["threats_detected"]) == 0


def test_credential_leak_blocked_and_signed_receipt():
    content = """
    # Production Deployment Config
    AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
    DATABASE_URL=postgresql://admin:prod_db_secret_key_99@prod-db.aws.com:5432/main
    TRIPLINE_CANARY_TOKEN=TRPL-phase3-l-cfe9784b
    """
    res = analyze_and_generate_receipt(".env.production", content)
    assert res["armoriq_decision"] == "DENY"
    assert res["tripline_decision"] == "BLOCKED_BEFORE_EXECUTION"
    assert res["blocked"] is True
    assert len(res["threats_detected"]) >= 2
    
    # Verify cryptographic signature
    receipt = res["receipt"]
    valid, reason = verify_receipt(receipt)
    assert valid is True
    assert reason == "VERIFIED"
    assert receipt["witness"]["execution_count"] == 0


def test_chatbot_answers_block_status():
    from agent.credential_scanner import answer_document_question

    content = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nSECRET=supersecret123"
    scan_res = analyze_and_generate_receipt(".env.secret", content)
    
    # Question 1: Is there a block?
    ans1 = answer_document_question("Is there a block on this document?", ".env.secret", scan_result=scan_res)
    assert ans1["is_blocked"] is True
    assert ans1["verdict"] == "DENY"
    assert "YES, THIS DOCUMENT IS BLOCKED" in ans1["response"]
    assert "ArmorIQ SDK" in ans1["response"]

    # Question 2: Why was it blocked?
    ans2 = answer_document_question("Why was this document blocked?", ".env.secret", scan_result=scan_res)
    assert "AWS_ACCESS_KEY_ID" in ans2["response"]
    assert "Shannon Entropy" in ans2["response"]

    # Question 3: Did the LLM read the document?
    ans3 = answer_document_question("Did the LLM or AI agent read this file?", ".env.secret", scan_result=scan_res)
    assert "zero tokens were exposed" in ans3["response"] or "0 tokens" in ans3["response"]

    # Clean file check
    clean_scan = analyze_and_generate_receipt("notes.txt", "Hello world, clean meeting notes.")
    ans_clean = answer_document_question("Is there a block?", "notes.txt", scan_result=clean_scan)
    assert ans_clean["is_blocked"] is False
    assert ans_clean["verdict"] == "ALLOW"
    assert "NO, THIS DOCUMENT IS NOT BLOCKED" in ans_clean["response"]

