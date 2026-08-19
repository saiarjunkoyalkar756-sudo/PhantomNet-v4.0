from unittest.mock import patch

from phantomnet_agent.ai_analyzer import analyze_attack
from phantomnet_agent.analyzers.command_injection_analyzer import CommandInjectionAnalyzer
from phantomnet_agent.analyzers.ml_analyzer import MLAnalyzer
from phantomnet_agent.analyzers.rule_based_analyzer import RuleBasedAnalyzer


def test_ml_analyzer_returns_structured_predictions_from_bundled_corpus():
    analyzer = MLAnalyzer()

    xss = analyzer.analyze("<script>alert('XSS')</script>")
    sql_injection = analyzer.analyze("SELECT * FROM users WHERE id = 1 OR 1=1")

    assert xss["prediction"] == "XSS"
    assert xss["confidence"] > 0
    assert sql_injection["prediction"] == "SQL Injection"
    assert sql_injection["confidence"] > 0


def test_rule_based_analyzer():
    analyzer = RuleBasedAnalyzer()
    assert analyzer.analyze("<script>alert('XSS')</script>") == "XSS"
    assert analyzer.analyze("1' or '1'='1") == "SQL Injection"
    assert analyzer.analyze("../../etc/passwd") == "Directory Traversal"
    assert analyzer.analyze("nmap -sS 127.0.0.1") == "Port Scan"
    assert analyzer.analyze("admin:admin") == "Brute Force"
    assert analyzer.analyze("some other payload") is None


def test_command_injection_analyzer():
    analyzer = CommandInjectionAnalyzer()
    assert analyzer.analyze("; ls -la") == "Command Injection"
    assert analyzer.analyze("| whoami") == "Command Injection"
    assert analyzer.analyze("&& cat /etc/passwd") == "Command Injection"
    assert analyzer.analyze("`uname -a`") == "Command Injection"
    assert analyzer.analyze("$(ifconfig)") == "Command Injection"
    assert analyzer.analyze("some other payload") is None


@patch("phantomnet_agent.analyzers.ml_analyzer.MLAnalyzer.analyze")
@patch("phantomnet_agent.analyzers.rule_based_analyzer.RuleBasedAnalyzer.analyze")
@patch("phantomnet_agent.analyzers.command_injection_analyzer.CommandInjectionAnalyzer.analyze")
def test_analyze_attack_uses_local_analyzer_precedence(
    mock_command_injection_analyze,
    mock_rule_based_analyze,
    mock_ml_analyze,
):
    mock_ml_analyze.return_value = {"prediction": "XSS"}
    mock_rule_based_analyze.return_value = None
    mock_command_injection_analyze.return_value = None
    assert analyze_attack("test payload") == "XSS"

    mock_ml_analyze.return_value = {"prediction": "unknown"}
    mock_rule_based_analyze.return_value = "SQL Injection"
    assert analyze_attack("test payload") == "SQL Injection"

    mock_rule_based_analyze.return_value = None
    mock_command_injection_analyze.return_value = "Command Injection"
    assert analyze_attack("test payload") == "Command Injection"

    mock_command_injection_analyze.return_value = None
    assert analyze_attack("test payload") == "Unknown"
