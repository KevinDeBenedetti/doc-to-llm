from src.services.vitepress import (
    add_vitepress_utilities,
    extract_sections,
    extract_vitepress_metadata,
)


def test_utilities_add_frontmatter_and_toc_when_missing():
    result = add_vitepress_utilities("# Title\n\nBody")

    assert result == (
        "---\noutline: deep\nlastUpdated: true\neditLink: true\n---\n\n"
        "# Title\n\n[[toc]]\n\n\nBody"
    )


def test_utilities_keep_existing_frontmatter_and_toc():
    content = "---\ntitle: x\n---\n# Title\n\n[[TOC]]\n\nBody"

    assert add_vitepress_utilities(content) == content


def test_extract_sections_lists_headings_of_every_level():
    content = "# One\ntext\n## Two\n###   Three  \n#\n"

    assert extract_sections(content) == ["One", "Two", "Three"]


def test_extract_metadata_reads_frontmatter_only():
    content = "---\ntitle: Guide: intro\nlastUpdated: true\n---\nkey: not metadata"

    assert extract_vitepress_metadata(content) == {
        "title": "Guide: intro",
        "lastUpdated": "true",
    }


def test_extract_metadata_without_frontmatter_is_empty():
    assert extract_vitepress_metadata("# Title\nkey: value") == {}
