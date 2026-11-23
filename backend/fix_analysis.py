import sys

file_path = "app/services/analysis_service.py"

with open(file_path, "r") as f:
    lines = f.readlines()

# Update import (lines 11-13)
# Find the line with "from app.services.decompiler_engine import ("
for i, line in enumerate(lines):
    if line.strip().startswith("from app.services.decompiler_engine import"):
        # Replace the block lines i through i+2 (assuming three lines)
        # We'll replace lines[i:i+3] with new import lines
        new_import = [
            "from app.services.decompiler_engine import (\n",
            "    AnalysisResult,\n",
            "    DecompilerEngine,\n",
            "    create_decompiler_engine,\n",
            "    Function,\n",
            "    VTable,\n",
            "    SwitchStatement,\n",
            "    CallSite,\n",
            "    StringRef,\n",
            ")\n"
        ]
        # Determine how many lines to replace; find the line that is just "\n" after import block?
        # We'll just replace from i to the line that ends with ")" (maybe i+2)
        for j in range(i, len(lines)):
            if lines[j].strip() == ")":
                end_idx = j
                break
        else:
            end_idx = i + 2
        # Replace lines[i:end_idx+1] with new_import
        lines[i:end_idx+1] = new_import
        break

# Update get_analysis_result method body
# Find line with "        data = json.loads(analysis.result_data)"
for i, line in enumerate(lines):
    if line.rstrip() == "        data = json.loads(analysis.result_data)":
        start = i
        # Find the line "        result_obj = AnalysisResult()"
        # We'll replace these two lines and subsequent blank line with new block
        # Determine end: find line with "        result_obj = AnalysisResult()"
        for j in range(start, len(lines)):
            if lines[j].rstrip() == "        result_obj = AnalysisResult()":
                end = j
                break
        # Build new block
        new_block = [
            "        data = json.loads(analysis.result_data)\n",
            "        result_obj = AnalysisResult()\n",
            "\n",
            "        # Rebuild AnalysisResult from stored JSON\n",
            "        # Functions\n",
            "        for f_data in data.get(\"functions\", []):\n",
            "            result_obj.functions.append(\n",
            "                Function(\n",
            "                    name=f_data[\"name\"],\n",
            "                    address=f_data[\"address\"],\n",
            "                    signature=f_data[\"signature\"],\n",
            "                    body=\"\",\n",
            "                    calls=[],\n",
            "                    strings=[],\n",
            "                )\n",
            "            )\n",
            "\n",
            "        # VTables\n",
            "        for v_data in data.get(\"vtables\", []):\n",
            "            result_obj.vtables.append(\n",
            "                VTable(\n",
            "                    name=v_data[\"name\"],\n",
            "                    address=v_data[\"address\"],\n",
            "                    functions=[],\n",
            "                )\n",
            "            )\n",
            "\n",
            "        # Switch statements\n",
            "        for s_data in data.get(\"switches\", []):\n",
            "            switch = SwitchStatement(\n",
            "                address=s_data[\"address\"],\n",
            "                variable=s_data[\"variable\"],\n",
            "                cases=[],\n",
            "                default_target=s_data.get(\"default_target\") if s_data.get(\"has_default\") else None,\n",
            "                default_name=None,\n",
            "            )\n",
            "            result_obj.switches.append(switch)\n",
            "\n",
            "        # JMP calls\n",
            "        for c_data in data.get(\"jmp_calls\", []):\n",
            "            result_obj.jmp_calls.append(\n",
            "                CallSite(\n",
            "                    address=0,\n",
            "                    caller=c_data[\"caller\"],\n",
            "                    target=c_data[\"target\"],\n",
            "                    target_address=c_data[\"target_address\"],\n",
            "                    call_type=\"unknown\",\n",
            "                    confidence=c_data[\"confidence\"],\n",
            "                    raw_text=\"\",\n",
            "                )\n",
            "            )\n",
            "\n",
            "        # Strings\n",
            "        for s_data in data.get(\"strings\", []):\n",
            "            result_obj.strings.append(\n",
            "                StringRef(\n",
            "                    address=s_data[\"address\"],\n",
            "                    value=s_data[\"value\"],\n",
            "                    segment=s_data[\"segment\"],\n",
            "                    references=[],\n",
            "                )\n",
            "            )\n",
            "\n",
            "        # Cross-references (directly from JSON)\n",
            "        if \"cross_references\" in data:\n",
            "            result_obj.cross_references = data[\"cross_references\"]\n"
        ]
        # Replace lines[start:end+1] (including result_obj line) with new_block
        lines[start:end+1] = new_block
        break

# Write back
with open(file_path, "w") as f:
    f.writelines(lines)
