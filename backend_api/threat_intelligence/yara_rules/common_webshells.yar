rule Webshell_ASP_China_Chopper {
    meta:
        description = "Detects the China Chopper ASP webshell"
        author = "PhantomNet AI"
        date = "2025-12-11"
    strings:
        $text = /<%eval request\(\"[^\"]+\"\)%>/ 
    condition:
        $text
}

rule Webshell_PHP_Simple_Backdoor {
    meta:
        description = "Detects a simple PHP backdoor"
        author = "PhantomNet AI"
        date = "2025-12-11"
    strings:
        $php_command = /<\?php\s+passthru\(\s*\$_GET\[\s*['\"]cmd['\"]\s*\]\s*\);/
    condition:
        $php_command
}

