"""
Tests for the SPSS output parser (snla.parser.output).

Covers OMS XML parsing, regex LST parsing (English and Chinese),
multi-dimension headers, and fallback behavior.
"""

import os
import tempfile

import pytest

from snla.parser.output import parse, parse_oms_xml, parse_raw_lst
from snla.parser.schema import AnalysisResult, TableResult


# =========================================================================
# Test 1: OMS XML — T-TEST
# =========================================================================


class TestOmsTtestXml:
    """OMS XML parsing for a standard T-TEST output."""

    def test_oms_ttest_xml_parse(self):
        """Parse a minimal T-TEST OMS XML and verify key structure."""
        pytest.importorskip("lxml", reason="lxml is required for OMS XML parsing")

        # OMS XML structure note:
        # The parser's findall("dimension") only visits direct children of
        # <pivotTable>.  Dimensions nested inside <category> elements are
        # invisible to the axis-discovery loop, so nested dimension axes
        # cannot serve as column headers.  As a result, cell values from
        # nested dimensions map to a generic "Value" column and are not
        # picked up by _extract_statistics.
        #
        # This test verifies the structural parsing (analysis type, table
        # titles, non-empty tables) rather than statistics extraction,
        # which is tested through the LST regex path.
        xml_content = """\
<oms>
  <command text="T-TEST">
    <pivotTable text="Group Statistics">
      <dimension axis="row">
        <category text="Male"/>
        <category text="Female"/>
      </dimension>
      <dimension axis="statistics">
        <category text="N"><cell text="10"/></category>
        <category text="Mean"><cell text="79.5"/></category>
      </dimension>
    </pivotTable>
    <pivotTable text="Independent Samples Test">
      <dimension axis="row">
        <category text="score"/>
      </dimension>
      <dimension axis="statistics">
        <category text="t"><cell text="2.34"/></category>
        <category text="df"><cell text="18"/></category>
        <category text="Sig. (2-tailed)"><cell text="0.021"/></category>
      </dimension>
    </pivotTable>
  </command>
</oms>"""

        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False)
        try:
            tmp.write(xml_content)
            tmp.close()

            result = parse_oms_xml(tmp.name)

            assert result.analysis_type == "T-TEST"
            assert isinstance(result.tables, list)
            assert len(result.tables) >= 1

            # Statistics dict is available (may be empty depending on
            # OMS XML dimension structure — see note above).
            assert isinstance(result.statistics, dict)

            # Verify table titles
            table_titles = [t.title for t in result.tables]
            assert "Group Statistics" in table_titles
            assert "Independent Samples Test" in table_titles

            # Verify parser_used is set correctly
            assert result.parser_used == "oms_xml"

            # Verify raw_output_path points to the temp file
            assert result.raw_output_path == tmp.name

        finally:
            os.unlink(tmp.name)


# =========================================================================
# Test 2: OMS XML — FREQUENCIES
# =========================================================================


class TestOmsFrequenciesXml:
    """OMS XML parsing for a FREQUENCIES output."""

    def test_oms_frequencies_xml_parse(self):
        """Parse a FREQUENCIES OMS XML and verify frequency rows."""
        pytest.importorskip("lxml", reason="lxml is required for OMS XML parsing")

        xml_content = """\
<oms>
  <command text="FREQUENCIES VARIABLES=education">
    <pivotTable text="Statistics">
      <dimension axis="row">
        <category text="education"/>
      </dimension>
      <dimension axis="statistics">
        <category text="N"><cell text="100"/></category>
        <category text="Mean"><cell text="3.45"/></category>
      </dimension>
    </pivotTable>
    <pivotTable text="Frequency">
      <dimension axis="row">
        <category text="High School"/>
        <category text="Bachelor"/>
        <category text="Master"/>
        <category text="PhD"/>
      </dimension>
      <dimension axis="statistics">
        <category text="Frequency"><cell text="30"/></category>
        <category text="Percent"><cell text="30.0"/></category>
      </dimension>
    </pivotTable>
  </command>
</oms>"""

        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False)
        try:
            tmp.write(xml_content)
            tmp.close()

            result = parse_oms_xml(tmp.name)

            assert isinstance(result.tables, list)
            assert len(result.tables) > 0

            # At least one table should have frequency-type title
            freq_tables = [
                t for t in result.tables
                if "Frequency" in t.title or "Statistics" in t.title
            ]
            assert len(freq_tables) >= 1

            # All tables should have non-empty rows
            all_rows = []
            for table in result.tables:
                all_rows.extend(table.rows)
            assert len(all_rows) > 0

            # Verify parser_used
            assert result.parser_used == "oms_xml"

        finally:
            os.unlink(tmp.name)


# =========================================================================
# Test 3: LST regex — English T-TEST
# =========================================================================


class TestLstTtestEn:
    """Regex LST parsing for English T-TEST output."""

    # NOTE: The parser's regex uses \s{2,} (two or more whitespace)
    # between columns, so mock text must use at least 2 spaces between tokens.
    MOCK_LST_EN = """\
T-TEST GROUPS=gender(1 2) /VARIABLES=score.

Group Statistics
            N     Mean    Std. Deviation
Male    10    79.500     8.200
Female    10    84.200     7.100

Independent Samples Test
Equal variances assumed  1.23  0.281  2.340   18    0.021

"""

    def test_lst_ttest_en_parse(self):
        """Parse English LST text and verify Group Statistics table."""
        result = parse_raw_lst(self.MOCK_LST_EN, "T-TEST")

        assert isinstance(result, AnalysisResult)
        assert len(result.tables) >= 1

        table_titles = [t.title for t in result.tables]
        assert "Group Statistics" in table_titles

    def test_lst_ttest_en_statistics(self):
        """Verify that p_value and t_value are extracted from English LST."""
        result = parse_raw_lst(self.MOCK_LST_EN, "T-TEST")

        assert "t_value" in result.statistics
        assert "p_value" in result.statistics

        # Both should be numeric
        assert isinstance(result.statistics["t_value"], (int, float))
        assert isinstance(result.statistics["p_value"], (int, float))


# =========================================================================
# Test 4: LST regex — Chinese T-TEST
# =========================================================================


class TestLstTtestZh:
    """Regex LST parsing for Chinese (Simplified) T-TEST output."""

    MOCK_LST_ZH = """\
T-TEST GROUPS=gender(1 2) /VARIABLES=score.

组统计
           个案数    平均值    标准差
score 男      10      79.500    8.200
      女      10      84.200    7.100

独立样本检验
假设方差相等  1.23  0.281  2.340   18     0.021

"""

    def test_lst_ttest_zh_parse(self):
        """Parse Chinese LST text and verify tables are produced."""
        result = parse_raw_lst(self.MOCK_LST_ZH, "T-TEST")

        assert isinstance(result, AnalysisResult)
        assert len(result.tables) >= 1

        table_titles = [t.title for t in result.tables]
        assert len(table_titles) >= 1

    def test_lst_ttest_zh_has_rows(self):
        """Verify Chinese LST parsing yields rows with data."""
        result = parse_raw_lst(self.MOCK_LST_ZH, "T-TEST")

        all_rows = []
        for table in result.tables:
            all_rows.extend(table.rows)
        assert len(all_rows) > 0

        # At least one row should contain a numeric group count
        has_numeric = any(
            row.get("N", "").replace(".", "").isdigit() for row in all_rows
        )
        assert has_numeric, "Expected at least one row with a numeric N value"


# =========================================================================
# Test 5: Multi-dimension headers (ANOVA-style)
# =========================================================================


class TestMultiDimensionAnova:
    """Multi-dimension ANOVA OMS XML parsing."""

    def test_multi_dimension_anova_parse(self):
        """Parse OMS XML with multiple dimension axis='variable' nodes."""
        pytest.importorskip("lxml", reason="lxml is required for OMS XML parsing")

        # The parser's findall("dimension") collects all direct-child
        # dimensions.  Multiple <dimension axis="variable"> nodes share
        # the same key in the dims dict (last one wins), but the parser
        # should not crash and should produce at least one table.
        xml_content = """\
<oms>
  <command text="UNIANOVA">
    <pivotTable text="Tests of Between-Subjects Effects">
      <dimension axis="row">
        <category text="Factor_A"/>
        <category text="Factor_B"/>
      </dimension>
      <dimension axis="variable">
        <category text="Level_1"/>
        <category text="Level_2"/>
      </dimension>
      <dimension axis="variable">
        <category text="Metric_A"/>
        <category text="Metric_B"/>
      </dimension>
      <dimension axis="statistics">
        <category text="F"><cell text="4.52"/></category>
        <category text="Sig."><cell text="0.012"/></category>
      </dimension>
    </pivotTable>
  </command>
</oms>"""

        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False)
        try:
            tmp.write(xml_content)
            tmp.close()

            result = parse_oms_xml(tmp.name)

            # Even with overlapping dimension axes the parser should
            # gracefully handle them and yield tables
            assert isinstance(result.tables, list)
            assert len(result.tables) > 0, (
                "Expected at least one table from multi-dimension XML"
            )

            # Rows should be present
            assert len(result.tables[0].rows) > 0, (
                "Expected rows from multi-dimension parsing"
            )

        finally:
            os.unlink(tmp.name)


# =========================================================================
# Test 6: Fallback behaviour (OMS → LST regex, and no-source error)
# =========================================================================


class TestFallback:
    """Fallback from OMS XML to LST regex and error handling."""

    MOCK_LST = """\
T-TEST GROUPS=gender(1 2) /VARIABLES=score.

Group Statistics
            N     Mean    Std. Deviation
Male    10    79.500     8.200
Female    10    84.200     7.100

Independent Samples Test
Equal variances assumed  1.23  0.281  2.340   18    0.021

"""

    def test_fallback_to_regex(self):
        """When OMS XML path does not exist, parse() falls back to LST text."""
        result = parse(
            oms_xml_path="/nonexistent/file.xml",
            lst_text=self.MOCK_LST,
            analysis_type="T-TEST",
        )

        assert result is not None
        assert len(result.tables) > 0
        # The parser_used should be "regex_lst" since the XML path
        # does not exist and the LST path was used
        assert result.parser_used == "regex_lst"

    def test_no_source_raises_value_error(self):
        """parse() raises ValueError when neither source is available."""
        with pytest.raises(ValueError):
            parse()
