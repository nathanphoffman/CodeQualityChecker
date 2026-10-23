from codequality.detect import detect
from codequality.rules.rule_01_power_of_six.shared.find_functions import find_functions
from codequality.rules.rule_02_clear_names.shared.find_names import find_names
from codequality.rules.rule_05_be_secure.shared.uses import find_uses
from codequality.rules.rule_07_magic_values.tree_sitter.tree_literals import tree_literals
from codequality.rules.rule_08_few_dependencies.read_manifests import project_dependencies
from codequality.rules.rule_10_test_what_matters.count_tests import count_csharp_tests
from codequality.rules.rule_11_fail_loudly.tree_sitter.tree_handlers import tree_handlers
from codequality.rules.rule_12_clean_up.tree_sitter import analyze_tree
from codequality.rules.rule_14_space_out.tree_sitter.text_spacing import text_gaps
from codequality.source_code import non_test_files

CSHARP = """using System;
using Json = Newtonsoft.Json;

public class Server
{
    private const int MaxItems = 10;

    public int Handle(string path, int count = 2)
    {
        var total = count + 1;
        int unused = 5;
        string sql = "SELECT * FROM users WHERE id = " + path;
        try
        {
            File.ReadAllText(path);
        }
        catch (IOException e)
        {
            Console.WriteLine(e);
        }
        catch (Exception)
        {
        }
        return total;
        Console.WriteLine("dead");
    }

    private static int Helper(int a) => a * 2;

    public IEnumerable<int> Numbers()
    {
        yield return 1;
        yield return 2;
    }

    [Fact]
    public void TestHandle() { }
}
"""

def test_csharp_files_are_detected(tmp_path):
    (tmp_path / "App.csproj").write_text("<Project />")
    assert "csharp" in detect(tmp_path).languages

def test_methods_are_found_with_their_arguments_plus_lambdas_are_not_functions():
    found = {info.name: info.argument_count for info in find_functions(CSHARP, "csharp")}
    assert found == {"Handle": 2, "Helper": 1, "Numbers": 0, "TestHandle": 0}

def test_names_include_methods_parameters_plus_variables():
    assert {"Server", "Handle", "path", "count", "total", "e", "MaxItems"} <= set(find_names(CSHARP, "csharp"))

def test_calls_plus_string_building_are_seen_by_the_security_rules():
    names = [use.name for use in find_uses(CSHARP, "csharp")]
    assert {"File.ReadAllText", "Console.WriteLine", "dynamic_string"} <= set(names)

def test_const_fields_plus_enum_values_are_named_numbers():
    numbers = [literal for literal in tree_literals(CSHARP, "csharp") if literal.kind == "number"]
    assert {literal.value: literal.in_constant for literal in numbers}[10] is True
    assert [literal.value for literal in tree_literals("class A { decimal d = 2.5m; long l = 5UL; }", "csharp")] == [5, 2.5]

def test_tests_are_counted_by_attribute():
    assert count_csharp_tests(CSHARP) == 1
    assert count_csharp_tests("class A { [Theory] void T() {} [TestMethod] public void U() {} void V() {} }") == 2

def test_catch_clauses_are_judged_by_what_they_do_plus_what_they_catch():
    catches = sorted((handler.line_number, handler.is_loud, handler.is_broad) for handler in tree_handlers(CSHARP, "csharp") if handler.is_catch)
    assert catches == [(17, True, False), (21, False, True)]

def test_cleanup_finds_unused_alias_variables_dead_code_plus_private_methods():
    findings, usage = analyze_tree(CSHARP, "csharp")
    assert findings.unused_imports == [2]
    assert findings.unused_variables == [11, 12]  # unused and sql
    assert findings.unreachable == [25]  # a yield return after another is not dead code
    assert [name for name, _ in usage.private_definitions] == ["Helper"]

def test_attributes_stay_attached_to_their_method():
    gaps = text_gaps("class A\n{\n    void F() { }\n\n    [Fact]\n    public void G() { }\n}\n", "csharp")
    assert gaps.before_control_missing == []

def test_nuget_packages_are_dependencies_but_test_tools_are_not(tmp_path):
    (tmp_path / "App.csproj").write_text('<Project><ItemGroup><PackageReference Include="Serilog" Version="3" />'
                                         '<PackageReference Include="xunit" Version="2" /></ItemGroup></Project>')

    assert project_dependencies(detect(tmp_path)) == {("nuget", "Serilog")}

def test_test_files_are_left_out_of_non_test_rules(tmp_path):
    (tmp_path / "Server.cs").write_text("class A {}")
    (tmp_path / "ServerTests.cs").write_text("class B {}")
    assert [path.name for path in non_test_files(detect(tmp_path), (".cs",))] == ["Server.cs"]
