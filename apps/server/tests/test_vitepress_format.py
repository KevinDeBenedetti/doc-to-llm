from src.services.vitepress import format_vitepress_markdown


def test_horizontal_rule_keeps_following_content():
    content = "# Title\n\nIntro\n\n---\n\nSection after a horizontal rule\n\nMore text"

    assert format_vitepress_markdown(content) == content


def test_body_between_two_rules_is_not_treated_as_frontmatter():
    content = "# Title\n\n---\n\nMiddle\n\n---\n\nEnd"

    result = format_vitepress_markdown(content)

    assert result == content
    assert "lastUpdated" not in result


def test_leading_frontmatter_gets_missing_metadata():
    content = "---\ntitle: Guide\n---\n\n# Guide\n\n---\n\nBody"

    result = format_vitepress_markdown(content)

    assert result == (
        "---\ntitle: Guide\nlastUpdated: true\neditLink: true\n---\n\n# Guide\n\n---\n\nBody"
    )


def test_unterminated_frontmatter_is_returned_unchanged():
    content = "---\ntitle: Guide\n\n# Guide\n\nBody"

    assert format_vitepress_markdown(content) == content


def test_links_with_a_scheme_are_left_unchanged():
    line = "[a](mailto:me@x.org) [b](tel:+123) [c](https://x.org/page) [d](ftp://x.org)"

    assert format_vitepress_markdown(line) == line


def test_asset_links_are_left_unchanged():
    line = "[b](./img.png) [pdf](files/guide.pdf)"

    assert format_vitepress_markdown(line) == line


def test_page_link_gets_md_before_its_anchor():
    assert format_vitepress_markdown("[c](guide#setup)") == "[c](guide.md#setup)"


def test_page_link_without_extension_gets_md():
    assert format_vitepress_markdown("See [the guide](./guide).") == (
        "See [the guide](./guide.md)."
    )


def test_md_directory_and_anchor_links_are_left_unchanged():
    line = "[a](guide.md) [b](guide.md#x) [c](./dir/) [d](#local)"

    assert format_vitepress_markdown(line) == line


def test_inline_image_is_left_unchanged():
    line = "Text ![alt](img) and [page](other)"

    assert format_vitepress_markdown(line) == "Text ![alt](img) and [page](other.md)"


def test_container_without_title_gets_default_title():
    content = "::: tip\nBody\n:::\n::: warning Custom\n:::"

    assert format_vitepress_markdown(content) == (
        "::: tip Conseil\nBody\n:::\n::: warning Custom\n:::"
    )


def test_fenced_code_is_left_unchanged():
    content = "```md\n[x](y)\n::: tip\n```\n[x](y)"

    assert (
        format_vitepress_markdown(content) == "```md\n[x](y)\n::: tip\n```\n[x](y.md)"
    )


def test_frontmatter_key_inside_another_key_still_gets_default():
    content = "---\nxlastUpdated: 1\n---\nBody"

    assert "\nlastUpdated: true\n" in format_vitepress_markdown(content)
