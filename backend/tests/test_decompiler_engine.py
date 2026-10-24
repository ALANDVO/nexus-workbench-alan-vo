"""Tests for the decompiler analysis engine."""

import pytest

from app.services.decompiler_engine import DecompilerEngine, create_decompiler_engine


class TestDecompilerEngine:
    @pytest.fixture
    def engine(self):
        return create_decompiler_engine()

    def test_analyze_empty_input(self, engine):
        result = engine.analyze("")
        assert result is not None
        assert len(result.functions) == 0

    def test_parse_functions(self, engine):
        text = """
        void func1() {
            int a = 1;
        }
        int func2(int x) {
            return x + 1;
        }
        """
        result = engine.analyze(text)
        assert len(result.functions) >= 2
        names = {f.name for f in result.functions}
        assert "func1" in names
        assert "func2" in names

    def test_detect_vtables(self, engine):
        text = """
        MyClass_vtable[] = {
            &MyClass::func1,
            &MyClass::func2,
            &MyClass::func3,
        };
        """
        result = engine.analyze(text)
        assert len(result.vtables) >= 1
        vtable = result.vtables[0]
        assert len(vtable.functions) == 3

    def test_resolve_vtable_calls(self, engine):
        text = """
        MyClass_vtable[] = {
            &MyClass::func1,
            &MyClass::func2,
        };

        void bar() {
            (*this->vtable[1])(local_20);
        }
        """
        result = engine.analyze(text)
        for func in result.functions:
            for call in func.calls:
                if call.call_type == "vtable":
                    assert call.target == "MyClass::func2"
                    return

    def test_detect_jmp_push_calls(self, engine):
        text = """
        void func1() {
            push 0x401000
            jmp 0x402000
        }
        """
        result = engine.analyze(text)
        assert len(result.jmp_calls) >= 1
        call = result.jmp_calls[0]
        assert call.call_type == "jmp_push"
        assert call.target_address == 0x402000

    def test_recover_switches(self, engine):
        text = """
        void func() {
            if (x == 1) {
                goto case1;
            }
            if (x == 2) {
                goto case2;
            }
            if (x == 3) {
                goto case3;
            }
        }
        """
        result = engine.analyze(text)
        assert len(result.switches) >= 1
        switch = result.switches[0]
        assert switch.variable == "x"
        assert len(switch.cases) >= 3

    def test_extract_strings(self, engine):
        text = """
        void func() {
            char *s = "Hello World";
            char *t = "Test String";
        }
        """
        result = engine.analyze(text)
        assert len(result.strings) >= 2
        values = {s.value for s in result.strings}
        assert "Hello World" in values
        assert "Test String" in values

    def test_build_cross_references(self, engine):
        text = """
        MyClass_vtable[] = {
            &MyClass::func1,
        };
        void bar() {
            (*this->vtable[0])(local_20);
        }
        """
        result = engine.analyze(text)
        assert len(result.cross_references) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
