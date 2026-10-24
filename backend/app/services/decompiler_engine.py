
"""Decompiler output analysis engine for Ghidra-style pseudo-C decompilation.

This module provides deterministic pattern recognition for:
- VTable indirect call resolution (Ghidra Issue #516)
- Switch statement recovery from jump tables (Ghidra Issue #2628)
- JMP-with-PUSH call recovery (Ghidra Issue #5747)
- Cross-segment string recovery (Ghidra Issue #4865)
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Function:
    """Represents a decompiled function."""
    name: str
    address: int
    signature: str
    body: str
    calls: list['CallSite'] = field(default_factory=list)
    strings: list['StringRef'] = field(default_factory=list)


@dataclass
class CallSite:
    """Represents a call site in decompiled code."""
    address: int
    caller: str
    target: Optional[str] = None
    target_address: Optional[int] = None
    call_type: str = "direct"  # direct, vtable, switch, jmp_push, unknown
    confidence: float = 1.0
    raw_text: str = ""


@dataclass
class StringRef:
    """Represents a string reference in decompiled code."""
    address: int
    value: str
    segment: str = ""
    references: list[int] = field(default_factory=list)


@dataclass
class SwitchCase:
    """Represents a recovered switch case."""
    value: int
    target_address: int
    target_name: Optional[str] = None


@dataclass
class SwitchStatement:
    """Represents a recovered switch statement."""
    address: int
    variable: str
    cases: list[SwitchCase]
    default_target: Optional[int] = None
    default_name: Optional[str] = None


@dataclass
class VTable:
    """Represents a virtual table."""
    name: str
    address: int
    functions: list[tuple[int, str]] = field(default_factory=list)  # (offset, function_name)


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    functions: list[Function] = field(default_factory=list)
    vtables: list[VTable] = field(default_factory=list)
    switches: list[SwitchStatement] = field(default_factory=list)
    jmp_calls: list[CallSite] = field(default_factory=list)
    strings: list[StringRef] = field(default_factory=list)
    cross_references: dict[str, list[int]] = field(default_factory=dict)


class DecompilerEngine:
    """Core decompiler analysis engine with deterministic pattern recognition."""

    # Patterns for Ghidra-style pseudo-C output
    VTABLE_CALL_PATTERN = re.compile(
        r'\(\*([a-zA-Z_][a-zA-Z0-9_]*\s*->\s*vtable\s*\[\s*(\d+)\s*\])\s*\)\s*\('
    )
    VTABLE_DECL_PATTERN = re.compile(
        r'struct\s+(\w+)\s*\{[^}]*vtable\s*\[\s*\d+\s*\]\s*;[^}]*\}'
    )
    JMP_PUSH_PATTERN = re.compile(
        r'push\s+(0x[0-9a-fA-F]+|[a-zA-Z_][a-zA-Z0-9_]*)\s*;?\s*jmp\s+(0x[0-9a-fA-F]+|[a-zA-Z_][a-zA-Z0-9_]*)'
    )
    SWITCH_COMPARE_PATTERN = re.compile(
        r'if\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*==\s*(\d+)\s*\)\s*\{'
    )
    STRING_LITERAL_PATTERN = re.compile(r'"([^"\\]*(\\.[^"\\]*)*)"')
    FUNCTION_PATTERN = re.compile(
        r'(?:void|int|char|float|double|struct\s+\w+)\s+(\w+)\s*\([^)]*\)\s*\{'
    )

    def analyze(self, decompiler_output: str) -> AnalysisResult:
        """Analyze decompiler output and extract structured information."""
        result = AnalysisResult()
        
        # Parse functions
        result.functions = self._parse_functions(decompiler_output)
        
        # Detect vtables
        result.vtables = self._detect_vtables(decompiler_output)
        
        # Resolve vtable calls
        self._resolve_vtable_calls(result)
        
        # Detect JMP+PUSH patterns
        result.jmp_calls = self._detect_jmp_push_calls(decompiler_output)
        
        # Recover switch statements
        result.switches = self._recover_switches(decompiler_output)
        
        # Extract strings
        result.strings = self._extract_strings(decompiler_output)
        
        # Build cross-references
        self._build_cross_references(result)
        
        return result

    def _parse_functions(self, text: str) -> list[Function]:
        """Parse function definitions from decompiler output."""
        functions = []
        matches = list(self.FUNCTION_PATTERN.finditer(text))
        
        for i, match in enumerate(matches):
            name = match.group(1)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end]
            
            # Extract signature
            sig_match = re.search(rf'{re.escape(name)}\s*\([^)]*\)', text[match.start():end])
            signature = sig_match.group(0) if sig_match else f"{name}()"
            
            func = Function(
                name=name,
                address=0,  # Would be extracted from metadata in real implementation
                signature=signature,
                body=body,
            )
            functions.append(func)
        
        return functions

    def _detect_vtables(self, text: str) -> list[VTable]:
        """Detect vtable structures in decompiler output."""
        vtables = []
        # Look for vtable array initializations
        vtable_pattern = re.compile(
            r'(\w+_vtable|vtable_\w+)\s*\[\s*\d*\s*\]\s*=\s*\{([^}]+)\}'
        )
        
        for match in vtable_pattern.finditer(text):
            name = match.group(1)
            entries_text = match.group(2)
            
            vtable = VTable(name=name, address=0)
            
            # Parse function pointers in vtable
            func_ptr_pattern = re.compile(r'&([\w:]+)')
            for i, func_match in enumerate(func_ptr_pattern.finditer(entries_text)):
                func_name = func_match.group(1)
                vtable.functions.append((i * 8, func_name))  # 8 bytes per pointer on x64
            
            vtables.append(vtable)
        
        return vtables

    def _resolve_vtable_calls(self, result: AnalysisResult) -> None:
        """Resolve indirect vtable calls to concrete functions."""
        # Build vtable lookup
        vtable_map = {}
        for vtable in result.vtables:
            for offset, func_name in vtable.functions:
                vtable_map[(vtable.name, offset)] = func_name
        
        # Find and resolve vtable calls in function bodies
        for func in result.functions:
            vtable_calls = self.VTABLE_CALL_PATTERN.findall(func.body)
            for vtable_expr, index_str in vtable_calls:
                index = int(index_str)
                offset = index * 8  # x64 pointer size
                
                # Try to resolve
                target_name = None
                for (vname, voffset), fname in vtable_map.items():
                    if voffset == offset:
                        target_name = fname
                        break
                
                if target_name:
                    call = CallSite(
                        address=0,
                        caller=func.name,
                        target=target_name,
                        target_address=offset,
                        call_type="vtable",
                        confidence=0.9,
                        raw_text=f"(*{vtable_expr})("
                    )
                    func.calls.append(call)

    def _detect_jmp_push_calls(self, text: str) -> list[CallSite]:
        """Detect JMP-with-PUSH patterns that are actually calls."""
        calls = []
        
        # Look for push + jmp sequences
        lines = text.split('\n')
        for i, line in enumerate(lines):
            push_match = re.search(r'push\s+(0x[0-9a-fA-F]+|\w+)', line)
            if push_match:
                push_target = push_match.group(1)
                # Check next few lines for jmp
                for j in range(i + 1, min(i + 4, len(lines))):
                    jmp_match = re.search(r'jmp\s+(0x[0-9a-fA-F]+|\w+)', lines[j])
                    if jmp_match:
                        jmp_target = jmp_match.group(1)
                        call = CallSite(
                            address=0,
                            caller="unknown",
                            target=jmp_target if not jmp_target.startswith('0x') else None,
                            target_address=int(jmp_target, 16) if jmp_target.startswith('0x') else None,
                            call_type="jmp_push",
                            confidence=0.85,
                            raw_text=f"{line.strip()} ; {lines[j].strip()}"
                        )
                        calls.append(call)
                        break
        
        return calls

    def _recover_switches(self, text: str) -> list[SwitchStatement]:
        """Recover switch statements from comparison chains."""
        switches = []
        lines = text.split('\n')
        
        # Find sequences of if (var == value) patterns
        compare_chain = []
        current_var = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            is_indented = line.startswith(' ') or line.startswith('	')
            match = self.SWITCH_COMPARE_PATTERN.search(line)
            if match:
                var, value = match.groups()
                value = int(value)
                
                if current_var is None:
                    current_var = var
                    compare_chain = [(value, i)]
                elif var == current_var:
                    compare_chain.append((value, i))
                else:
                    # Different variable, check if previous chain was a switch
                    if len(compare_chain) >= 3:
                        switches.append(self._build_switch(current_var, compare_chain, lines))
                    current_var = var
                    compare_chain = [(value, i)]
            elif current_var and (not (line.startswith(' ') or line.startswith('	')) or stripped == ''):
                # Check if chain ended
                if len(compare_chain) >= 3:
                    switches.append(self._build_switch(current_var, compare_chain, lines))
                current_var = None
                compare_chain = []
        
        # Check final chain
        if current_var and len(compare_chain) >= 3:
            switches.append(self._build_switch(current_var, compare_chain, lines))
        
        return switches

    def _build_switch(self, var: str, cases: list[tuple[int, int]], lines: list[str]) -> SwitchStatement:
        """Build a switch statement from comparison chain."""
        switch_cases = []
        default_target = None
        
        for value, line_idx in cases:
            # Find the target address/label in the if body
            target_addr = 0
            target_name = None
            for j in range(line_idx + 1, min(line_idx + 5, len(lines))):
                # Look for goto, function call, or label
                goto_match = re.search(r'goto\s+(\w+)', lines[j])
                call_match = re.search(r'(\w+)\s*\(', lines[j])
                if goto_match:
                    target_name = goto_match.group(1)
                    break
                elif call_match and not call_match.group(1) in ('if', 'while', 'for', 'switch'):
                    target_name = call_match.group(1)
                    break
            
            switch_cases.append(SwitchCase(value=value, target_address=target_addr, target_name=target_name))
        
        return SwitchStatement(
            address=0,
            variable=var,
            cases=switch_cases,
            default_target=default_target,
        )

    def _extract_strings(self, text: str) -> list[StringRef]:
        """Extract string literals from decompiler output."""
        strings = []
        for match in self.STRING_LITERAL_PATTERN.finditer(text):
            value = match.group(1)
            if len(value) >= 4:  # Filter out very short strings
                strings.append(StringRef(
                    address=0,
                    value=value,
                    segment=".rodata",
                ))
        return strings

    def _build_cross_references(self, result: AnalysisResult) -> None:
        """Build cross-reference map from analysis results."""
        # Map function names to addresses
        func_address_map = {f.name: f.address for f in result.functions}
        
        # Cross-reference calls
        for func in result.functions:
            for call in func.calls:
                if call.target and call.target in func_address_map:
                    key = f"call_{call.target}"
                    if key not in result.cross_references:
                        result.cross_references[key] = []
                    result.cross_references[key].append(func.address)
        
        # Cross-reference JMP calls
        for call in result.jmp_calls:
            if call.target and call.target in func_address_map:
                key = f"call_{call.target}"
                if key not in result.cross_references:
                    result.cross_references[key] = []
                result.cross_references[key].append(call.target_address or 0)
        
        # Cross-reference strings
        for string_ref in result.strings:
            key = f"string_{string_ref.address}"
            result.cross_references[key] = []


def create_decompiler_engine() -> DecompilerEngine:
    """Factory function to create a DecompilerEngine instance."""
    return DecompilerEngine()
