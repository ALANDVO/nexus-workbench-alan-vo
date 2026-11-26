import sys

file_path = "tests/test_analysis_service.py"

with open(file_path, "r") as f:
    lines = f.readlines()

# Find the line with "if __name__ == \"__main__\":"
main_line = -1
for i, line in enumerate(lines):
    if line.strip() == 'if __name__ == "__main__":':
        main_line = i
        break

# Insert new test before that line
new_test = [
    "\\n",
    "    @pytest.mark.asyncio\\n",
    "    async def test_get_analysis_result(self, service: AnalysisService, db_session: AsyncSession, test_user: User):\\n",
    "        # Create an analysis with input that yields results\\n",
    "        analysis = Analysis(\\n",
    "            user_id=test_user.id,\\n",
    "            name=\"Test Get Result\",\\n",
    "            analysis_type=AnalysisType.VTABLE_RESOLUTION,\\n",
    "            input_data=\"\"\"\\n",
    "            MyClass_vtable[] = {\\n",
    "                &MyClass::func1,\\n",
    "                &MyClass::func2,\\n",
    "            };\\n",
    "            void bar() {\\n",
    "                (*this->vtable[1])(local_20);\\n",
    "            }\\n",
    "            \"\"\",\\n",
    "            status=AnalysisStatus.PENDING,\\n",
    "        )\\n",
    "        db_session.add(analysis)\\n",
    "        await db_session.commit()\\n",
    "        await db_session.refresh(analysis)\\n",
    "\\n",
    "        # Run analysis to generate result_data\\n",
    "        result = await service.run_analysis(db_session, analysis)\\n",
    "\\n",
    "        # Retrieve result via get_analysis_result\\n",
    "        retrieved = await service.get_analysis_result(db_session, analysis.id)\\n",
    "        assert retrieved is not None\\n",
    "        # Should have at least one function from the analysis\\n",
    "        assert len(retrieved.functions) >= 1\\n",
    "        # The function name should match\\n",
    "        func_names = {f.name for f in retrieved.functions}\\n",
    "        assert \"func1\" in func_names\\n",
    "        # VTables should be present\\n",
    "        assert len(retrieved.vtables) >= 1\\n",
    "        # VTable name\\n",
    "        vtable_names = {v.name for v in retrieved.vtables}\\n",
    "        assert \"MyClass_vtable\" in vtable_names\\n",
    "        # Cross references dict may be present\\n",
    "        assert isinstance(retrieved.cross_references, dict)\\n",
    "\\n",
]

# Insert new_test before main_line
lines[main_line:main_line] = new_test

# Write back
with open(file_path, "w") as f:
    f.writelines(lines)
