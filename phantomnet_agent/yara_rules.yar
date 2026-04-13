/*
    This is a dummy YARA rule file for PhantomNet.
    Add your own rules here.
*/

rule dummy_rule
{
    strings:
        $a = "dummy"
    condition:
        $a
}
