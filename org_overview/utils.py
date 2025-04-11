from pywebio.output import clear, put_buttons, put_markdown


def page_init(
    text,
    title,
    target=None,
):
    clear()
    if target is not None:
        put_buttons([text], onclick=[target])
    put_markdown(f"## {title}")
